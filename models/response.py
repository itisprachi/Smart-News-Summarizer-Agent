"""
Pydantic response models for the Smart News Summarizer Agent.
"""

from pydantic import BaseModel, Field
from typing import List


class ArticleResult(BaseModel):
    """A single summarised article."""
    title: str = Field(..., description="Original article headline")
    source: str = Field(..., description="News source name")
    summary: str = Field(..., description="Three-sentence AI-generated summary")
    sentiment: str = Field(..., description="Positive | Neutral | Negative")
    url: str = Field(..., description="Original article URL")
    published_at: str = Field(..., description="Publication date (YYYY-MM-DD)")


class SummarizeResponse(BaseModel):
    """Response payload for GET /summarize."""
    articles: List[ArticleResult]
    total: int = Field(..., description="Number of articles returned")
    fetched_at: str = Field(..., description="ISO date when results were generated")
