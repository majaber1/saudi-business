"""Single-use account tokens and optional SMTP delivery."""
from __future__ import annotations

import hashlib
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.parse import urlencode


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def token_digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def issue_token(db, models, user_id: int, purpose: str, lifetime_minutes: int) -> str:
    now = utc_now_naive()
    db.query(models.AccountToken).filter(
        models.AccountToken.user_id == user_id,
        models.AccountToken.purpose == purpose,
        models.AccountToken.consumed_at.is_(None),
    ).update({"consumed_at": now}, synchronize_session=False)
    raw = secrets.token_urlsafe(32)
    db.add(models.AccountToken(
        user_id=user_id,
        purpose=purpose,
        token_hash=token_digest(raw),
        expires_at=now + timedelta(minutes=lifetime_minutes),
    ))
    db.commit()
    return raw


def consume_token(db, models, raw: str, purpose: str):
    now = utc_now_naive()
    row = db.query(models.AccountToken).filter_by(
        token_hash=token_digest(raw), purpose=purpose, consumed_at=None,
    ).first()
    if row is None or row.expires_at <= now:
        return None
    row.consumed_at = now
    db.commit()
    return row


def public_account_url(path: str, raw_token: str) -> str:
    base = os.getenv("PUBLIC_WEB_URL", "http://localhost:3000").rstrip("/")
    return f"{base}{path}?{urlencode({'token': raw_token})}"


def send_account_email(recipient: str, purpose: str, action_url: str, locale: str) -> bool:
    """Deliver via configured SMTP. Returns False when delivery is not configured."""
    host = os.getenv("SMTP_HOST", "").strip()
    sender = os.getenv("SMTP_FROM", "").strip()
    if not host or not sender:
        return False
    ar = locale == "ar"
    subject = ("تأكيد بريدك في سعودي بزنس" if purpose == "verify_email" else "إعادة تعيين كلمة مرور سعودي بزنس") if ar else ("Verify your Saudi Business email" if purpose == "verify_email" else "Reset your Saudi Business password")
    body = ("استخدم الرابط الآمن التالي لإكمال الطلب:\n" if ar else "Use this secure link to complete your request:\n") + action_url
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=10) as smtp:
        if os.getenv("SMTP_STARTTLS", "true").lower() in {"1", "true", "yes"}:
            smtp.starttls()
        username = os.getenv("SMTP_USERNAME", "")
        password = os.getenv("SMTP_PASSWORD", "")
        if username:
            smtp.login(username, password)
        smtp.send_message(message)
    return True
