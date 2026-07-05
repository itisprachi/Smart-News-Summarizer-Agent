"""
Ollama service – sends prompts to the local Ollama LLM and returns responses.
"""

import logging
import time

import httpx

from config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)


async def generate(prompt: str) -> str:
    """
    Send a *prompt* to the Ollama ``/api/generate`` endpoint and return the
    model's response text.
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    start = time.perf_counter()
    logger.debug("Sending prompt to Ollama (%s) …", OLLAMA_MODEL)

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

    elapsed = time.perf_counter() - start
    logger.info("Ollama responded in %.2f s", elapsed)

    data = response.json()
    return data.get("response", "").strip()
