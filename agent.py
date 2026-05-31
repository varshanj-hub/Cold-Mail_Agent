"""
agent.py — Cold Mail Agent Orchestrator

Per company:
  1. Read from Google Sheets
  2. Parse email → recipient name / type
  3. DuckDuckGo → company summary
  4. GPT-4o-mini → personalised cold email
  5. Gmail API → send
  6. Update Sheet → status + timestamp + subject
"""

import os, sys, time, logging, traceback, io
from datetime import datetime

# Force UTF-8 on the console stream regardless of Windows codepage
_utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# ── logging ───────────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
_log_file = f"logs/agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(_log_file, encoding='utf-8'),
        logging.StreamHandler(_utf8_stdout),
    ],
)
log = logging.getLogger(__name__)

# ── imports ───────────────────────────────────────────────────────────────────
from config.settings         import DRY_RUN, VERBOSE, SEND_DELAY_SECONDS
from modules.sheets          import get_companies, update_status
from modules.email_parser    import parse_email
from modules.searcher        import search_company
from modules.email_generator import generate_email
from modules.gmail_sender    import send_email


# ── per-company pipeline ──────────────────────────────────────────────────────

def process_company(company: dict) -> bool:
    """Full pipeline for one company. Returns True on success."""
    row   = company["row_index"]
    name  = company["company_name"]
    email = company["email"]

    log.info(f"\n[Row {row}] {name}  <{email}>")

    # 1. Parse recipient
    parsed = parse_email(email)
    log.info(f"  Recipient  -> {parsed['recipient_type']} / {parsed['recipient_name']}")

    # 2. Search company
    log.info(f"  Searching  -> {name} ...")
    summary = search_company(name)
    if summary:
        log.info(f"  Summary    -> {summary[:120]}...")
    else:
        log.info("  Summary    -> no results, using generic fallback")

    # 3. Generate email
    log.info("  Generating -> GPT-4o-mini ...")
    data = generate_email(
        company_name    = name,
        recipient_name  = parsed["recipient_name"],
        recipient_type  = parsed["recipient_type"],
        company_summary = summary,
    )

    if VERBOSE:
        log.info(f"  Subject    -> {data['subject']}")
        log.info(f"  Preview    -> {data['body'][:200]}...")

    # 4. Send (or dry-run)
    if DRY_RUN:
        log.info("  [DRY RUN]  -> skipping actual send")
        update_status(row, "Dry-Run")
        return True

    success = send_email(to=email, subject=data["subject"], body=data["body"])

    # 5. Update sheet
    update_status(row, "Sent" if success else "Failed")
    return success


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("  COLD MAIL AGENT — START")
    log.info(f"  DRY_RUN = {DRY_RUN}  |  log -> {_log_file}")
    log.info("=" * 60)

    companies = get_companies()
    total     = len(companies)
    log.info(f"\n  Companies to process: {total}\n")

    if not total:
        log.info("  Nothing to do. Exiting.")
        return

    sent, failed = 0, 0

    for idx, company in enumerate(companies, 1):
        log.info(f"-- {idx}/{total} {'-' * 45}")
        try:
            ok = process_company(company)
            if ok:
                sent   += 1
            else:
                failed += 1

        except Exception as e:
            log.error(f"  [ERROR] {company['company_name']}: {e}")
            log.debug(traceback.format_exc())
            failed += 1
            try:
                update_status(company["row_index"], "Failed")
            except Exception:
                pass

        if idx < total:
            log.info(f"  Waiting {SEND_DELAY_SECONDS}s before next ...\n")
            time.sleep(SEND_DELAY_SECONDS)

    log.info("\n" + "=" * 60)
    log.info(f"  [SENT]   Sent   : {sent}")
    log.info(f"  [FAILED] Failed : {failed}")
    log.info(f"  [LOG]    Log    : {_log_file}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()