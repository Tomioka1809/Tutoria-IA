from typing import List, Dict
from google import genai
from google.genai import types
from app.application.ports.llm_port import LLMPort

class GeminiAdapter(LLMPort):
    def __init__(self, api_key: str):
        self.api_key = api_key
        # We use the async client to avoid blocking the event loop
        self.client = genai.Client(api_key=api_key)

    async def generate_response(self, system_instruction: str, history: List[Dict], user_message: str) -> str:
        if not self.api_key:
            return (
                "¡Hola! Soy TutorIA 🦖. Mi cerebro requiere que configures "
                "la variable `GEMINI_API_KEY`. Por ahora estoy en modo de simulación."
            )
            
        # Convert history format to genai SDK format
        contents = []
        for msg in history:
            contents.append(types.Content(
                role=msg["role"],
                parts=[types.Part.from_text(text=msg["parts"][0]["text"])]
            ))
            
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)]
        ))

        try:
            response = await self.client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction
                )
            )
            return response.text
        except Exception as e:
            print(f"Gemini API Exception: {e}")
            return "🦖 ¡Ups! Ocurrió un error al intentar conectarme con mi red de conocimiento."

    async def compute_embedding(self, text: str) -> List[float]:
        if not self.api_key:
            return [0.0] * 768  # Dummy embedding for testing if no key

        try:
            response = await self.client.aio.models.embed_content(
                model='gemini-embedding-001',
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=768
                )
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"Gemini Embedding Exception: {e}")
            return [0.0] * 768
