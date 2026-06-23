import asyncio
from google import genai

client = genai.Client(api_key="AIzaSyDzcleJCeTwqmFPcHJqkxJEiXYa_yvyT4U")
for model in client.models.list():
    if "embed" in model.name or "embedding" in model.name:
        print(model.name)
