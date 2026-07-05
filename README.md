# 🧠 Smart News Summarizer Agent

An AI-powered web application that fetches live news articles, generates concise 3-sentence summaries, and classifies sentiment — all using a **local LLM** (Ollama) with zero API costs.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Ollama](https://img.shields.io/badge/Ollama-llama3.1:8b-purple)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Live News Search** | Fetches latest articles from NewsAPI by keyword |
| 🤖 **AI Summarization** | Generates exactly 3-sentence summaries via local LLM |
| 🎭 **Sentiment Analysis** | Classifies each article as Positive / Neutral / Negative |
| ⚡ **FastAPI REST API** | Clean `GET /summarize` endpoint with JSON response |
| 🎨 **Premium Dashboard** | Dark-mode glassmorphism UI with animations |
| 💾 **TTL Cache** | 30-minute cache avoids redundant LLM calls |
| 🏗️ **Multi-Agent Architecture** | Modular Fetcher → Cleaner → Summarizer → Sentiment pipeline |

---

## 🏗️ Architecture

```
User → HTML Dashboard → FastAPI
                            │
                     ┌──────┼──────┐
                     ▼      ▼      ▼
              Fetcher   Cleaner   ...
              (NewsAPI)  (regex)
                     │      │
                     ▼      ▼
              Summarizer → Sentiment
              (Ollama)     (Ollama)
                     │
                     ▼
               TTL Cache → JSON Response → Card UI
```

---

## 📁 Project Structure

```
smart-news-agent/
├── app.py                  # FastAPI application & routes
├── main.py                 # Uvicorn entry point
├── config.py               # Environment variables & constants
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment file
│
├── agents/
│   ├── fetcher.py          # Agent 1 – Fetch articles from NewsAPI
│   ├── cleaner.py          # Agent 2 – Clean article text
│   ├── summarizer.py       # Agent 3 – LLM summarization
│   └── sentiment.py        # Agent 4 – LLM sentiment classification
│
├── services/
│   ├── news_api.py         # NewsAPI HTTP client
│   ├── ollama_service.py   # Ollama LLM client
│   └── cache.py            # TTL cache wrapper
│
├── models/
│   └── response.py         # Pydantic response schemas
│
├── templates/
│   └── index.html          # Jinja2 HTML template
│
└── static/
    ├── style.css           # Premium dark-mode stylesheet
    └── script.js           # Frontend logic
```

---

## 🚀 Setup Instructions

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Runtime |
| Ollama | latest | Local LLM |
| NewsAPI Key | free tier | News data |

### Step 1 — Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2 — Pull the LLM model

```bash
ollama pull llama3.1:8b
```

### Step 3 — Start Ollama server

```bash
ollama serve
```

> Keep this running in a separate terminal.

### Step 4 — Get a NewsAPI key

1. Go to [https://newsapi.org/register](https://newsapi.org/register)
2. Sign up for a **free** account
3. Copy your API key

### Step 5 — Clone & configure

```bash
cd smart-news-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your NEWS_API_KEY
```

### Step 6 — Run the application

```bash
python main.py
```

Open your browser at **http://localhost:8000** 🎉

---

## 📡 API Reference

### `GET /summarize`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic` | string | *required* | Search keyword |
| `max_articles` | integer | `5` | Articles to process (1-20) |
| `language` | string | `en` | Language code |

#### Example Request

```
GET /summarize?topic=artificial+intelligence&max_articles=3&language=en
```

#### Example Response

```json
{
  "articles": [
    {
      "title": "OpenAI launches new model",
      "source": "TechCrunch",
      "summary": "OpenAI has released a faster model. It improves reasoning and coding performance. The company expects developers to adopt it quickly.",
      "sentiment": "Positive",
      "url": "https://techcrunch.com/...",
      "published_at": "2026-06-23"
    }
  ],
  "total": 3,
  "fetched_at": "2026-06-23"
}
```

---

## 📝 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEWS_API_KEY` | ✅ | — | Your NewsAPI.org key |
| `OLLAMA_BASE_URL` | ❌ | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | ❌ | `llama3.1:8b` | Model to use |
| `CACHE_TTL_SECONDS` | ❌ | `1800` | Cache lifetime (30 min) |
| `LOG_LEVEL` | ❌ | `INFO` | Logging verbosity |

---

## ⚠️ Limitations

- **NewsAPI free tier**: ~100 requests/day, no article body for some sources
- **Ollama**: requires sufficient RAM (~8 GB for llama3.1:8b)
- **No persistent storage**: results are cached in-memory only
- **Sequential LLM calls**: each article is processed one at a time

---

## 📄 License

MIT — free for personal and commercial use.
