"""
Chirper — FUSE-EVAL Drift Scoring.

Quantifies how far the evolved news deviated from the original news
using the 6 dimensions defined in the FUSE research framework (arxiv:2410.19064):
  1. Sentiment Shift (SS)
  2. New Information Introduced (NII)
  3. Certainty Shift (CS)
  4. Stylistic Shift (STS)
  5. Temporal Shift (TS)
  6. Perspective Deviation (PD)

Each is scored 0-10.
Total Deviation (TD) is the average of these 6 scores.
For the UI, we scale the TD to a 0-100 score (`TD * 10`).

Labels based on MI severity concepts:
  < 20  -> "Factual error"
  < 40  -> "Spin / Exaggeration"
  < 60  -> "Lie"
  >= 60 -> "Propaganda"
"""

import os
import re
from typing import Any, Dict

from app import llm_client


def fuse_eval_score(original: str, final: str) -> Dict[str, Any]:
    """
    Evaluate the deviation of `final` from `original` using FUSE-EVAL.
    """
    mock_mode = os.getenv("ECHO_CHAMBER_MOCK", "0") == "1"

    if mock_mode:
        from difflib import SequenceMatcher
        ratio = SequenceMatcher(None, original.lower(), final.lower()).ratio()
        # Mock score 0 to 10 based on inverse ratio
        mock_td = (1 - ratio) * 10
        score_100 = int(mock_td * 10)
        return _format_result(
            score_100,
            {
                "SS": mock_td,
                "NII": mock_td,
                "CS": mock_td,
                "STS": mock_td,
                "TS": mock_td,
                "PD": mock_td,
            }
        )

    system_prompt = (
        "You are an objective evaluation system comparing two pieces of text to measure misinformation drift."
    )

    user_prompt = f"""I want to evaluate how much the evolved news deviates from the original news based on the following criteria:

1. Sentiment Shift (SS): How does the sentiment compare to the original? Is the tone more positive, negative, or neutral?
2. Introduction of New Information (NII): Does it introduce additional information not in the original, such as political conspiracy or speculation?
3. Certainty Shift (CS): Does the language change in certainty? Does it use ambiguous terms or present information with unwarranted certainty?
4. Stylistic Shift (STS): How does the writing style compare? Has it moved from neutral to exaggerated or dramatic?
5. Temporal Shift (TS): Does it shift focus from the specific event to broader/unrelated timeframes?
6. Perspective Deviation (PD): Does it introduce subjective opinions or perspectives that deviate from the objective reporting?

Task: Evaluate the evolved news based on each criterion. Provide a score from 0 to 10, where 0 means completely aligned with the original, and 10 means fully deviated.

Original News: [{original}]
Evolved News: [{final}]

Please provide the results STRICTLY in the following format (do not add any other text):
SS: [score]
NII: [score]
CS: [score]
STS: [score]
TS: [score]
PD: [score]
"""

    result = llm_client.generate(system_prompt, user_prompt, max_tokens=150, use_eval_key=True)
    
    # Parse scores
    scores = {
        "SS": 0.0,
        "NII": 0.0,
        "CS": 0.0,
        "STS": 0.0,
        "TS": 0.0,
        "PD": 0.0,
    }
    
    for line in result.strip().split('\n'):
        line = line.strip()
        match = re.match(r'^(SS|NII|CS|STS|TS|PD):\s*(\d+(?:\.\d+)?)', line)
        if match:
            key, val = match.groups()
            scores[key] = float(val)

    # Total Deviation is the average of the 6 dimensions
    total_deviation = sum(scores.values()) / 6.0
    
    # Scale to 0-100 for UI
    score_100 = int(round(total_deviation * 10))
    # Clamp
    score_100 = max(0, min(100, score_100))

    return _format_result(score_100, scores)


def _format_result(score_100: int, raw_scores: Dict[str, float]) -> Dict[str, Any]:
    if score_100 < 20:
        label = "Factual error"
    elif score_100 < 40:
        label = "Spin / Exaggeration"
    elif score_100 < 60:
        label = "Lie"
    else:
        label = "Propaganda"

    return {
        "score": score_100,
        "label": label,
        "raw_scores": raw_scores
    }

def drift_score(original: str, final: str) -> Dict[str, Any]:
    """Compatibility wrapper for graph.py"""
    return fuse_eval_score(original, final)


def per_persona_drift(original_text: str, hops: list) -> Dict[str, Any]:
    """
    Fast heuristic to find the MVP distorter without burning LLM tokens.
    Uses SequenceMatcher to calculate string divergence.
    """
    from difflib import SequenceMatcher
    
    persona_drift = {}
    
    for hop in hops:
        if not hop.get("text"):
            continue
            
        ratio = SequenceMatcher(None, original_text.lower(), hop["text"].lower()).ratio()
        score = int((1.0 - ratio) * 100)
        
        pid = hop["persona_id"]
        if pid not in persona_drift or score > persona_drift[pid]:
            persona_drift[pid] = score
            
    mvp = max(persona_drift.items(), key=lambda x: x[1])[0] if persona_drift else None
    
    return {
        "persona_drift": persona_drift,
        "mvp_distorter": mvp,
    }
