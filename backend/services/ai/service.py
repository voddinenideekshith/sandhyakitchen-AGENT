import asyncio
import logging
from typing import Optional

from .adapter import AIAdapter
from .schemas import AIRequest, AIResponse
from .prompts import build_prompt

logger = logging.getLogger(__name__)

# lazy adapter instance to avoid init work during module import
_adapter: Optional[AIAdapter] = None


def _get_adapter() -> AIAdapter:
    global _adapter
    if _adapter is None:
        _adapter = AIAdapter()
    return _adapter


async def generate_response(request: AIRequest) -> AIResponse:
    """Construct prompt, call adapter, handle retries/timeouts, normalize response.

    Logs structured events for start, success, retries and failures.
    """
    prompt = build_prompt(request.message, request.context)
    adapter = _get_adapter()

    max_retries = 2
    base_backoff = 0.5

    logger.info("ai_request_start", extra={"service_module": __name__, "provider": adapter.provider, "model": adapter.model})

    for attempt in range(0, max_retries + 1):
        try:
            # adapter has its own timeout, but we wrap with asyncio.wait_for for safety
            raw = await asyncio.wait_for(adapter.send_prompt(prompt, timeout=10.0), timeout=12.0)
            reply = raw.get("reply", "")
            tokens = raw.get("tokens_used")
            logger.info("ai_response_success", extra={"provider": adapter.provider, "model": adapter.model, "tokens_used": tokens})
            return AIResponse(reply=reply, tokens_used=tokens)

        except asyncio.TimeoutError:
            logger.warning("ai_request_timeout", extra={"attempt": attempt, "provider": adapter.provider})
            if attempt == max_retries:
                logger.error("ai_request_failed_timeout", extra={"attempt": attempt, "provider": adapter.provider})
                raise
            await asyncio.sleep(base_backoff * (2 ** attempt))

        except Exception as e:
            # Log and retry for transient errors
            logger.warning("ai_provider_error_retry", extra={"attempt": attempt, "error": str(e)})
            if attempt == max_retries:
                logger.error("ai_provider_failure", extra={"attempt": attempt, "error": str(e)})
                raise
            await asyncio.sleep(base_backoff * (2 ** attempt))


async def shutdown() -> None:
    """Gracefully shutdown AI adapter resources."""
    global _adapter
    if _adapter is not None:
        try:
            await _adapter.close()
            logger.info("ai_service_shutdown", extra={"provider": _adapter.provider})
        except Exception:
            logger.exception("error shutting down ai adapter")
        _adapter = None


async def health_check() -> dict:
    """Return a small health dict for the AI provider.

    This tries to ensure adapter can be created; it does not send a prompt.
    """
    try:
        adapter = _get_adapter()
        return {"status": "ok", "ai_provider": adapter.provider}
    except Exception as e:
        logger.error("ai_health_error", extra={"error": str(e)})
        return {"status": "unavailable", "ai_provider": str(e)}
