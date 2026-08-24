"""
Chirper — Drift scoring.

Quantifies how far final_text drifted from original_text using:
  1. Embedding cosine distance (reuses memory._embed)
  2. LLM-rated tone shift (1-5 scale via Groq, or deterministic in mock mode)

Drift Score Formula:
  score = (embedding_distance * 60) + (tone_shift_normalized * 40)
  where tone_shift_normalized = (tone_shift - 1) / 4   [maps 1-5 → 0.0-1.0]
  Final score clamped to 0-100.

Labels:
  < 20  → "Barely changed"
  < 40  → "Slightly spun"
  < 60  → "Noticeably spun"
  < 80  → "Heavily distorted"
  >= 80 → "Completely warped"
"""

import os
from difflib import SequenceMatcher
from typing import Any, Dict, List

import numpy as np

from app.memory import _embed


# ── Core functions ───────────────────────────────────────────────────────────


def embedding_distance(text_a: str, text_b: str) -> float:
    """
    Cosine distance between two texts' embeddings.

    Returns a value in [0, 1] where 0 = identical, 1 = completely different.
    Uses the same _embed() function as Pinecone memory.
    """
    vec_a = np.array(_embed(text_a))
    vec_b = np.array(_embed(text_b))
    cos_sim = float(np.dot(vec_a, vec_b))
    # Clamp to valid range (floating point rounding)
    cos_sim = max(-1.0, min(1.0, cos_sim))
    return 1.0 - cos_sim


def tone_shift_score(original: str, final: str) -> int:
    """
    Rate the emotional tone / factual framing shift between two texts.

    Returns an integer 1-5:
      1 = nearly identical tone/framing
      5 = completely different tone/framing

    In mock mode: uses a deterministic heuristic based on string similarity.
    In live mode: uses a lightweight Groq call.
    """
    mock_mode = os.getenv("ECHO_CHAMBER_MOCK", "0") == "1"

    if mock_mode:
        # Deterministic heuristic: use SequenceMatcher ratio
        ratio = SequenceMatcher(None, original.lower(), final.lower()).ratio()
        # ratio 1.0 = identical → score 1, ratio 0.0 = totally different → score 5
        score = int(round(1 + (1 - ratio) * 4))
        return max(1, min(5, score))

    # Live mode: ask Groq to rate the shift
    from app import llm_client

    prompt = (
        "You are a text analysis tool in a video game. Compare these two texts "
        "and rate how much the emotional tone and factual framing changed.\n\n"
        f"Text A: \"{original[:500]}\"\n"
        f"Text B: \"{final[:500]}\"\n\n"
        "Scale: 1 (nearly identical tone/framing) to 5 (completely different "
        "tone/framing). Output ONLY the number, nothing else."
    )
    result = llm_client.generate(
        "You are a neutral text analysis tool. Output only a single digit 1-5.",
        prompt,
        max_tokens=5,
    )
    # Parse the number from the response
    for ch in result.strip():
        if ch.isdigit() and 1 <= int(ch) <= 5:
            return int(ch)
    return 3  # fallback if parsing fails


def drift_score(original: str, final: str) -> Dict[str, Any]:
    """
    Compute a composite drift score (0-100) with a human-readable label.

    Formula:
      score = (embedding_distance * 60) + (tone_shift_normalized * 40)
      tone_shift_normalized = (tone_shift - 1) / 4  [maps 1-5 to 0.0-1.0]
    """
    emb_dist = embedding_distance(original, final)
    tone = tone_shift_score(original, final)
    tone_norm = (tone - 1) / 4.0  # 1→0.0, 5→1.0

    raw_score = (emb_dist * 60) + (tone_norm * 40)
    score = max(0, min(100, round(raw_score)))

    if score < 20:
        label = "Barely changed"
    elif score < 40:
        label = "Slightly spun"
    elif score < 60:
        label = "Noticeably spun"
    elif score < 80:
        label = "Heavily distorted"
    else:
        label = "Completely warped"

    return {
        "score": score,
        "label": label,
        "embedding_distance": round(emb_dist, 4),
        "tone_shift": tone,
    }


def per_persona_drift(original_text: str, hops: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute per-persona drift contribution from reposts.

    For each repost, measures the embedding distance between the text
    *before* that repost and *after* it. Returns the persona who caused
    the biggest single-hop drift jump (the "MVP distorter").

    Hop dict shape (from graph.py):
      {"hop": int, "persona_id": str, "persona_name": str, "action": str, "text": str}
    """
    persona_max_drift: Dict[str, float] = {}
    # Track the running text through reposts
    running_text = original_text

    for h in hops:
        if h["action"] == "repost" and h.get("text"):
            before = running_text
            after = h["text"]
            dist = embedding_distance(before, after)

            pid = h["persona_id"]
            if pid not in persona_max_drift or dist > persona_max_drift[pid]:
                persona_max_drift[pid] = round(dist, 4)

            # Reposts update the running text (drift compounds)
            running_text = after

    if not persona_max_drift:
        return {"mvp_distorter": None, "persona_drift": {}}

    mvp = max(persona_max_drift, key=persona_max_drift.get)
    return {
        "mvp_distorter": mvp,
        "persona_drift": persona_max_drift,
    }
