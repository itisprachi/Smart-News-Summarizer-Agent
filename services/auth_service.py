"""
Auth service – in-memory user store with JWT cookie-based sessions.

Beginner-friendly: uses hashlib for password hashing (no heavy deps)
and PyJWT for token management stored in httponly cookies.
"""

import hashlib
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List

import json
import jwt
import random

from config import JWT_SECRET, JWT_EXPIRY_HOURS

logger = logging.getLogger(__name__)

USERS_FILE = "users.json"

def _load_users() -> Dict[str, dict]:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load users from %s: %s", USERS_FILE, e)
    return {}

def _save_users():
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(_users, f, indent=4)
    except Exception as e:
        logger.error("Failed to save users to %s: %s", USERS_FILE, e)

# ── In-memory user store ─────────────────────────────────────────────────────
# { email: { "id": str, "name": str, "email": str, "password_hash": str } }
_users: Dict[str, dict] = _load_users()

# { email: { "otp": str, "user": dict, "expires_at": float } }
_pending_users: Dict[str, dict] = {}


# ── Password helpers ─────────────────────────────────────────────────────────

def _hash_password(password: str, salt: Optional[str] = None) -> str:
    """SHA-256 hash with a random salt (beginner-friendly, no bcrypt dep)."""
    if salt is None:
        salt = uuid.uuid4().hex[:16]
    hashed = hashlib.sha256(f"{salt}${password}".encode()).hexdigest()
    return f"{salt}${hashed}"


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its stored hash."""
    salt = stored_hash.split("$")[0]
    return _hash_password(password, salt) == stored_hash


# ── User CRUD ────────────────────────────────────────────────────────────────

def signup(name: str, email: str, password: str) -> str:
    """
    Begin registration process for a new user.
    Generates an OTP and stores the pending user.
    Returns the generated OTP as a string.
    Raises ``ValueError`` if the email is already taken.
    """
    email_lower = email.lower().strip()

    if email_lower in _users:
        raise ValueError("An account with this email already exists.")

    user = {
        "id": uuid.uuid4().hex[:12],
        "name": name.strip(),
        "email": email_lower,
        "password_hash": _hash_password(password),
        "subscriptions": [],
    }
    
    otp = str(random.randint(100000, 999999))
    _pending_users[email_lower] = {
        "otp": otp,
        "user": user,
    }
    
    logger.info("Generated OTP for pending user: %s", email_lower)
    return otp

def verify_otp(email: str, otp: str) -> dict:
    """
    Verify the OTP for a pending user and activate their account.
    Returns the user dict (without password).
    Raises ``ValueError`` on invalid or expired OTP.
    """
    email_lower = email.lower().strip()
    
    if email_lower not in _pending_users:
        raise ValueError("No pending registration found for this email.")
        
    pending = _pending_users[email_lower]
    if pending["otp"] != otp.strip():
        raise ValueError("Invalid OTP code.")
        
    user = pending["user"]
    _users[email_lower] = user
    del _pending_users[email_lower]
    _save_users()
    
    logger.info("New user registered and verified: %s", email_lower)
    return _safe_user(user)


def login(email: str, password: str) -> dict:
    """
    Authenticate a user. Returns the user dict (without password).
    Raises ``ValueError`` on invalid credentials.
    """
    email_lower = email.lower().strip()
    user = _users.get(email_lower)

    if not user or not _verify_password(password, user["password_hash"]):
        raise ValueError("Invalid email or password.")

    logger.info("User logged in: %s", email_lower)
    return _safe_user(user)


def get_user_by_email(email: str) -> Optional[dict]:
    """Return the user dict (without password) or None."""
    user = _users.get(email.lower().strip())
    if user and "subscriptions" not in user:
        user["subscriptions"] = []
    return _safe_user(user) if user else None


def subscribe_topic(email: str, topic: str) -> dict:
    """Subscribe a user to a topic. Returns the updated user dict."""
    email_lower = email.lower().strip()
    topic = topic.strip()
    if email_lower not in _users:
        raise ValueError("User not found.")
    
    user = _users[email_lower]
    if "subscriptions" not in user:
        user["subscriptions"] = []
    
    if topic not in user["subscriptions"]:
        user["subscriptions"].append(topic)
        _save_users()
    
    return _safe_user(user)


def unsubscribe_topic(email: str, topic: str) -> dict:
    """Unsubscribe a user from a topic. Returns the updated user dict."""
    email_lower = email.lower().strip()
    topic = topic.strip()
    if email_lower not in _users:
        raise ValueError("User not found.")
    
    user = _users[email_lower]
    if "subscriptions" not in user:
        user["subscriptions"] = []
    
    if topic in user["subscriptions"]:
        user["subscriptions"].remove(topic)
        _save_users()
    
    return _safe_user(user)


def get_all_users() -> List[dict]:
    """Return a list of all safe user dicts."""
    return [_safe_user(u) for u in _users.values()]


def _safe_user(user: dict) -> dict:
    """Return user dict without the password hash."""
    return {k: v for k, v in user.items() if k != "password_hash"}


# ── JWT Token ────────────────────────────────────────────────────────────────

def create_token(user: dict) -> str:
    """Create a JWT token for the given user."""
    payload = {
        "sub": user["email"],
        "name": user["name"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.
    Returns the user dict or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        email = payload.get("sub")
        if email:
            return get_user_by_email(email)
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
    except jwt.InvalidTokenError as exc:
        logger.debug("Invalid token: %s", exc)
    return None
