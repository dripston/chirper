"""
Chirper — LangGraph spread simulation.

Implements the core "misinformation telephone" loop:
  select_reactors → react → check_dm → advance → (loop or end)

Each hop picks 1-2 agents from the persona pool. Agents comment, argue,
or repost (with LLM-powered distortion). DMs are sent probabilistically
based on each persona's dm_trigger_threshold.
"""

import os
import random
import uuid
from typing import Annotated, Any, Dict, List, Literal, Optional

from langgraph.graph import END, StateGraph

from app import llm_client, memory
from app.personas import all_persona_ids, get_persona

# ── State schema (TypedDict for LangGraph) ───────────────────────────────────
# Using Annotated with a reducer lets LangGraph know how to merge node outputs
# back into the state.  Keys without Annotated use "last write wins."

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


def _weighted_choice(weights: Dict[str, float]) -> str:
    """Pick an action from a {action: weight} dict."""
    actions = list(weights.keys())
    w = [weights[a] for a in actions]
    return random.choices(actions, weights=w, k=1)[0]


# ── Graph nodes ──────────────────────────────────────────────────────────────


def select_reactors(state: SimState) -> dict:
    """Randomly pick 1-2 personas from the pool to react this hop."""
    pool = state["persona_pool"]
    count = random.randint(1, min(2, len(pool)))
    selected = random.sample(pool, count)
    return {"selected": selected}


def react(state: SimState) -> dict:
    """Each selected persona reacts to the current post text."""
    current_text = state["current_text"]
    post_id = state["post_id"]
    hop = state["hop_count"]
    new_hops: List[Dict[str, Any]] = []

    for pid in state["selected"]:
        persona = get_persona(pid)

        # Recall relevant memory for context
        memories = memory.recall(pid, current_text, top_k=3)
        mem_context = ""
        if memories:
            mem_context = (
                "\n\nYour recent memories:\n"
                + "\n".join(f"- {m['text']}" for m in memories)
            )

        # Pick action weighted by persona's engagement_style
        action = _weighted_choice(persona.engagement_style)

        if action == "repost":
            # ── LLM-powered distortion (the core mechanic) ──────────────
            distort_prompt = (
                f"You are reposting the following post on Chirper.\n"
                f"Your distortion bias: {persona.distortion_bias}\n\n"
                f"Original post:\n\"{current_text}\"\n\n"
                f"Rewrite this post in your own words, applying your bias. "
                f"Keep it under 280 characters. Output ONLY the rewritten post."
            )
            distorted = llm_client.generate(
                persona.system_prompt + mem_context, distort_prompt
            )
            current_text = distorted  # the post mutates
            new_hops.append(
                {
                    "hop": hop,
                    "persona_id": pid,
                    "persona_name": persona.name,
                    "action": "repost",
                    "text": distorted,
                }
            )
        else:
            # comment or argue
            react_prompt = (
                f"Respond to this Chirper post as a brief {action}. "
                f"Stay in character.\n\n"
                f"Post: \"{current_text}\""
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
                f"You are sending a private DM to the original poster on Chirper. "
                f"The post that caught your attention:\n\"{current_text}\"\n\n"
                f"Write a brief, in-character DM. You might try to recruit them, "
                f"warn them, provoke them, or radicalize them toward your worldview. "
                f"Keep it under 280 characters. Output ONLY the DM text."
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
        """Compare original vs. final text and tally statistics."""
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


# ── Public simulation interface ──────────────────────────────────────────────


class ChirperSimulation:
    """Run a full misinformation-spread simulation on Chirper."""

    def run(
        self,
        original_text: str,
        persona_pool: Optional[List[str]] = None,
        max_hops: int = 8,
    ) -> SpreadResult:
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

        return SpreadResult(
            post_id=result["post_id"],
            original_text=result["original_text"],
            final_text=result["current_text"],
            hops=result["hops"],
            dms=result["dms"],
        )
