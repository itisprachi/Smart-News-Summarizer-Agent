"""
Cleaner Agent – Agent 2

Responsibility: sanitise raw article text before sending it to the LLM.

Removes HTML tags, excessive whitespace, line-breaks, and common junk
patterns that appear in NewsAPI content payloads.
"""

import logging
import re

logger = logging.getLogger(__name__)


def clean(text: str) -> str:
    """
    Clean *text* using rule-based transformations.

    Steps
    -----
    1. Strip HTML tags.
    2. Decode common HTML entities.
    3. Remove URLs.
    4. Collapse multiple spaces / newlines.
    5. Strip leading / trailing whitespace.
    """
    if not text:
        return ""

    # 1 – HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # 2 – HTML entities
    text = (
        text.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&#39;", "'")
            .replace("&nbsp;", " ")
    )

    # 3 – URLs
    text = re.sub(r"https?://\S+", "", text)

    # 4 – Truncation markers from NewsAPI (e.g. "… [+1234 chars]")
    text = re.sub(r"\[\+\d+ chars\]", "", text)

    # 5 – Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    # 6 – Strip
    text = text.strip()

    logger.debug("[CleanerAgent] Cleaned text length: %d chars", len(text))
    return text
