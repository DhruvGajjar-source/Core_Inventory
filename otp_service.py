"""
otp_service.py — Gmail OTP delivery and verification
"""

import random
import string
import time
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    SMTP_HOST, SMTP_PORT,
    SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM_EMAIL, SMTP_FROM_NAME,
    OTP_LENGTH, OTP_EXPIRY_SECONDS,
    OTP_MAX_ATTEMPTS, OTP_RESEND_COOLDOWN,
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

otp_store: dict = {}


def _generate_otp() -> str:
    return "".join(random.SystemRandom().choices(string.digits, k=OTP_LENGTH))


def send_otp(email: str, force: bool = False) -> dict:
    now = time.time()

    # ── Debug: print exactly what config loaded ──────────────────────────
    print(f"\n{'='*60}")
    print(f"  OTP REQUEST for: {email}")
    print(f"  SMTP_USER     : '{SMTP_USER}'")
    print(f"  SMTP_PASSWORD : '{'*' * len(SMTP_PASSWORD)}' (len={len(SMTP_PASSWORD)})")
    print(f"  SMTP_FROM     : '{SMTP_FROM_EMAIL}'")
    print(f"  SMTP_HOST     : {SMTP_HOST}:{SMTP_PORT}")
    print(f"{'='*60}\n")

    existing = otp_store.get(email)
    if not force and existing:
        elapsed = now - existing.get("last_sent", 0)
        if elapsed < OTP_RESEND_COOLDOWN:
            wait = int(OTP_RESEND_COOLDOWN - elapsed)
            return {"ok": False, "message": f"Please wait {wait}s before requesting a new OTP."}

    if not SMTP_USER or not SMTP_PASSWORD:
        msg = (
            f"Email not configured. "
            f"SMTP_USER='{SMTP_USER}' SMTP_PASSWORD len={len(SMTP_PASSWORD)}. "
            f"Make sure your .env file is in the project root folder "
            f"(same folder as app.py) and contains SMTP_USER and SMTP_PASSWORD."
        )
        print(f"  ERROR: {msg}")
        return {"ok": False, "message": msg}

    otp = _generate_otp()
    otp_store[email] = {
        "otp":        otp,
        "expires_at": now + OTP_EXPIRY_SECONDS,
        "attempts":   0,
        "last_sent":  now,
    }
    print(f"  Generated OTP: {otp}  (also printed here in case email fails)")
    return _send_gmail(email, otp)


def verify_otp_code(email: str, entered: str) -> dict:
    entry = otp_store.get(email)

    if not entry:
        return {"ok": False, "message": "No OTP found. Please request a new one."}
    if time.time() > entry["expires_at"]:
        otp_store.pop(email, None)
        return {"ok": False, "message": "OTP has expired. Please request a new one."}
    if entry["attempts"] >= OTP_MAX_ATTEMPTS:
        otp_store.pop(email, None)
        return {"ok": False, "message": "Too many failed attempts. Please request a new OTP."}
    if entered.strip() != entry["otp"]:
        entry["attempts"] += 1
        left = OTP_MAX_ATTEMPTS - entry["attempts"]
        return {"ok": False, "message": f"Incorrect OTP. {left} attempt(s) remaining."}

    otp_store.pop(email, None)
    return {"ok": True, "message": "OTP verified."}


def _send_gmail(recipient: str, otp: str) -> dict:
    expiry_min = OTP_EXPIRY_SECONDS // 60

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;
                border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:#0f172a;padding:24px;text-align:center;">
        <h2 style="color:white;margin:0;font-size:20px;">📦 CoreInventory</h2>
      </div>
      <div style="padding:32px;">
        <p style="color:#334155;font-size:15px;margin-top:0;">
          You requested a password reset. Enter this OTP to continue:
        </p>
        <div style="background:#f8fafc;border:2px dashed #2563eb;border-radius:10px;
                    text-align:center;padding:28px;margin:24px 0;">
          <span style="font-size:44px;font-weight:700;letter-spacing:0.35em;
                       color:#2563eb;font-family:monospace;">{otp}</span>
        </div>
        <p style="color:#64748b;font-size:13px;margin-bottom:0;">
          ⏱ Expires in <strong>{expiry_min} minutes</strong>.
          If you did not request this, you can safely ignore this email.
        </p>
      </div>
      <div style="background:#f1f5f9;padding:14px;text-align:center;
                  font-size:12px;color:#94a3b8;">
        CoreInventory · Inventory Management System
      </div>
    </div>
    """
    text = f"Your CoreInventory OTP is: {otp}\nExpires in {expiry_min} minutes."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your CoreInventory Password Reset OTP"
    msg["From"]    = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg["To"]      = recipient
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        print(f"  Connecting to {SMTP_HOST}:{SMTP_PORT} ...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        server.set_debuglevel(1)   # prints every SMTP command to terminal
        server.ehlo()
        server.starttls()
        server.ehlo()
        print(f"  Logging in as {SMTP_USER} ...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print(f"  Sending to {recipient} ...")
        server.sendmail(SMTP_FROM_EMAIL, recipient, msg.as_string())
        server.quit()
        print(f"  SUCCESS — OTP email sent to {recipient}")
        return {"ok": True,
                "message": f"OTP sent to {recipient}. Check your inbox (and spam folder)."}

    except smtplib.SMTPAuthenticationError as e:
        print(f"  AUTH FAILED: {e}")
        return {"ok": False,
                "message": (
                    "Gmail authentication failed. "
                    "Check that SMTP_USER is your full Gmail address and "
                    "SMTP_PASSWORD is a Gmail App Password "
                    "(not your regular password). "
                    "Get one at: myaccount.google.com → Security → App passwords"
                )}
    except smtplib.SMTPException as e:
        print(f"  SMTP ERROR: {e}")
        return {"ok": False, "message": f"Email delivery failed: {e}"}
    except Exception as e:
        print(f"  UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return {"ok": False, "message": f"Unexpected error: {type(e).__name__}: {e}"}
