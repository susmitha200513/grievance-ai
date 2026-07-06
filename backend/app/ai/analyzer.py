"""
The heart of the project: given a raw citizen complaint, ask an LLM (via LangChain)
to return structured JSON with category, responsible department, priority,
a short summary, and sentiment.

If no GOOGLE_API_KEY is configured, falls back to a simple keyword-based
analyzer so the app still runs end-to-end for local testing/demo without a key.
"""
import json
import re
from typing import Optional

from app.config import settings

_ANALYZER_PROMPT = """You are an AI assistant for a municipal grievance system.
Given a citizen's complaint, analyze it and respond with ONLY a JSON object
(no markdown, no extra text) with these exact keys:

{{
  "category": "<short category like 'Road Safety', 'Sanitation', 'Electrical', 'Water Supply', 'Corruption', 'Other'>",
  "department": "<responsible department, e.g. 'Public Works', 'Sanitation Department', 'Electricity Board', 'Water Board', 'Vigilance Cell'>",
  "priority": "<one of: critical, high, medium, low>",
  "summary": "<one sentence, under 20 words, professional summary of the issue>",
  "sentiment": "<one of: negative, neutral, positive>"
}}

Guidance for priority:
- "critical": immediate danger to life (structural collapse, live wires, major pipeline burst)
- "high": safety risk near schools/hospitals/main roads, or many people affected
- "medium": inconvenience without immediate danger
- "low": minor/cosmetic issues

Complaint type hint: {complaint_type}
Location/area: {area}

Complaint text:
\"\"\"{text}\"\"\"
"""


def _rule_based_fallback(text: str, complaint_type: str, area: Optional[str]) -> dict:
    """Simple keyword-based fallback so the demo works even without an API key."""
    t = text.lower()
    type_map = {
        "road": ("Road Safety", "Public Works"),
        "street_light": ("Public Safety", "Electricity Department"),
        "illegal_dumping": ("Sanitation", "Sanitation Department"),
        "corruption": ("Corruption", "Vigilance Cell"),
        "water_leakage": ("Water Supply", "Water Board"),
    }
    category, department = type_map.get(complaint_type, ("General", "General Administration"))

    priority = "medium"
    if any(k in t for k in ["collapse", "burst", "live wire", "fire", "accident", "died", "death"]):
        priority = "critical"
    elif any(k in t for k in ["school", "hospital", "main road", "children"]):
        priority = "high"
    elif any(k in t for k in ["minor", "small", "cosmetic"]):
        priority = "low"

    sentiment = "neutral"
    if any(k in t for k in ["nobody", "months", "still not", "worst", "terrible", "unsafe", "danger"]):
        sentiment = "negative"

    summary = re.sub(r"\s+", " ", text.strip())
    summary = (summary[:100] + "...") if len(summary) > 100 else summary

    return {
        "category": category,
        "department": department,
        "priority": priority,
        "summary": summary,
        "sentiment": sentiment,
    }


def analyze_complaint(text: str, complaint_type: str, area: Optional[str] = None) -> dict:
    if not settings.GOOGLE_API_KEY:
        return _rule_based_fallback(text, complaint_type, area)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        prompt = _ANALYZER_PROMPT.format(
            complaint_type=complaint_type, area=area or "unknown", text=text
        )
        response = llm.invoke(prompt)
        raw = response.content.strip()
        raw = re.sub(r"^```json|```$", "", raw, flags=re.MULTILINE).strip()
        data = json.loads(raw)

        required = {"category", "department", "priority", "summary", "sentiment"}
        if not required.issubset(data.keys()):
            raise ValueError("Missing keys in LLM response")
        return data
    except Exception:
        # Never let an LLM hiccup break complaint registration during a demo
        return _rule_based_fallback(text, complaint_type, area)
