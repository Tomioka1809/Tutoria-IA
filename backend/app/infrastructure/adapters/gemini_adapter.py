from typing import List, Dict
from google import genai
from google.genai import types
from app.application.ports.llm_port import LLMPort

class GeminiAdapter(LLMPort):
    def __init__(self, api_key: str):
        self.api_key = api_key
        # We use the async client to avoid blocking the event loop
        self.client = genai.Client(api_key=api_key)

    async def generate_response(
        self, 
        system_instruction: str, 
        history: List[Dict], 
        user_message: str,
        tools: List = None
    ) -> str:
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

        # Construct a map of tool functions to lookup by name
        tool_map = {func.__name__: func for func in tools} if tools else {}

        try:
            # We allow up to 5 manual tool execution steps to avoid infinite loops
            for _ in range(5):
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
                                import inspect
                                if inspect.iscoroutinefunction(func):
                                    result = await func(**call.args)
                                else:
                                    result = func(**call.args)
                            except Exception as ex:
                                print(f"Error executing tool {call.name}: {ex}")
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

            return response.text or "🦖 ¡Ups! Superé mi límite de razonamiento interno buscando tus datos."

        except Exception as e:
            print(f"Gemini API Exception: {e}")
            import traceback
            traceback.print_exc()
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
