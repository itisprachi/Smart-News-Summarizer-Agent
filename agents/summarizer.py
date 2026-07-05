"""
Summarizer Agent – Agent 3

Responsibility: generate a concise 3-sentence summary for an article using
the local Ollama LLM (llama3.1:8b by default).
"""

import logging

from services.ollama_service import generate

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = (
    "Summarize the following news article into exactly three concise sentences "
    "written in simple English.\n\n"
    "Article:\n{article}\n\n"
    "Do not invent facts."
)


async def summarize(article_text: str) -> str:
    """
    Send *article_text* to the LLM and return a 3-sentence summary.
    """
    if not article_text:
        return "No article content available to summarize."

    prompt = _PROMPT_TEMPLATE.format(article=article_text)
    logger.info("[SummarizerAgent] Requesting summary (%d chars input)", len(article_text))

    summary = await generate(prompt)

    if not summary:
        summary = "Summary could not be generated."

    logger.info("[SummarizerAgent] Summary generated (%d chars)", len(summary))
    return summary
