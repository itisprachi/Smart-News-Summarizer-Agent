"""
NewsAPI service – handles HTTP communication with newsapi.org.
"""

import logging
from typing import Any, Dict, List

import httpx

from config import NEWS_API_KEY, NEWS_API_BASE_URL

logger = logging.getLogger(__name__)


async def fetch_articles(
    topic: str,
    max_articles: int = 5,
    language: str = "en",
) -> List[Dict[str, Any]]:
    """
    Fetch articles from NewsAPI for the given *topic*.

    Returns a list of raw article dicts (title, description, content, etc.).
    Raises ``httpx.HTTPStatusError`` on non-2xx responses.
    """
    if not NEWS_API_KEY:
        raise ValueError(
            "NEWS_API_KEY is not set. "
            "Add it to your .env file or export it as an environment variable."
        )

    params = {
        "q": f'"{topic}"',
        "pageSize": max_articles,
        "language": language,
        "sortBy": "relevancy",
        "apiKey": NEWS_API_KEY,
    }

    logger.info("Fetching up to %d articles for topic '%s' (lang=%s)", max_articles, topic, language)

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(NEWS_API_BASE_URL, params=params)
        response.raise_for_status()

    data = response.json()
    articles = data.get("articles", [])

    # Filter out removed / empty articles
    valid = [
        a for a in articles
        if a.get("title") and a["title"] != "[Removed]"
    ]

    logger.info("Received %d valid articles from NewsAPI", len(valid))
    return valid
