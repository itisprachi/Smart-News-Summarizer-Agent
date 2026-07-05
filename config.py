"""
Configuration module for Smart News Summarizer Agent.
Loads environment variables and defines application constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── News APIs ──────────────────────────────────────────────────────────────────
NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
NEWS_API_BASE_URL: str = "https://newsapi.org/v2/everything"

GNEWS_API_KEY: str = os.getenv("GNEWS_API_KEY", "")
GNEWS_BASE_URL: str = "https://gnews.io/api/v4/search"

# ── Ollama ───────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# ── Cache ────────────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "1800"))  # 30 min
CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "128"))

# ── Email / SMTP ─────────────────────────────────────────────────────────────
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")          # e.g. you@gmail.com
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")   # Gmail App Password
SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Smart News Summarizer")

# ── Defaults ─────────────────────────────────────────────────────────────────
DEFAULT_MAX_ARTICLES: int = 5
DEFAULT_LANGUAGE: str = "en"

# ── Auth / JWT ───────────────────────────────────────────────────────────────
JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production-please")
JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
