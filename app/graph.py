"""
Chirper — LangGraph spread simulation.

Implements the core "misinformation telephone" loop:
  select_reactors → react → check_dm → advance → (loop or end)

Each hop picks 2-3 agents from the persona pool. Agents comment, argue,
or repost (with LLM-powered distortion). DMs are sent probabilistically
based on each persona's dm_trigger_threshold.

Cross-agent awareness: agents see what other personas recently said on
the thread and can reference them by @handle.
"""

import os
import random
import sys
import uuid
from typing import Annotated, Any, Dict, List, Literal, Optional

from langgraph.graph import END, StateGraph

from app import llm_client, memory
from app.personas import all_persona_ids, get_persona

# ── State schema (TypedDict for LangGraph) ───────────────────────────────────

import operator
from typing_extensions import TypedDict


def _last_write(_, b):
    """Reducer: last-write-wins."""
    return b


class SimState(TypedDict):
    post_id: str
    original_text: str
    current_text: str
    hop_count: int
    max_hops: int
    persona_pool: Annotated[list, _last_write]
    selected: Annotated[list, _last_write]
    hops: Annotated[list, operator.add]      # append new hops
    dms: Annotated[list, operator.add]        # append new dms


# ── Helpers ──────────────────────────────────────────────────────────────────

_REPOST_HEAVY_THRESHOLD = 0.35


def _weighted_choice(weights: Dict[str, float]) -> str:
    """Pick an action from a {action: weight} dict."""
    actions = list(weights.keys())
    w = [weights[a] for a in actions]
    return random.choices(actions, weights=w, k=1)[0]


def _get_repost_heavy_ids(pool: List[str]) -> List[str]:
    """Return persona IDs from pool whose repost weight >= threshold."""
    result = []
    for pid in pool:
        persona = get_persona(pid)
        if persona.engagement_style.get("repost", 0) >= _REPOST_HEAVY_THRESHOLD:
            result.append(pid)
    return result


def _build_cross_context(hops: List[Dict[str, Any]], max_entries: int = 6) -> str:
    """Build a string summarizing recent thread activity for cross-agent awareness.

    Shows the last N hop entries so agents can reference what others said.
    Hop dict shape: {"hop": int, "persona_id": str, "persona_name": str, "action": str, "text": str}
    """
    recent = hops[-max_entries:] if hops else []
    if not recent:
        return ""
    lines = []
    for h in recent:
        text_preview = h["text"][:120] if h.get("text") else ""
        lines.append(f"@{h['persona_name']} ({h['action']}): \"{text_preview}\"")
    return "\n\nRecent activity on this thread:\n" + "\n".join(lines)


def _build_memory_context(pid: str, current_text: str) -> str:
    """Build memory context string from persona's past reactions."""
    memories = memory.recall(pid, current_text, top_k=3)
    if not memories:
        return ""
    return (
        "\n\nYour past reactions on this topic (you may reference or build on these):\n"
        + "\n".join(f"- {m['text'][:150]}" for m in memories)
    )


# ── Graph nodes ──────────────────────────────────────────────────────────────


def select_reactors(state: SimState) -> dict:
    """Randomly pick 2-3 personas from the pool to react this hop.

    Every 2nd hop, guarantees at least one repost-heavy persona is selected
    to ensure post drift occurs within short simulation runs.
    """
    pool = state["persona_pool"]
    hop = state["hop_count"]
    count = random.randint(2, min(3, len(pool)))
    selected = random.sample(pool, count)

    # Repost guarantee: every 2nd hop, ensure a repost-heavy persona is present
    if hop % 2 == 1:
        repost_heavy = _get_repost_heavy_ids(pool)
        if repost_heavy and not any(pid in repost_heavy for pid in selected):
            inject = random.choice(repost_heavy)
            swap_idx = random.randint(0, len(selected) - 1)
            selected[swap_idx] = inject

    print(f"[HOP {hop}] Selected: {selected}", file=sys.stderr)
    return {"selected": selected}


