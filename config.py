"""
config.py — CoreInventory Gmail Configuration
Credentials are set directly here. No .env file needed.
"""

import os

# ── OTP Behaviour ──────────────────────────────────────────────────────────
OTP_LENGTH          = 6
OTP_EXPIRY_SECONDS  = 600   # 10 minutes
OTP_MAX_ATTEMPTS    = 3
OTP_RESEND_COOLDOWN = 60    # seconds

# ── Gmail SMTP ─────────────────────────────────────────────────────────────
# Replace these two values with your actual credentials.
# SMTP_PASSWORD must be a Gmail App Password (16 chars, spaces are stripped).
# Get one at: myaccount.google.com → Security → App passwords

SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587

SMTP_USER     = "krrishmevada34@gmail.com"          # ← your Gmail
SMTP_PASSWORD = "rpnryjomlimlteez"                # ← App Password, no spaces

SMTP_FROM_EMAIL = SMTP_USER
SMTP_FROM_NAME  = "CoreInventory"
