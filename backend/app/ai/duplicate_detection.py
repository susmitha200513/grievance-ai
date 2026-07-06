"""
Detects whether a new complaint is likely a duplicate of an existing one:
same/similar area + same complaint_type + high text similarity.

Uses OpenAI embeddings + cosine similarity when an API key is set,
otherwise falls back to difflib sequence matching (no external calls).
"""
import json
import difflib
from typing import List, Optional

import numpy as np

from app.config import settings

SIMILARITY_THRESHOLD = 0.80


def get_embedding(text: str) -> Optional[List[float]]:
    if not settings.GOOGLE_API_KEY:
        return None
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        embedder = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004", google_api_key=settings.GOOGLE_API_KEY
        )
        return embedder.embed_query(text)
    except Exception:
        return None


def cosine_similarity(a: List[float], b: List[float]) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    denom = (np.linalg.norm(a_arr) * np.linalg.norm(b_arr))
    if denom == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / denom)


def text_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_duplicate(new_text: str, new_embedding: Optional[List[float]], candidates: list):
    """
    candidates: list of Complaint ORM objects already filtered by same
    complaint_type and (roughly) same area, from the caller.
    Returns (best_match_complaint, similarity_score) or (None, 0.0)
    """
    best_match = None
    best_score = 0.0

    for c in candidates:
        score = 0.0
        if new_embedding is not None and c.embedding:
            try:
                existing_vec = json.loads(c.embedding)
                score = cosine_similarity(new_embedding, existing_vec)
            except Exception:
                score = text_similarity(new_text, c.description)
        else:
            score = text_similarity(new_text, c.description)

        if score > best_score:
            best_score = score
            best_match = c

    threshold = SIMILARITY_THRESHOLD if new_embedding is not None else 0.55
    if best_match and best_score >= threshold:
        return best_match, best_score
    return None, 0.0
