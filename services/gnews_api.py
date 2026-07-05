"""
GNews API service – handles HTTP communication with gnews.io.
"""

import logging
from typing import Any, Dict, List

import httpx

from config import GNEWS_API_KEY, GNEWS_BASE_URL

logger = logging.getLogger(__name__)


async def fetch_articles(
    topic: str,
    max_articles: int = 5,
    language: str = "en",
) -> List[Dict[str, Any]]:
    """
    Fetch articles from GNews for the given *topic*.

    Returns a list of raw article dicts (title, description, content, etc.).
    Raises ``httpx.HTTPStatusError`` on non-2xx responses.
    """
    if not GNEWS_API_KEY:
        raise ValueError(
            "GNEWS_API_KEY is not set. "
            "Add it to your .env file or export it as an environment variable."
        )

    params = {
        "q": topic,
        "max": max_articles,
        "lang": language,
        "apikey": GNEWS_API_KEY,
    }

    logger.info("Fetching up to %d articles for topic '%s' (lang=%s) from GNews", max_articles, topic, language)

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(GNEWS_BASE_URL, params=params)
        response.raise_for_status()

    data = response.json()
    articles = data.get("articles", [])

    # Filter out empty articles just in case
    valid = [
        a for a in articles
        if a.get("title")
    ]

    logger.info("Received %d valid articles from GNews", len(valid))
    return valid
