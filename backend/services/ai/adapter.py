from core.config import settings
import logging
from typing import Dict, Any, Optional
import httpx
import time
from urllib.parse import urljoin, urlparse
from core.request_context import get_request_id

logger = logging.getLogger(__name__)


class AIAdapter:
    def __init__(self) -> None:
        self.provider = (settings.AI_PROVIDER or "openai").lower()
        self.model = settings.AI_MODEL

        if self.provider == "openai":
            self._init_openai()

        elif self.provider == "gemini":
            self._init_gemini()

        else:
            raise NotImplementedError(
                f"AI provider '{self.provider}' not supported"
            )

    # ---------------------------------------------------
    # OPENAI INIT
    # ---------------------------------------------------
    def _init_openai(self):
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY missing")

        self.api_key = settings.OPENAI_API_KEY
        self.base_url = (
            str(settings.OPENAI_API_BASE)
            if settings.OPENAI_API_BASE
            else "https://api.openai.com"
        )

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            event_hooks={
                "request": [self._on_request],
                "response": [self._on_response],
            },
        )

    # ---------------------------------------------------
    # GEMINI INIT
    # ---------------------------------------------------
    def _init_gemini(self):
        import google.generativeai as genai

        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY missing")

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.gemini = genai.GenerativeModel(self.model)

    # ---------------------------------------------------
    # SEND PROMPT
    # ---------------------------------------------------
    async def send_prompt(
        self, prompt: str, timeout: Optional[float] = 15.0
    ) -> Dict[str, Any]:

        if self.provider == "openai":
            return await self._openai_prompt(prompt, timeout)

        if self.provider == "gemini":
            return await self._gemini_prompt(prompt)

        raise NotImplementedError()

    # ---------------------------------------------------
    # OPENAI REQUEST
    # ---------------------------------------------------
    async def _openai_prompt(self, prompt, timeout):
        url = "/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        start = time.time()

        resp = await self.client.post(
            url, json=payload, headers=headers, timeout=timeout
        )
        resp.raise_for_status()

        data = resp.json()
        text = data["choices"][0]["message"]["content"]

        latency = int((time.time() - start) * 1000)

        logger.info(
            "ai_openai_success",
            extra={"latency_ms": latency, "provider": "openai"},
        )

        return {"reply": text, "tokens_used": None}

    # ---------------------------------------------------
    # GEMINI REQUEST
    # ---------------------------------------------------
    async def _gemini_prompt(self, prompt):
        response = self.gemini.generate_content(prompt)

        logger.info(
            "ai_gemini_success",
            extra={"provider": "gemini"},
        )

        return {"reply": response.text, "tokens_used": None}

    # ---------------------------------------------------
    async def close(self):
        if hasattr(self, "client"):
            await self.client.aclose()

    # ---------------------------------------------------
    async def _on_request(self, request: httpx.Request):
        rid = get_request_id()
        if rid:
            request.headers["X-Request-ID"] = rid
        request.extensions["start_time"] = time.time()

    async def _on_response(self, response: httpx.Response):
        start = response.request.extensions.get("start_time")
        latency = int((time.time() - start) * 1000) if start else None

        logger.info(
            "ai_http_response",
            extra={
                "status_code": response.status_code,
                "latency_ms": latency,
            },
        )


def _safe_url(full_url: str) -> str:
    try:
        p = urlparse(full_url)
        return f"{p.scheme}://{p.netloc}{p.path}"
    except Exception:
        return full_url