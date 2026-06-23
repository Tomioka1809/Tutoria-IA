import asyncio
from google import genai
from google.genai import types

async def main():
    client = genai.Client(api_key="AIzaSyDzcleJCeTwqmFPcHJqkxJEiXYa_yvyT4U")
    response = await client.aio.models.embed_content(
        model='gemini-embedding-001',
        contents="hola",
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    print(len(response.embeddings[0].values))
    print("Success 001")

    response = await client.aio.models.embed_content(
        model='text-embedding-004',
        contents="hola",
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    print("Success 004")
    
asyncio.run(main())
