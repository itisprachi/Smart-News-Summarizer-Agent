"""
TTL cache service – avoids repeated LLM calls for the same query.

Uses ``cachetools.TTLCache`` with a configurable TTL (default 30 min).
"""

import logging

from cachetools import TTLCache

from config import CACHE_TTL_SECONDS, CACHE_MAX_SIZE

logger = logging.getLogger(__name__)

# In-memory TTL cache keyed by "<topic>|<max_articles>|<language>"
_cache: TTLCache = TTLCache(maxsize=CACHE_MAX_SIZE, ttl=CACHE_TTL_SECONDS)


def make_key(topic: str, max_articles: int, language: str) -> str:
    """Build a deterministic cache key."""
    return f"{topic.lower().strip()}|{max_articles}|{language}"


def get(key: str):
    """Return cached value or ``None``."""
    value = _cache.get(key)
    if value is not None:
        logger.info("Cache HIT for key '%s'", key)
    else:
        logger.info("Cache MISS for key '%s'", key)
    return value


def put(key: str, value):
    """Store a value in the cache."""
    _cache[key] = value
    logger.info("Cached result for key '%s' (TTL=%ds)", key, CACHE_TTL_SECONDS)
