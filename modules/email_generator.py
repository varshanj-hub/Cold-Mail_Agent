"""
modules/email_generator.py
Generates a personalised cold email.
Fixed subject and body template; LLM fills only two company-specific placeholders.
Returns { subject: str, body: str }.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config.settings import (
    OPENAI_API_KEY, LLM_MODEL,
    YOUR_NAME, YOUR_PHONE, YOUR_LINKEDIN,
    YOUR_GITHUB, SENDER_EMAIL, YOUR_LOCATION,
)

_client = OpenAI(api_key=OPENAI_API_KEY)

_SUBJECT = "Application – AI/ML Engineer | RAG, LLMs & Agentic AI Experience"

_BODY_TEMPLATE = (
    "I am {name}, an AI Engineer with experience building production-grade Generative AI, RAG, and Agentic AI solutions. "
    "I am currently exploring opportunities in AI/ML Engineering, and Data Science.\n\n"
    "{company_name}'s focus on {company_objective} aligns closely with my experience developing scalable AI systems "
    "that transform large-scale data into actionable insights. "
    "I am particularly excited about the opportunity to contribute to {specific_area}.\n\n"
    "Some highlights of my experience include:\n"
    "• Built a production RAG platform to analyze and retrieve insights from 3.7M+ IT incident records using PySpark, "
    "semantic chunking, vector embeddings, and PostgreSQL pgvector, achieving an 80% retrieval hit rate with 2.15ms latency.\n"
    "• Designed an intelligent LLM routing framework that dynamically selected models based on query complexity, "
    "reducing inference costs by 64% while maintaining response quality.\n"
    "• Evaluated multiple vector databases and embedding models at enterprise scale, "
    "identifying the optimal architecture for high-performance retrieval and knowledge discovery.\n\n"
    "I have attached my resume for your review and would welcome the opportunity to discuss "
    "how my experience can contribute to {company_name}'s initiatives.\n\n"
    "Thank you for your time and consideration."
)

_FILL_SYSTEM = """\
You fill two company-specific placeholders for a cold email from an AI Engineer.

Given company info, return ONLY valid JSON with exactly these two fields:
- "company_objective": A concise phrase (5–10 words) describing the company's core focus or mission. Must fit naturally after "focus on ".
- "specific_area": A concise phrase (5–12 words) describing the most relevant area where an AI/ML engineer could contribute. Must fit naturally after "contribute to ".

Return ONLY valid JSON, no markdown, no explanation:
{"company_objective": "...", "specific_area": "..."}"""


def _signature() -> str:
    return (
        f"Best regards,\n\n"
        f"{YOUR_NAME}\n"
        f"Phone    : {YOUR_PHONE}\n"
        f"Email    : {SENDER_EMAIL}\n"
        f"LinkedIn : {YOUR_LINKEDIN}\n"
        f"GitHub   : {YOUR_GITHUB}\n"
        f"Location : {YOUR_LOCATION}"
    )


def _greeting(recipient_name: str) -> str:
    return f"Dear {recipient_name},"


def generate_email(
    company_name: str,
    recipient_name: str,
    recipient_type: str,  # noqa: kept for API compatibility
    company_summary: str,
) -> dict:
    """Calls LLM to fill company-specific placeholders, returns { subject, body }."""
    summary_block = (
        f"Company: {company_name}\nInfo: {company_summary}"
        if company_summary
        else f"Company: {company_name} (no additional info available)"
    )

    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": _FILL_SYSTEM},
            {"role": "user",   "content": summary_block},
        ],
        temperature=0.5,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)
    body_content = _BODY_TEMPLATE.format(
        name=YOUR_NAME,
        company_name=company_name,
        company_objective=data["company_objective"],
        specific_area=data["specific_area"],
    )

    greeting = _greeting(recipient_name)
    body = f"{greeting}\n\n{body_content}\n\n{_signature()}"
    return {"subject": _SUBJECT, "body": body}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    result = generate_email(
        company_name    = "Sarvam AI",
        recipient_name  = "Hiring Team",
        recipient_type  = "careers",
        company_summary = (
            "Sarvam AI is an Indian AI company building a full-stack sovereign AI platform "
            "with speech-to-text, text-to-speech, translation, and conversational agents "
            "across 22 Indian languages."
        ),
    )
    print("=== SUBJECT ===")
    print(result["subject"])
    print("\n=== BODY ===")
    print(result["body"])
