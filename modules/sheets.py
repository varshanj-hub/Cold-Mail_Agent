"""
modules/sheets.py
Reads company list from Google Sheets.
Writes back status, timestamp, subject after each send.
"""

import sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

log = logging.getLogger(__name__)

from config.settings import (
    SHEET_ID, SHEET_NAME,
    COL_COMPANY, COL_EMAIL,
    COL_STATUS, COL_SENT_AT,
    GOOGLE_CREDENTIALS_FILE, DATA_START_ROW,
)

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _service():
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=_SCOPES)
    return build("sheets", "v4", credentials=creds).spreadsheets()


def get_companies() -> list[dict]:
    """
    Returns list of dicts: { row_index, company_name, email }.
    Checks Column C (Status) first — skips any row already marked 'Sent'.
    """
    svc    = _service()
    range_ = f"{SHEET_NAME}!A{DATA_START_ROW}:D"
    rows   = svc.values().get(spreadsheetId=SHEET_ID, range=range_).execute().get("values", [])

    companies = []
    for i, row in enumerate(rows):
        row_idx = i + DATA_START_ROW
        company = row[COL_COMPANY - 1].strip() if len(row) >= COL_COMPANY else ""
        email   = row[COL_EMAIL   - 1].strip() if len(row) >= COL_EMAIL   else ""
        status  = row[COL_STATUS  - 1].strip() if len(row) >= COL_STATUS  else ""

        # Check status FIRST — skip rows already sent
        if status.lower() == "sent":
            log.info(f"  [SKIP] Row {row_idx} | {company} -- already Sent")
            continue

        if not company or not email:
            log.info(f"  [SKIP] Row {row_idx} -- missing company name or email")
            continue

        companies.append({
            "row_index":    row_idx,
            "company_name": company,
            "email":        email,
        })

    return companies


def update_status(row_index: int, status: str) -> None:
    """Writes status and timestamp back to Columns C and D."""
    svc       = _service()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    svc.values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={
            "valueInputOption": "RAW",
            "data": [
                {"range": f"{SHEET_NAME}!C{row_index}", "values": [[status]]},
                {"range": f"{SHEET_NAME}!D{row_index}", "values": [[timestamp]]},
            ]
        }
    ).execute()