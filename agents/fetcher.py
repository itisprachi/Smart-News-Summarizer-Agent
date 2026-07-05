"""
Fetcher Agent – Agent 1

Responsibility: calls NewsAPI and returns a list of raw article dicts.
"""

import logging
from typing import Any, Dict, List

from services import news_api, gnews_api

logger = logging.getLogger(__name__)


async def fetch(topic: str, max_articles: int = 5, language: str = "en") -> List[Dict[str, Any]]:
    """
    Fetch live articles for the given *topic* from NewsAPI.

    Returns
    -------
    list[dict]
        Each dict contains keys like ``title``, ``description``, ``content``,
        ``source``, ``url``, ``publishedAt``.
    """
    logger.info("[FetcherAgent] Fetching articles for topic='%s' (Primary: GNews)", topic)
    articles = []
    try:
        articles = await gnews_api.fetch_articles(topic, max_articles, language)
    except Exception as exc:
        logger.warning("[FetcherAgent] GNews API failed (%s), falling back to NewsAPI.", exc)
        
    if not articles:
        logger.info("[FetcherAgent] No articles from GNews, trying NewsAPI fallback.")
        try:
            articles = await news_api.fetch_articles(topic, max_articles, language)
        except Exception as exc:
            logger.error("[FetcherAgent] NewsAPI fallback failed: %s", exc)

    logger.info("[FetcherAgent] Retrieved %d articles", len(articles))
    return articles
