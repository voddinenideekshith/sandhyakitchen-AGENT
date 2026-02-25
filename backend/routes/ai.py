from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import asyncio

from services.ai import generate_response, AIRequest, health_check

router = APIRouter()


async def stream_ai_response(message: str):
    """Async generator that yields SSE-formatted chunks from the AI reply.

    It calls the existing `generate_response` function to obtain the full reply
    and then yields it in smaller chunks as Server-Sent Events (SSE).
    """
    try:
        # reuse existing service logic to produce the response
        resp = await generate_response(AIRequest(message=message))
        text = resp.reply or ''

        # chunk size in characters
        chunk_size = 60
        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            # SSE format: data: <payload>\n\n
            yield f"data: {chunk}\n\n"
            # small delay to simulate streaming tokens
            await asyncio.sleep(0.05)

        # indicate stream end (optional in SSE clients)
        yield "data: [DONE]\n\n"
    except Exception:
        # signal error to client in SSE format
        yield "data: [ERROR]\n\n"


@router.post("/test")
async def ai_test(request: AIRequest):
    try:
        generator = stream_ai_response(request.message)
        return StreamingResponse(generator, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def ai_health():
    return await health_check()
