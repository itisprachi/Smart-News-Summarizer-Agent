"""
Smart News Summarizer Agent – FastAPI application.

Exposes:
    GET  /              → HTML dashboard
    GET  /summarize     → JSON API
    POST /signup        → Register a new user
    POST /login         → Authenticate & set session cookie
    POST /logout        → Clear session cookie
    GET  /me            → Current logged-in user info
    POST /send-email    → Email summary to logged-in user
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from config import DEFAULT_LANGUAGE, DEFAULT_MAX_ARTICLES, LOG_LEVEL
from models.response import SummarizeResponse
from services import cache
from services.email_service import send_summary_email, send_verification_email
from services import auth_service
from services import pipeline

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("smart-news-agent")

# ── Scheduler ────────────────────────────────────────────────────────────────
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.newsletter_job import run_daily_newsletter

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler
    scheduler.add_job(run_daily_newsletter, 'cron', hour=8, minute=0)
    scheduler.start()
    logger.info("APScheduler started. Daily newsletter scheduled for 08:00 AM.")
    yield
    # Shutdown the scheduler
    scheduler.shutdown()
    logger.info("APScheduler shutdown.")


# ── FastAPI instance ─────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart News Summarizer Agent",
    description="Fetch, clean, summarize & sentiment-analyse live news articles.",
    version="1.0.0",
    lifespan=lifespan,
)

# Static files & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── Auth helpers ─────────────────────────────────────────────────────────────

COOKIE_NAME = "session_token"


def _get_current_user(request: Request) -> Optional[dict]:
    """Extract the logged-in user from the session cookie, or return None."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return auth_service.decode_token(token)


