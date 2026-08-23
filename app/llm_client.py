"""
Chirper — LLM client wrapper.

Uses **Groq** as the primary inference provider.  When ECHO_CHAMBER_MOCK=1 is
set, returns deterministic canned responses so the full pipeline can be tested
without burning API credits.
"""

import os
import hashlib
from typing import Optional

# ── Mock responses keyed by ideology hints in the system prompt ──────────────

_MOCK_BANK = {
    "conspiracy": [
        "Wake up people! This is CLEARLY a cover-up. Follow the money. 👁️",
        "My insider source just confirmed this. They don't want you to see it.",
        "Funny how the 'fact-checkers' are silent on this one… do your own research.",
    ],
    "activist": [
        "This is absolutely UNACCEPTABLE!! We MUST demand accountability NOW! ✊",
        "How can people stay SILENT about this?! Silence is COMPLICITY!",
        "WE WILL NOT BE SILENCED. Share this. Amplify this. ACT. 🔥",
    ],
    "corporate": [
        "Let's look at the data before jumping to conclusions. The full picture is more nuanced.",
        "Actually, if you read the full report, you'll see this is taken out of context.",
        "Industry experts have already addressed this. Markets remain stable.",
    ],
    "contrarian": [
        "Interesting take, but have you considered that the exact opposite might be true?",
        "Everyone's agreeing a little too fast on this one. That's usually a red flag.",
        "You're all proving my point. This take is embarrassingly one-dimensional.",
    ],
    "engagement": [
        "🔥 BREAKING 🔥 You won't BELIEVE what's actually going on… wait for it… 👀",
        "THIS. CHANGES. EVERYTHING. RT if you agree, ignore if you don't care 💯",
        "They tried to HIDE this but it's going VIRAL… 🚨🚨🚨",
    ],
    "anxious": [
        "wait is this real?? idk this is lowkey terrifying 😰",
        "okay can someone explain what's happening because I'm genuinely scared rn",
        "should I be worried about this?? idk what to think anymore…",
    ],
}

_MOCK_FALLBACK = "This is a mock response from Chirper. [MOCK MODE]"

_IDEOLOGY_KEYWORDS = {
    "conspiracy": ["conspiracy", "cover-up", "hidden", "elites", "insiders"],
    "activist": ["justice", "activist", "outrage", "oppressed", "silence"],
    "corporate": ["corporate", "market", "institution", "data", "report"],
    "contrarian": ["contrarian", "opposite", "disagree", "devil"],
    "engagement": ["engagement", "viral", "sensationalize", "clickbait"],
    "anxious": ["anxious", "impressionable", "worried", "scared", "nervous"],
}


def _detect_ideology(system_prompt: str) -> str:
    """Guess which ideology a system prompt belongs to based on keywords."""
    prompt_lower = system_prompt.lower()
    best, best_score = "fallback", 0
    for ideology, keywords in _IDEOLOGY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > best_score:
            best, best_score = ideology, score
    return best


def _pick_mock(system_prompt: str, user_prompt: str) -> str:
    """Return a deterministic-ish mock response based on prompt content."""
    ideology = _detect_ideology(system_prompt)
    bank = _MOCK_BANK.get(ideology)
    if not bank:
        return _MOCK_FALLBACK
    # Deterministic pick based on user_prompt hash so re-runs are stable
    idx = int(hashlib.md5(user_prompt.encode()).hexdigest(), 16) % len(bank)
    return bank[idx]


import re

# ── Public API ───────────────────────────────────────────────────────────────

_DEFAULT_MODEL = "qwen/qwen3.6-27b"


def generate(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 300,
    model: Optional[str] = None,
) -> str:
    """
    Generate a short in-character reply.

    When ECHO_CHAMBER_MOCK=1 is set, returns a canned mock response.
    Otherwise calls the Groq API.
    """
    mock_mode = os.getenv("ECHO_CHAMBER_MOCK", "0") == "1"

    if mock_mode:
        return _pick_mock(system_prompt, user_prompt)

    # ── Real Groq call ───────────────────────────────────────────────────
    from groq import Groq  # lazy import to avoid load-time errors when mocking

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Set it in .env or export it, "
            "or use ECHO_CHAMBER_MOCK=1 for testing."
        )

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model or _DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.9,
    )
    raw_content = response.choices[0].message.content or ""
    
    # Strip <think>...</think> blocks if present (from reasoning models like Qwen)
    cleaned_content = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL)
    return cleaned_content.strip()
