"""
modules/searcher.py
DuckDuckGo search — no API key required.
Returns a plain-text company summary for the LLM prompt.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ddgs import DDGS
from config.settings import DDG_MAX_RESULTS


def search_company(company_name: str) -> str:
    """
    Returns up to ~800 chars of company description.
    Returns empty string on any failure.
    """
    query = f"{company_name} company AI ML data science mission products"
    try:
        with DDGS() as ddg:
            results = list(ddg.text(query, max_results=DDG_MAX_RESULTS))

        snippets = [r.get("body", "").strip() for r in results if r.get("body")]
        combined = " ".join(snippets)
        return combined[:800].rsplit(" ", 1)[0]

    except Exception as e:
        print(f"  [SEARCH WARN] '{company_name}': {e}")
        return ""


if __name__ == "__main__":
    import time
    for c in ["Sarvam AI", "Yellow.ai", "Fractal Analytics"]:
        print(f"\n=== {c} ===\n{search_company(c)}")
        time.sleep(1)