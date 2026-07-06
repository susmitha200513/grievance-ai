"""
Smart Complaint Score = weighted combination of:
  - Severity (from AI priority)          40%
  - Location importance (near school/hospital/main road) 30%
  - Number of similar reports (support_count) 20%
  - Sentiment (negative sentiment raises urgency) 10%

Returns a score 0-100.
"""
from typing import Optional

PRIORITY_SEVERITY = {
    "critical": 100,
    "high": 75,
    "medium": 45,
    "low": 20,
}

SENTIMENT_SCORE = {
    "negative": 100,
    "neutral": 50,
    "positive": 20,
}


def location_importance(text: str, area: Optional[str]) -> float:
    t = (text + " " + (area or "")).lower()
    score = 30  # baseline
    if "school" in t:
        score += 30
    if "hospital" in t:
        score += 30
    if "main road" in t or "highway" in t:
        score += 20
    return min(score, 100)


def support_score(support_count: int) -> float:
    # diminishing returns: 1 report -> 20, 5 -> ~70, 10+ -> 100
    return min(20 + (support_count - 1) * 12, 100)


def compute_score(priority: str, text: str, area: Optional[str], support_count: int, sentiment: str) -> float:
    severity = PRIORITY_SEVERITY.get(priority, 45)
    location = location_importance(text, area)
    reports = support_score(support_count)
    sentiment_val = SENTIMENT_SCORE.get(sentiment, 50)

    total = (
        severity * 0.40
        + location * 0.30
        + reports * 0.20
        + sentiment_val * 0.10
    )
    return round(total, 1)
