"""
modules/gmail_sender.py
Sends email via Gmail API using OAuth2 (personal Gmail).
Attaches resume PDF to every email.

First-time setup — run once:
  python modules/gmail_sender.py --auth

After that the agent runs fully automated using the saved token.
"""

import sys, os, base64
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email.mime.multipart import MIMEMultipart
from email                import encoders

from config.settings import SENDER_EMAIL, GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE

_SCOPES     = ["https://www.googleapis.com/auth/gmail.send"]
RESUME_PATH = os.getenv("RESUME_PATH", "config/resume.pdf")


def _get_service():
    from google.oauth2.credentials      import Credentials
    from google_auth_oauthlib.flow      import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery      import build

    creds = None

    if os.path.exists(GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, _SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GMAIL_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _build_raw(to: str, subject: str, body: str) -> dict:
    msg           = MIMEMultipart()
    msg["to"]     = to
    msg["from"]   = SENDER_EMAIL
    msg["subject"] = subject

    # Convert plain text to clean HTML — full width, no max-width restriction
    html_body = """<html><body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #000000;">{}</body></html>""".format(
        body
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n\n", "</p><p>")
        .replace("\n", "<br>")
        .replace("&bull;", "&#8226;")
        .replace("•", "&#8226;")
        .join(["<p>", "</p>"])
    )

    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Attach resume PDF
    if os.path.exists(RESUME_PATH):
        with open(RESUME_PATH, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = os.path.basename(RESUME_PATH)
            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
            msg.attach(part)
    else:
        print(f"  [WARN] Resume not found at '{RESUME_PATH}' — sending without attachment")

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


def send_email(to: str, subject: str, body: str) -> bool:
    """Sends email with resume attached. Returns True on success."""
    try:
        svc = _get_service()
        svc.users().messages().send(
            userId="me",
            body=_build_raw(to, subject, body)
        ).execute()
        print(f"  [SENT] -> {to}")
        return True
    except Exception as e:
        print(f"  [GMAIL ERROR] {to}: {e}")
        return False


if __name__ == "__main__":
    if "--auth" in sys.argv:
        _get_service()
        print(f"[OK] Gmail authorised. Token saved to {GMAIL_TOKEN_FILE}")
    else:
        ok = send_email(
            to      = SENDER_EMAIL,
            subject = "Cold Mail Agent — Test (with Resume)",
            body    = "Test email with resume attached. It works!"
        )
        print("Result:", "OK" if ok else "FAILED")