# Cold Mail Agent

> Automated cold outreach pipeline — reads a target list from Google Sheets, researches each company, generates a personalised email via GPT-4o-mini, sends it through Gmail with your resume attached, and logs the result back to the sheet.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)
![Gmail API](https://img.shields.io/badge/Gmail-API-EA4335?logo=gmail&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Google_Sheets-API-34A853?logo=googlesheets&logoColor=white)

---

## Table of Contents

- [Overview](#overview)
- [Pipeline](#pipeline)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
  - [1. Install dependencies](#1-install-dependencies)
  - [2. Configure environment](#2-configure-environment)
  - [3. Google Sheets — service account](#3-google-sheets--service-account)
  - [4. Gmail — one-time OAuth](#4-gmail--one-time-oauth)
  - [5. Add your resume](#5-add-your-resume)
  - [6. Prepare the sheet](#6-prepare-the-sheet)
- [Usage](#usage)
- [Email Format](#email-format)
- [Configuration Reference](#configuration-reference)
- [Module Reference](#module-reference)
- [Security](#security)

---

## Overview

Cold Mail Agent eliminates manual outreach by automating every step of the cold email workflow:

1. **Reads** a Google Sheet with company names and contact emails
2. **Parses** each address to infer the right greeting (`Hiring Team`, `HR Team`, or a person's first name)
3. **Researches** the company via DuckDuckGo (no API key required)
4. **Generates** a personalised email — fixed structure, LLM fills only the two company-specific phrases
5. **Sends** an HTML-formatted email with your resume PDF attached via Gmail API
6. **Updates** the sheet with `Sent` / `Failed` status and a timestamp
7. **Logs** every run to a timestamped file in `logs/`

Rows already marked `Sent` are automatically skipped on re-runs, making it safe to run multiple times.

---

## Pipeline

```
┌─────────────────┐
│  Google Sheets  │  Company name + email
└────────┬────────┘
         │  sheets.get_companies()
         ▼
┌─────────────────┐
│  Email Parser   │  Classify address → careers / hr / hiring / person / generic
└────────┬────────┘
         │  email_parser.parse_email()
         ▼
┌─────────────────┐
│   DuckDuckGo    │  Company research → plain-text summary (~800 chars)
└────────┬────────┘
         │  searcher.search_company()
         ▼
┌─────────────────┐
│  GPT-4o-mini    │  Fill two placeholders: company_objective + specific_area
└────────┬────────┘
         │  email_generator.generate_email()
         ▼
┌─────────────────┐
│   Gmail API     │  Send HTML email + resume PDF attachment
└────────┬────────┘
         │  gmail_sender.send_email()
         ▼
┌─────────────────┐
│  Google Sheets  │  Write status ("Sent" / "Failed") + timestamp
└─────────────────┘
```

---

## Project Structure

```
Cold_Mail_App/
│
├── agent.py                    # Orchestrator — runs the full pipeline
│
├── config/
│   ├── settings.py             # Loads & validates all env vars
│   ├── credentials.json        # Gmail OAuth client secret        ← gitignored
│   ├── token.json              # Gmail OAuth token (auto-generated) ← gitignored
│   ├── service_account.json    # Google Sheets service account key ← gitignored
│   └── Your_Resume.pdf         # Resume attached to every email    ← gitignored
│
├── modules/
│   ├── sheets.py               # Google Sheets read / write
│   ├── email_parser.py         # Address → recipient type + greeting
│   ├── searcher.py             # DuckDuckGo company research
│   ├── email_generator.py      # LLM email generation
│   └── gmail_sender.py         # Gmail API send + PDF attachment
│
├── logs/                       # Per-run timestamped log files     ← gitignored
│
├── .env                        # Secrets — never commit             ← gitignored
├── .env.example                # Template — copy and fill in
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Google Cloud project | Free tier sufficient |
| Gmail account | Must be the sender address |
| OpenAI account | API key with GPT-4o-mini access |

---

## Setup

### 1. Install dependencies

```bash
git clone <repo-url>
cd Cold_Mail_App

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in every value. See [Configuration Reference](#configuration-reference) for all variables.

### 3. Google Sheets — service account

The agent uses a **service account** to read and write your sheet without requiring user interaction.

1. Open [Google Cloud Console](https://console.cloud.google.com) → **APIs & Services** → **Library** → enable **Google Sheets API**
2. Navigate to **IAM & Admin** → **Service Accounts** → **Create Service Account**
3. Download the JSON key → save as `config/service_account.json`
4. Copy the service account email (e.g. `name@project.iam.gserviceaccount.com`)
5. Open your Google Sheet → **Share** → paste the service account email → set role to **Editor**

Update `.env`:

```env
SHEET_ID=<id from your sheet URL — the long alphanumeric string>
GOOGLE_SERVICE_ACCOUNT_EMAIL=name@project.iam.gserviceaccount.com
GOOGLE_PROJECT_ID=your-gcp-project-id
```

### 4. Gmail — one-time OAuth

The agent sends from your personal Gmail using OAuth 2.0.

1. In Google Cloud Console → **APIs & Services** → **Library** → enable **Gmail API**
2. Go to **Credentials** → **Create Credentials** → **OAuth client ID** → select **Desktop app**
3. Download the JSON → save as `config/credentials.json`
4. Run the one-time authorisation:

```bash
python modules/gmail_sender.py --auth
```

A browser window opens. Log in and grant Gmail send permission. The token is saved to `config/token.json` — all subsequent runs are fully headless.

### 5. Add your resume

Place your resume PDF at the path specified by `RESUME_PATH` in `.env` (default: `config/Your_Resume.pdf`). It is automatically attached to every outgoing email.

### 6. Prepare the sheet

The sheet must follow this column structure starting from row 2 (configurable via `DATA_START_ROW`):

| Column A | Column B | Column C | Column D |
|---|---|---|---|
| Company Name | Contact Email | Status *(agent writes)* | Sent At *(agent writes)* |
| Sarvam AI | careers@sarvam.ai | | |
| Fractal Analytics | hr@fractal.ai | | |

> Rows where **Column C = `Sent`** are automatically skipped on re-runs.

---

## Usage

```bash
# Send real emails
python agent.py

# Dry run — full pipeline, no emails sent, sheet gets "Dry-Run" status
DRY_RUN=True python agent.py
```

Each run produces a log file at `logs/agent_YYYYMMDD_HHMMSS.log` with per-company status, subject line, and body preview.

**Sample run output:**

```
============================================================
  COLD MAIL AGENT — START
  DRY_RUN = False  |  log -> logs/agent_20260531_120000.log
============================================================

  Companies to process: 3

-- 1/3 ---------------------------------------------
[Row 2] Sarvam AI  <careers@sarvam.ai>
  Recipient  -> careers / Hiring Team
  Searching  -> Sarvam AI ...
  Summary    -> Sarvam AI is an Indian AI company building a full-stack ...
  Generating -> GPT-4o-mini ...
  Subject    -> Application – AI/ML Engineer | RAG, LLMs & Agentic AI Experience
  [SENT]     -> careers@sarvam.ai
  Waiting 5s before next ...
```

---

## Email Format

The subject line and body structure are fixed. GPT-4o-mini fills **only two company-specific phrases** — keeping output consistent and reducing hallucination risk.

**Subject**
```
Application – AI/ML Engineer | RAG, LLMs & Agentic AI Experience
```

**Body**
```
Dear Hiring Team,

I am [YOUR_NAME], an AI Engineer with experience building production-grade
Generative AI, RAG, and Agentic AI solutions. I am currently exploring
opportunities in AI/ML Engineering, and Data Science.

[COMPANY]'s focus on [LLM: company objective] aligns closely with my experience
developing scalable AI systems that transform large-scale data into actionable
insights. I am particularly excited about the opportunity to contribute to
[LLM: specific area].

Some highlights of my experience include:
• Built a production RAG platform on 3.7M+ IT incident records (PySpark,
  pgvector) — 80% retrieval hit rate, 2.15ms latency.
• Designed an LLM routing framework — 64% inference cost reduction.
• Benchmarked 5 vector DBs and 3 embedding models at enterprise scale.

I have attached my resume and would welcome the opportunity to discuss how
my experience can contribute to [COMPANY]'s initiatives.

Thank you for your time and consideration.

Best regards,
[YOUR_NAME]
📧 [YOUR_EMAIL]  📱 [YOUR_PHONE]
🔗 LinkedIn  🔗 GitHub  📍 [YOUR_CITY]
```

---

## Configuration Reference

### Personal Details

| Variable | Required | Description |
|---|:---:|---|
| `YOUR_NAME` | ✅ | Full name used in email body and signature |
| `YOUR_PHONE` | ✅ | Phone number in signature |
| `YOUR_LINKEDIN` | ✅ | LinkedIn profile URL |
| `YOUR_GITHUB` | ✅ | GitHub profile URL |
| `YOUR_BIO` | ✅ | Short bio for LLM context |
| `YOUR_SKILLS` | ✅ | Comma-separated skill list |
| `YOUR_EDUCATION` | ✅ | Degree and institution |
| `YOUR_EXPERIENCE` | ✅ | Pipe-separated `|` experience entries |
| `YOUR_PROJECTS` | ✅ | Notable projects |

### Google Sheets

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `SHEET_ID` | ✅ | — | Sheet ID from the URL |
| `SHEET_NAME` | ❌ | `Sheet1` | Tab name |
| `GOOGLE_CREDENTIALS_FILE` | ❌ | `config/service_account.json` | Service account key path |
| `GOOGLE_SERVICE_ACCOUNT_EMAIL` | ❌ | — | Service account email |
| `GOOGLE_PROJECT_ID` | ❌ | — | GCP project ID |
| `DATA_START_ROW` | ❌ | `2` | First data row (skip header) |

### Gmail

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `SENDER_EMAIL` | ✅ | — | Your Gmail address |
| `GMAIL_CREDENTIALS_FILE` | ❌ | `config/credentials.json` | OAuth client secret path |
| `GMAIL_TOKEN_FILE` | ❌ | `config/token.json` | OAuth token path |
| `RESUME_PATH` | ❌ | `config/resume.pdf` | Resume PDF to attach |

### OpenAI

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `OPENAI_API_KEY` | ✅ | — | OpenAI secret key |
| `LLM_MODEL` | ❌ | `gpt-4o-mini` | Model for email generation |

### Agent Behaviour

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `DRY_RUN` | ❌ | `False` | Skip sending; write `Dry-Run` to sheet |
| `VERBOSE` | ❌ | `True` | Log subject + body preview per company |
| `SEND_DELAY_SECONDS` | ❌ | `5` | Delay between sends to avoid rate limits |
| `DDG_MAX_RESULTS` | ❌ | `5` | Max DuckDuckGo snippets per company |

---

## Module Reference

| Module | Responsibility |
|---|---|
| `agent.py` | Top-level orchestrator; iterates companies, handles errors, prints final summary |
| `config/settings.py` | Loads all env vars via `python-dotenv`; raises `EnvironmentError` on missing required vars |
| `modules/sheets.py` | Reads company list via Sheets API v4; batch-writes status + timestamp after each send |
| `modules/email_parser.py` | Classifies email local-parts (`careers`, `hr`, `hiring`, `person`, `generic`) and derives the correct greeting |
| `modules/searcher.py` | DuckDuckGo search with `ddgs`; returns up to 800 chars of company description; fails silently |
| `modules/email_generator.py` | Fixed subject + body template; one LLM call per company to fill `company_objective` and `specific_area` |
| `modules/gmail_sender.py` | Builds multipart MIME email (HTML body + PDF attachment); manages OAuth token refresh automatically |

---

## Security

> **Never commit secrets.** All sensitive files are covered by `.gitignore`.

| File | Why it must stay local |
|---|---|
| `.env` | Contains API keys and personal data |
| `config/credentials.json` | Gmail OAuth client secret |
| `config/token.json` | Live Gmail access token |
| `config/service_account.json` | Google Sheets write access |
| `config/*.pdf` | Your resume |

If your OpenAI API key is ever exposed, revoke it immediately at **platform.openai.com → API Keys**.