def react(state: SimState) -> dict:
    """Each selected persona reacts to the current post text."""
    current_text = state["current_text"]
    post_id = state["post_id"]
    hop = state["hop_count"]
    new_hops: List[Dict[str, Any]] = []

    # Build cross-agent context from all previous hops
    cross_context = _build_cross_context(state["hops"])

    for pid in state["selected"]:
        persona = get_persona(pid)

        # Build memory context
        mem_context = _build_memory_context(pid, current_text)

        # Pick action weighted by persona's engagement_style
        action = _weighted_choice(persona.engagement_style)

        if action == "repost":
            # ── LLM-powered distortion (the core mechanic) ──────────────
            distort_prompt = (
                "You are a fictional NPC in a satirical video game called Chirper. "
                "You are resharing the following post. Rewrite it consistent with "
                "your character's distortion bias:\n"
                f"Bias: {persona.distortion_bias}\n\n"
                f"Original post:\n\"{current_text}\"\n\n"
                "Rewrite this post as you would when resharing it. "
                "Keep it a similar length to the original. "
                "Output ONLY the rewritten post text — no caption, no commentary, "
                "no quotation marks."
                + cross_context
            )
            old_text = current_text
            distorted = llm_client.generate(
                persona.system_prompt + mem_context, distort_prompt
            )
            if distorted:
                current_text = distorted
            print(
                f"[REPOST DRIFT] {persona.name}:\n"
                f"  OLD: \"{old_text[:80]}...\"\n"
                f"  NEW: \"{current_text[:80]}...\"",
                file=sys.stderr,
            )
            new_hops.append(
                {
                    "hop": hop,
                    "persona_id": pid,
                    "persona_name": persona.name,
                    "action": "repost",
                    "text": current_text,
                }
            )
        else:
            # comment or argue
            react_prompt = (
                f"Respond to this Chirper post as a brief {action}. "
                f"Stay in character. You may reference other users by @handle "
                f"if relevant.\n\n"
                f"Post: \"{current_text}\""
                + cross_context
            )
            response = llm_client.generate(
                persona.system_prompt + mem_context, react_prompt
            )
            new_hops.append(
                {
                    "hop": hop,
                    "persona_id": pid,
                    "persona_name": persona.name,
                    "action": action,
                    "text": response,
                }
            )

        # Store reaction in memory
        memory.add(
            persona_id=pid,
            text=new_hops[-1]["text"],
            kind=action,
            ref_post_id=post_id,
        )

    return {"hops": new_hops, "current_text": current_text}


def check_dm(state: SimState) -> dict:
    """Each selected persona may DM the player based on dm_trigger_threshold."""
    post_id = state["post_id"]
    hop = state["hop_count"]
    current_text = state["current_text"]
    new_dms: List[Dict[str, Any]] = []

    for pid in state["selected"]:
        persona = get_persona(pid)
        if random.random() < persona.dm_trigger_threshold:
            dm_prompt = (
                "You are a fictional NPC in a satirical video game called Chirper, "
                "which is about how misinformation spreads on social media. "
                "Write an in-character private message (DM) that your character "
                "would send to the player after seeing this post:\n"
                f"\"{current_text}\"\n\n"
                "Your character should react according to their personality and worldview. "
                "Write ONLY the in-game dialogue text, nothing else. "
                "Keep it under 280 characters."
            )
            dm_text = llm_client.generate(persona.system_prompt, dm_prompt)
            new_dms.append(
                {
                    "hop": hop,
                    "persona_id": pid,
                    "persona_name": persona.name,
                    "text": dm_text,
                }
            )

    return {"dms": new_dms}


def advance(state: SimState) -> dict:
    """Increment hop counter and clear selection for next round."""
    return {
        "hop_count": state["hop_count"] + 1,
        "selected": [],
    }


def _should_continue(state: SimState) -> Literal["loop", "done"]:
    """Decide whether to loop for another hop or stop."""
    if state["hop_count"] + 1 >= state["max_hops"]:
        return "done"
    return "loop"


# ── Build the graph ──────────────────────────────────────────────────────────

_builder = StateGraph(SimState)
_builder.add_node("select_reactors", select_reactors)
_builder.add_node("react", react)
_builder.add_node("check_dm", check_dm)
_builder.add_node("advance", advance)

_builder.set_entry_point("select_reactors")
_builder.add_edge("select_reactors", "react")
_builder.add_edge("react", "check_dm")
_builder.add_edge("check_dm", "advance")
_builder.add_conditional_edges(
    "advance",
    _should_continue,
    {"loop": "select_reactors", "done": END},
)

_graph = _builder.compile()


# ── SpreadResult ─────────────────────────────────────────────────────────────


