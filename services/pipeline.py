import logging
from typing import List

from agents import fetcher, cleaner, summarizer, sentiment
from models.response import ArticleResult

logger = logging.getLogger(__name__)


async def run_pipeline(topic: str, max_articles: int, language: str) -> List[ArticleResult]:
    """
    Core business logic pipeline:
        Fetcher → Cleaner → Summarizer → Sentiment
    Returns a list of processed ArticleResult objects.
    """
    try:
        raw_articles = await fetcher.fetch(topic, max_articles, language)
    except Exception as exc:
        logger.error("Pipeline fetch error: %s", exc)
        raise

    if not raw_articles:
        return []

    results: List[ArticleResult] = []

    for idx, article in enumerate(raw_articles, start=1):
        title = article.get("title", "Untitled")
        source_name = article.get("source", {}).get("name", "Unknown")
        url = article.get("url", "")
        published = (article.get("publishedAt") or "")[:10]  # YYYY-MM-DD

        # Build the fullest text available
        raw_text = " ".join(
            filter(None, [
                article.get("title", ""),
                article.get("description", ""),
                article.get("content", ""),
            ])
        )

        # ── Agent 2: Clean ───────────────────────────────────────────────────
        cleaned_text = cleaner.clean(raw_text)

        if not cleaned_text:
            logger.warning("Article %d has no usable text; skipping", idx)
            continue

        # ── Agent 3: Summarize ───────────────────────────────────────────────
        try:
            summary_text = await summarizer.summarize(cleaned_text)
        except Exception as exc:
            logger.error("Summarizer error for article %d: %s", idx, exc)
            summary_text = "Summary generation failed."

        # ── Agent 4: Sentiment ───────────────────────────────────────────────
        try:
            sentiment_label = await sentiment.analyse(cleaned_text)
        except Exception as exc:
            logger.error("Sentiment error for article %d: %s", idx, exc)
            sentiment_label = "Neutral"

        results.append(
            ArticleResult(
                title=title,
                source=source_name,
                summary=summary_text,
                sentiment=sentiment_label,
                url=url,
                published_at=published,
            )
        )

        logger.info(
            "Processed article %d/%d: '%s' → %s",
            idx, len(raw_articles), title[:50], sentiment_label,
        )

    return results
