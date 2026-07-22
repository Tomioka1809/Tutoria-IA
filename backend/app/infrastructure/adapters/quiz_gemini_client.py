import json
import urllib.request
import logging
from typing import Dict, Mapping
import anyio

logger = logging.getLogger(__name__)


def call_gemini_sync(api_key: str, payload: Mapping[str, object]) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "") or "{}"
            return "{}"
    except Exception as e:
        logger.error("Gemini API Error in quiz client: %s", e)
        return "{}"


async def call_gemini_api(api_key: str, payload: Dict[str, object]) -> str:
    return await anyio.to_thread.run_sync(call_gemini_sync, api_key, payload)
