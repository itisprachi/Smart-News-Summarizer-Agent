"""
Sentiment Agent – Agent 4

Responsibility: classify the sentiment of an article as
Positive, Neutral, or Negative using the local Ollama LLM.
"""

import logging

from services.ollama_service import generate

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = (
    "Classify the sentiment of the following news article.\n\n"
    "Only answer with one word:\n"
    "Positive\n"
    "Neutral\n"
    "Negative\n\n"
    "Article:\n{text}"
)

_VALID_SENTIMENTS = {"positive", "neutral", "negative"}


async def analyse(text: str) -> str:
    """
    Return ``"Positive"``, ``"Neutral"``, or ``"Negative"`` for *text*.
    Falls back to ``"Neutral"`` if the LLM response is unexpected.
    """
    if not text:
        return "Neutral"

    prompt = _PROMPT_TEMPLATE.format(text=text)
    logger.info("[SentimentAgent] Classifying sentiment …")

    raw = await generate(prompt)
    sentiment = raw.strip().strip(".").capitalize()

    if sentiment.lower() not in _VALID_SENTIMENTS:
        logger.warning(
            "[SentimentAgent] Unexpected LLM response '%s'; defaulting to Neutral",
            raw,
        )
        # Try to extract a valid sentiment from the response
        lower = raw.lower()
        if "positive" in lower:
            sentiment = "Positive"
        elif "negative" in lower:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

    logger.info("[SentimentAgent] Sentiment → %s", sentiment)
    return sentiment
