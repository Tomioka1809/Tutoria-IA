from typing import List, Dict, Optional, Callable, Any
from google import genai
from google.genai import types
import logging
import asyncio
import inspect
from app.application.ports.llm_port import LLMPort

logger = logging.getLogger(__name__)


class GeminiAdapter(LLMPort):
    def __init__(
        self,
        api_key: str,
        allow_embedding_fallback: bool = True,
        allow_generation_fallback: bool = True,
        api_max_attempts: int = 3,
        before_generate_request: Optional[Callable[[], Any]] = None
    ):
        if type(api_max_attempts) is bool or not isinstance(api_max_attempts, int) or api_max_attempts < 1:
            raise ValueError("api_max_attempts debe ser un entero mayor o igual a 1")

        self.api_key = api_key
        self.allow_embedding_fallback = allow_embedding_fallback
        self.allow_generation_fallback = allow_generation_fallback
        self.api_max_attempts = api_max_attempts
        self.before_generate_request = before_generate_request
        # We use the async client to avoid blocking the event loop
        self.client = genai.Client(api_key=api_key) if api_key else None

    async def _trigger_before_generate(self):
        if self.before_generate_request:
            res = self.before_generate_request()
            if asyncio.iscoroutine(res) or inspect.iscoroutine(res):
                await res

    async def generate_response(
        self,
        system_instruction: str,
        history: List[Dict],
        user_message: str,
        tools: List = None
    ) -> str:
        if not self.api_key or not self.client:
            if not self.allow_generation_fallback:
                raise RuntimeError("GEMINI_API_KEY is missing in strict generation mode.")
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

        # Construct a map of tool functions to lookup by name
        tool_map = {func.__name__: func for func in tools} if tools else {}

        max_retries = self.api_max_attempts
        for attempt in range(max_retries):
            try:
                # We allow up to 5 manual tool execution steps to avoid infinite loops
                for _ in range(5):
                    await self._trigger_before_generate()

                    response = await self.client.aio.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            tools=tools if tools else None
                        )
                    )

                    if response.function_calls:
                        # Append the model's function call intent to the contents history
                        model_content = response.candidates[0].content
                        contents.append(model_content)

                        # Execute the function calls and gather responses
                        tool_parts = []
                        for call in response.function_calls:
                            func = tool_map.get(call.name)
                            if func:
                                try:
                                    if inspect.iscoroutinefunction(func):
                                        result = await func(**call.args)
                                    else:
                                        result = func(**call.args)
                                except Exception as ex:
                                    logger.error("Error executing tool %s: %s", getattr(call, "name", "tool"), ex)
                                    result = f"Error al ejecutar la herramienta: {str(ex)}"
                            else:
                                result = f"Error: Herramienta '{call.name}' no encontrada."

                            tool_parts.append(types.Part.from_function_response(
                                name=call.name,
                                response={"result": result}
                            ))

                        # Append the tool responses to the contents history
                        contents.append(types.Content(
                            role="tool",
                            parts=tool_parts
                        ))

                        # Continue generating content with tool context
                        continue
                    else:
                        return response.text or ""

                if not self.allow_generation_fallback and (not response or not response.text):
                    raise RuntimeError("Gemini limit reached without text response")
                return response.text or "🦖 ¡Ups! Superé mi límite de razonamiento interno buscando tus datos."

            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    logger.warning("429 Quota limit hit. Retrying in %ds... (attempt %d/%d)", wait_time, attempt + 1, max_retries)
                    await asyncio.sleep(wait_time)
                    continue

                if not self.allow_generation_fallback:
                    raise e

                logger.error("Gemini API Exception: %s", e)
                return "No cuento con información suficiente en la base oficial de la UNSAAC para responder con certeza."

    async def compute_embedding(self, text: str) -> List[float]:
        if not self.api_key or not self.client:
            if not self.allow_embedding_fallback:
                raise RuntimeError("GEMINI_API_KEY is missing in strict embedding mode.")
            return self._fallback_embedding(text)

        max_retries = self.api_max_attempts
        for attempt in range(max_retries):
            try:
                response = await self.client.aio.models.embed_content(
                    model='gemini-embedding-2',
                    contents=text,
                    config=types.EmbedContentConfig(
                        output_dimensionality=768
                    )
                )
                if response and hasattr(response, "embeddings") and response.embeddings:
                    vals = response.embeddings[0].values
                    if len(vals) == 768:
                        return [float(v) for v in vals]

                if not self.allow_embedding_fallback:
                    raise RuntimeError("Gemini embedding returned invalid structure or length")
                logger.error("Gemini embedding returned invalid structure or length")
                return self._fallback_embedding(text)
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    logger.warning("429 Quota limit hit for embedding. Retrying in %ds...", wait_time)
                    await asyncio.sleep(wait_time)
                    continue

                if not self.allow_embedding_fallback:
                    raise RuntimeError(f"Gemini Embedding failed in strict mode: {e}") from e

                logger.error("Gemini Embedding Exception: %s", e)
                return self._fallback_embedding(text)

    def _fallback_embedding(self, text: str) -> List[float]:
        import hashlib
        import math
        vec = [0.0] * 768
        if not text or not text.strip():
            vec[0] = 1.0
            return vec
        words = text.lower().split()
        for word in words:
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            idx = h % 768
            val = ((h >> 8) % 1000) / 1000.0
            vec[idx] += val
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0:
            vec[0] = 1.0
            return vec
        return [x / norm for x in vec]
