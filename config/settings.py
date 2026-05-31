"""
config/settings.py
Loads all settings from .env — single source of truth for the project.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing required env var: {key}")
    return val


def _bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in ("true", "1", "yes")


def _int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


# ── Personal ──────────────────────────────────────────────────────────────────
YOUR_NAME       = _require("YOUR_NAME")
YOUR_PHONE      = _require("YOUR_PHONE")
YOUR_LINKEDIN   = _require("YOUR_LINKEDIN")
YOUR_GITHUB     = _require("YOUR_GITHUB")
YOUR_BIO        = _require("YOUR_BIO")
YOUR_SKILLS     = [s.strip() for s in _require("YOUR_SKILLS").split(",")]
YOUR_EDUCATION  = _require("YOUR_EDUCATION")
YOUR_EXPERIENCE = [e.strip() for e in _require("YOUR_EXPERIENCE").split("|")]
YOUR_PROJECTS   = _require("YOUR_PROJECTS")

# ── Google Sheets ─────────────────────────────────────────────────────────────
SHEET_ID                      = _require("SHEET_ID")
SHEET_NAME                    = os.getenv("SHEET_NAME", "Sheet1")
GOOGLE_CREDENTIALS_FILE       = os.getenv("GOOGLE_CREDENTIALS_FILE", "config/service_account.json")
GOOGLE_SERVICE_ACCOUNT_EMAIL  = os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
GOOGLE_PROJECT_ID             = os.getenv("GOOGLE_PROJECT_ID", "")

COL_COMPANY    = 1   # A
COL_EMAIL      = 2   # B
COL_STATUS     = 3   # C  ← agent writes Sent / Failed
COL_SENT_AT    = 4   # D  ← agent writes timestamp
DATA_START_ROW = _int("DATA_START_ROW", 2)

# ── Gmail ─────────────────────────────────────────────────────────────────────
SENDER_EMAIL           = _require("SENDER_EMAIL")
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "config/credentials.json")
GMAIL_TOKEN_FILE       = os.getenv("GMAIL_TOKEN_FILE",       "config/token.json")

# ── OpenAI ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = _require("OPENAI_API_KEY")
LLM_MODEL      = os.getenv("LLM_MODEL", "gpt-4o-mini")

# ── Agent behaviour ───────────────────────────────────────────────────────────
DRY_RUN            = _bool("DRY_RUN",  False)
VERBOSE            = _bool("VERBOSE",  True)
SEND_DELAY_SECONDS = _int("SEND_DELAY_SECONDS", 5)
DDG_MAX_RESULTS    = _int("DDG_MAX_RESULTS",    5)