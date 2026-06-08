from google import genai

from app.config import get_settings

gemini_client = genai.Client(api_key=get_settings().gemini_api_key)