def _set_session_cookie(response: Response, token: str):
    """Set an httponly session cookie."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,  # 24 hours
        path="/",
    )


def _clear_session_cookie(response: Response):
    """Remove the session cookie."""
    response.delete_cookie(key=COOKIE_NAME, path="/")


# ── Auth request bodies ─────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class VerifySignupRequest(BaseModel):
    email: str
    otp: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the HTML dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})


# ── Auth endpoints ───────────────────────────────────────────────────────────

@app.post("/signup")
async def signup(payload: SignupRequest, response: Response):
    """Register a new user and set session cookie."""
    if not payload.name or not payload.email or not payload.password:
        return JSONResponse(status_code=400, content={"error": "All fields are required."})

    if "@" not in payload.email:
        return JSONResponse(status_code=400, content={"error": "Invalid email address."})

    if len(payload.password) < 6:
        return JSONResponse(status_code=400, content={"error": "Password must be at least 6 characters."})

    try:
        otp = auth_service.signup(payload.name, payload.email, payload.password)
    except ValueError as exc:
        return JSONResponse(status_code=409, content={"error": str(exc)})

    try:
        await send_verification_email(payload.email, otp)
    except Exception as exc:
        logger.error("Failed to send OTP email: %s", exc)
        return JSONResponse(status_code=500, content={"error": "Failed to send verification email."})

    logger.info("OTP sent to: %s", payload.email)
    return {"message": "OTP sent. Please verify your email."}


@app.post("/verify-signup")
async def verify_signup(payload: VerifySignupRequest, response: Response):
    """Verify OTP and activate account."""
    if not payload.email or not payload.otp:
        return JSONResponse(status_code=400, content={"error": "Email and OTP are required."})

    try:
        user = auth_service.verify_otp(payload.email, payload.otp)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    token = auth_service.create_token(user)
    _set_session_cookie(response, token)

    logger.info("User verified and logged in: %s", user["email"])
    return {"user": user}


@app.post("/login")
async def login(payload: LoginRequest, response: Response):
    """Authenticate user and set session cookie."""
    try:
        user = auth_service.login(payload.email, payload.password)
    except ValueError as exc:
        return JSONResponse(status_code=401, content={"error": str(exc)})

    token = auth_service.create_token(user)
    _set_session_cookie(response, token)

    logger.info("User logged in: %s", user["email"])
    return {"user": user}


@app.post("/logout")
async def logout(response: Response):
    """Clear session cookie."""
    _clear_session_cookie(response)
    return {"message": "Logged out"}


@app.get("/me")
async def get_me(request: Request):
    """Return the current logged-in user or 401."""
    user = _get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not logged in"})
    return {"user": user}


class SubscribeRequest(BaseModel):
    topic: str


@app.post("/api/subscribe")
async def subscribe(payload: SubscribeRequest, request: Request):
    """Subscribe a user to a topic."""
    user = _get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not logged in"})
    
    try:
        updated_user = auth_service.subscribe_topic(user["email"], payload.topic)
        return {"user": updated_user, "message": f"Subscribed to {payload.topic}"}
    except Exception as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})


@app.delete("/api/subscribe")
async def unsubscribe(payload: SubscribeRequest, request: Request):
    """Unsubscribe a user from a topic."""
    user = _get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not logged in"})
    
    try:
        updated_user = auth_service.unsubscribe_topic(user["email"], payload.topic)
        return {"user": updated_user, "message": f"Unsubscribed from {payload.topic}"}
    except Exception as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})


@app.post("/api/trigger-newsletter")
async def trigger_newsletter(request: Request):
    """Manually trigger the daily newsletter job (for testing)."""
    user = _get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not logged in"})
    
    # Run in background so request doesn't hang
    import asyncio
    asyncio.create_task(run_daily_newsletter())
    return {"message": "Newsletter job triggered in the background."}


# ── Summarize endpoint ───────────────────────────────────────────────────────

@app.get("/summarize", response_model=SummarizeResponse)
async def summarize_articles(
    topic: str = Query(..., min_length=1, description="Search keyword"),
    max_articles: int = Query(DEFAULT_MAX_ARTICLES, ge=1, le=20, description="Max articles"),
    language: str = Query(DEFAULT_LANGUAGE, min_length=2, max_length=5, description="Language code"),
):
    """
    Pipeline:
        Fetcher → Cleaner → Summarizer → Sentiment → Cache → JSON
    """
    # ── Cache check ──────────────────────────────────────────────────────────
    cache_key = cache.make_key(topic, max_articles, language)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # ── Pipeline ─────────────────────────────────────────────────────────────
    try:
        results = await pipeline.run_pipeline(topic, max_articles, language)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=502, content={"error": f"Failed to fetch news: {exc}"})
    
    if not results:
        return SummarizeResponse(articles=[], total=0, fetched_at=str(date.today()))

    # ── Build response & cache ───────────────────────────────────────────────
    response = SummarizeResponse(
        articles=results,
        total=len(results),
        fetched_at=str(date.today()),
    )

    cache.put(cache_key, response)
    return response


# ── Email endpoint ───────────────────────────────────────────────────────────

class EmailRequest(BaseModel):
    """Request body for POST /send-email."""
    topic: str
    articles: List[Dict[str, Any]]


@app.post("/send-email")
async def email_summary(payload: EmailRequest, request: Request):
    """
    Send the summarised articles to the LOGGED-IN user's email.
    Requires authentication.
    """
    user = _get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Please log in to send emails."})

    recipient = user["email"]

    if not payload.articles:
        return JSONResponse(status_code=400, content={"error": "No articles to send."})

    try:
        await send_summary_email(
            recipient=recipient,
            topic=payload.topic,
            articles=payload.articles,
        )
        logger.info("Email sent to %s for topic '%s'", recipient, payload.topic)
        return {"message": f"Summary sent to {recipient}"}
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    except Exception as exc:
        logger.error("Email send failed: %s", exc)
        return JSONResponse(status_code=500, content={"error": f"Failed to send email: {exc}"})


# ── Suggestions endpoint ─────────────────────────────────────────────────────

@app.get("/api/suggestions")
async def get_suggestions(q: str = Query(..., min_length=1)):
    """Fetch real-time topic suggestions from Google Autocomplete."""
    url = "http://suggestqueries.google.com/complete/search"
    params = {"client": "firefox", "q": q}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=3.0)
            resp.raise_for_status()
            data = resp.json()
            # Google suggest format with client=firefox: ["query", ["suggestion1", "suggestion2", ...]]
            suggestions = data[1] if len(data) > 1 else []
            return JSONResponse(content={"suggestions": suggestions})
    except Exception as exc:
        logger.error("Suggestion fetch error: %s", exc)
        return JSONResponse(content={"suggestions": []})
