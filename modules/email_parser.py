"""
modules/email_parser.py
Parses an email address to determine:
  - recipient_type : 'careers' | 'hr' | 'hiring' | 'person' | 'generic'
  - recipient_name : greeting name  e.g. "Mahalaxmi" or "Hiring Team"
  - first_name     : short name for subject personalisation
"""

import re, sys
sys.stdout.reconfigure(encoding='utf-8')


def _split_camel(s: str) -> list[str]:
    """Split camelCase or PascalCase string into words. e.g. johnVarshan -> ['john', 'Varshan']"""
    return [p for p in re.sub(r'([a-z])([A-Z])', r'\1 \2', s).split() if p]

_TYPE_MAP = {
    "careers":       "careers",
    "career":        "careers",
    "resumes":       "careers",
    "resume":        "careers",
    "hr":            "hr",
    "humanresource": "hr",
    "hiring":        "hiring",
    "recruit":       "hiring",
    "recruitment":   "hiring",
    "talent":        "hiring",
    "jobs":          "hiring",
    "job":           "hiring",
    "apply":         "hiring",
    "future":        "hiring",
    "hello":         "generic",
    "info":          "generic",
    "contact":       "generic",
    "support":       "generic",
    "team":          "generic",
    "tateam":        "generic",
}

_GREETING_MAP = {
    "careers": "Hiring Team",
    "hr":      "HR Team",
    "hiring":  "Hiring Team",
    "generic": "Team",
}


def _title(s: str) -> str:
    return " ".join(w.capitalize() for w in s.split())


def parse_email(email: str) -> dict:
    """
    Returns:
      { recipient_type, recipient_name, first_name }
    """
    local = email.split("@")[0].lower()

    # --- keyword match ---
    for keyword, rtype in _TYPE_MAP.items():
        if local == keyword or local.startswith(keyword):
            greeting = _GREETING_MAP.get(rtype, "Team")
            return {
                "recipient_type": rtype,
                "recipient_name": greeting,
                "first_name":     greeting.split()[0],
            }

    # --- personal name: split on . _ - digits first ---
    parts = [p for p in re.split(r"[.\-_\d]+", local) if len(p) > 1]
    if parts:
        # If still a single long chunk, try camelCase on the original-case local part
        if len(parts) == 1:
            original_local = email.split("@")[0]
            camel = _split_camel(original_local)
            if len(camel) > 1:
                parts = [p.lower() for p in camel]
        first = _title(parts[0])
        return {
            "recipient_type": "person",
            "recipient_name": first,
            "first_name":     first,
        }

    # --- fallback ---
    return {
        "recipient_type": "generic",
        "recipient_name": "Team",
        "first_name":     "Team",
    }


if __name__ == "__main__":
    tests = [
        "careers@example.com",
        "hr@example.com",
        "hiring@example.com",
        "jobs@example.com",
        "talent@example.com",
        "firstname.lastname@example.com",
        "john@example.com",
        "team@example.com",
        "hello@example.com",
        "contact@example.com",
    ]
    for t in tests:
        print(f"{t:45s}  ->  {parse_email(t)}")