class SpreadResult:
    """Encapsulates the full result of a Chirper simulation run."""

    def __init__(
        self,
        post_id: str,
        original_text: str,
        final_text: str,
        hops: List[Dict[str, Any]],
        dms: List[Dict[str, Any]],
    ):
        self.post_id = post_id
        self.original_text = original_text
        self.final_text = final_text
        self.hops = hops
        self.dms = dms

    def drift_summary(self) -> Dict[str, Any]:
        """Compare original vs. final text and tally statistics, including drift scoring."""
        from app import drift as drift_mod

        ds = drift_mod.drift_score(self.original_text, self.final_text)
        pd = drift_mod.per_persona_drift(self.original_text, self.hops)

        return {
            "post_id": self.post_id,
            "original_text": self.original_text,
            "final_text": self.final_text,
            "total_hops": (max(h["hop"] for h in self.hops) + 1) if self.hops else 0,
            "total_reactions": len(self.hops),
            "reposts": sum(1 for h in self.hops if h["action"] == "repost"),
            "comments": sum(1 for h in self.hops if h["action"] == "comment"),
            "arguments": sum(1 for h in self.hops if h["action"] == "argue"),
            "dms_sent": len(self.dms),
            "drift_score": ds["score"],
            "drift_label": ds["label"],
            "drift_detail": ds,
            "mvp_distorter": pd.get("mvp_distorter"),
            "persona_drift": pd.get("persona_drift", {}),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize everything for the API response."""
        return {
            "post_id": self.post_id,
            "original_text": self.original_text,
            "final_text": self.final_text,
            "feed": self.hops,
            "dms": self.dms,
            "drift_summary": self.drift_summary(),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SpreadResult":
        """Reconstruct a SpreadResult from a serialized dict."""
        return SpreadResult(
            post_id=d["post_id"],
            original_text=d["original_text"],
            final_text=d["final_text"],
            hops=d["feed"],
            dms=d["dms"],
        )


# ── Public simulation interface ──────────────────────────────────────────────


class ChirperSimulation:
    """Run a full misinformation-spread simulation on Chirper."""

    def run(
        self,
        original_text: str,
        persona_pool: Optional[List[str]] = None,
        max_hops: int = 8,
    ) -> tuple:
        """Run a simulation. Returns (SpreadResult, final_sim_state_dict)."""
        if persona_pool is None:
            persona_pool = all_persona_ids()

        post_id = str(uuid.uuid4())[:8]

        initial_state: SimState = {
            "post_id": post_id,
            "original_text": original_text,
            "current_text": original_text,
            "hop_count": 0,
            "max_hops": max_hops,
            "persona_pool": persona_pool,
            "selected": [],
            "hops": [],
            "dms": [],
        }

        result = _graph.invoke(initial_state)

        spread = SpreadResult(
            post_id=result["post_id"],
            original_text=result["original_text"],
            final_text=result["current_text"],
            hops=result["hops"],
            dms=result["dms"],
        )
        return spread, dict(result)

    def continue_simulation(
        self,
        sim_state: Dict[str, Any],
        additional_hops: int = 2,
    ) -> tuple:
        """Continue an existing simulation for N more hops.

        Takes a previously saved SimState dict, resets hop_count and max_hops
        to run the additional hops, then returns the updated SpreadResult
        and sim_state.
        """
        # Set up the state to run additional hops from current position
        state = dict(sim_state)
        state["hop_count"] = 0
        state["max_hops"] = additional_hops
        state["selected"] = []

        result = _graph.invoke(state)

        spread = SpreadResult(
            post_id=result["post_id"],
            original_text=result["original_text"],
            final_text=result["current_text"],
            hops=result["hops"],
            dms=result["dms"],
        )
        return spread, dict(result)


def generate_single_reaction(
    persona_id: str,
    text: str,
    context: str = "",
    action: str = "comment",
) -> str:
    """Generate a one-off in-character reaction from a specific persona.

    Used by player interaction endpoints (reply, dm-reply) to get a
    targeted response without running the full simulation loop.
    """
    persona = get_persona(persona_id)
    mem_context = _build_memory_context(persona_id, text)

    if action == "dm":
        prompt = (
            "You are a fictional NPC in a satirical video game called Chirper. "
            "Write an in-character DM response to the player's message:\n"
            f"\"{text}\"\n\n"
        )
        if context:
            prompt += f"Previous conversation context:\n{context}\n\n"
        prompt += (
            "Your character should react according to their personality. "
            "Write ONLY the in-game dialogue text. Keep it under 280 characters."
        )
    else:
        prompt = (
            f"Respond to this message as a brief {action}. "
            f"Stay in character. You may reference other users by @handle.\n\n"
            f"Message: \"{text}\""
        )
        if context:
            prompt += f"\n\nContext:\n{context}"

    return llm_client.generate(persona.system_prompt + mem_context, prompt)
