"""
Email service – sends summarised news results as a styled HTML email.

Uses Python's built-in ``smtplib`` and ``email`` modules (no extra deps).
Configured for Gmail SMTP by default, but works with any SMTP provider.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_NAME

logger = logging.getLogger(__name__)


def _build_html(topic: str, articles: List[Dict]) -> str:
    """Build a beautiful HTML email body from the summarised articles."""

    article_cards = ""
    for art in articles:
        sentiment = art.get("sentiment", "Neutral")
        if sentiment == "Positive":
            badge_color = "#22c55e"
            badge_bg = "rgba(34,197,94,0.12)"
        elif sentiment == "Negative":
            badge_color = "#ef4444"
            badge_bg = "rgba(239,68,68,0.12)"
        else:
            badge_color = "#94a3b8"
            badge_bg = "rgba(148,163,184,0.12)"

        article_cards += f"""
        <tr><td style="padding:12px 0;">
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#1e293b;border-radius:12px;border:1px solid rgba(255,255,255,0.06);">
            <tr><td style="padding:20px 24px;">
              <!-- Title & Badge -->
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="font-size:16px;font-weight:700;color:#f1f5f9;line-height:1.4;padding-right:12px;">
                    {art.get("title", "Untitled")}
                  </td>
                  <td width="90" align="right" valign="top">
                    <span style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;color:{badge_color};background:{badge_bg};border:1px solid {badge_color}33;">
                      {sentiment}
                    </span>
                  </td>
                </tr>
              </table>
              <!-- Meta -->
              <p style="margin:10px 0 0;font-size:12px;color:#64748b;">
                📰 {art.get("source", "Unknown")} &nbsp;·&nbsp; 📅 {art.get("published_at", "")}
              </p>
              <!-- Summary -->
              <p style="margin:14px 0 0;font-size:14px;line-height:1.7;color:#cbd5e1;">
                {art.get("summary", "")}
              </p>
              <!-- Link -->
              <p style="margin:14px 0 0;">
                <a href="{art.get("url", "#")}" style="color:#818cf8;font-size:13px;font-weight:600;text-decoration:none;">
                  Read Original →
                </a>
              </p>
            </td></tr>
          </table>
        </td></tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#0b0f19;font-family:'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#0b0f19;">
        <tr><td align="center" style="padding:32px 16px;">
          <table width="600" cellpadding="0" cellspacing="0">

            <!-- Header -->
            <tr><td style="padding:24px 28px;background:linear-gradient(135deg,#6366f1,#a855f7);border-radius:14px 14px 0 0;text-align:center;">
              <h1 style="margin:0;font-size:22px;color:#ffffff;font-weight:800;letter-spacing:-0.3px;">
                🧠 Smart News Summarizer
              </h1>
              <p style="margin:6px 0 0;font-size:13px;color:rgba(255,255,255,0.8);">
                AI-Powered News Intelligence
              </p>
            </td></tr>

            <!-- Body -->
            <tr><td style="padding:24px 28px;background:#111827;border-radius:0 0 14px 14px;">
              <p style="margin:0 0 4px;font-size:14px;color:#94a3b8;">Your news summary for:</p>
              <h2 style="margin:0 0 20px;font-size:20px;color:#f1f5f9;font-weight:700;">
                {topic}
              </h2>

              <p style="margin:0 0 8px;font-size:13px;color:#64748b;">
                {len(articles)} article{"s" if len(articles) != 1 else ""} summarised
              </p>

              <table width="100%" cellpadding="0" cellspacing="0">
                {article_cards}
              </table>

              <!-- Footer -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:24px;border-top:1px solid rgba(255,255,255,0.06);">
                <tr><td style="padding:18px 0 0;text-align:center;">
                  <p style="margin:0;font-size:12px;color:#475569;">
                    Sent by Smart News Summarizer Agent · FastAPI · Ollama · NewsAPI
                  </p>
                </td></tr>
              </table>
            </td></tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """
    return html


async def send_summary_email(
    recipient: str,
    topic: str,
    articles: List[Dict],
) -> None:
    """
    Send the summarised articles as a styled HTML email.

    Raises ``ValueError`` if SMTP credentials are not configured.
    Raises ``smtplib.SMTPException`` on delivery failure.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError(
            "Email is not configured. Set SMTP_USER and SMTP_PASSWORD in your .env file."
        )

    subject = f"📰 News Summary: {topic}"
    html_body = _build_html(topic, articles)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = recipient

    # Plain-text fallback
    plain_lines = [f"News Summary: {topic}\n"]
    for art in articles:
        plain_lines.append(f"• {art.get('title', '')} [{art.get('sentiment', '')}]")
        plain_lines.append(f"  {art.get('summary', '')}")
        plain_lines.append(f"  Source: {art.get('source', '')} | {art.get('url', '')}\n")
    plain_text = "\n".join(plain_lines)

    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    logger.info("Sending summary email to %s via %s:%d", recipient, SMTP_HOST, SMTP_PORT)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

    logger.info("Email sent successfully to %s", recipient)


async def send_verification_email(recipient: str, otp: str) -> None:
    """Send an OTP code for account verification."""
    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError("Email is not configured.")

    subject = "🔑 Verify your Smart News Summarizer account"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:32px;background:#0b0f19;font-family:sans-serif;text-align:center;color:#f1f5f9;">
      <h2 style="color:#ffffff;">Verify Your Account</h2>
      <p>Your one-time password (OTP) is:</p>
      <div style="margin:24px auto;font-size:32px;font-weight:bold;letter-spacing:4px;color:#a855f7;">{otp}</div>
      <p style="font-size:12px;color:#64748b;">This code is required to complete your registration.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = recipient

    msg.attach(MIMEText(f"Your OTP is: {otp}", "plain"))
    msg.attach(MIMEText(html_body, "html"))

    logger.info("Sending OTP email to %s", recipient)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)

    logger.info("OTP Email sent successfully to %s", recipient)
