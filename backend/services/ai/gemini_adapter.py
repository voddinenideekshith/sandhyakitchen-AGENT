import google.generativeai as genai
from core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel(settings.AI_MODEL)


async def generate_reply(message: str):
    response = model.generate_content(message)
    return response.text