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
import time
import queue
import threading
import concurrent.futures
from typing import Annotated, Any, Dict, List, Literal, Optional

from langgraph.graph import END, StateGraph

from app import llm_client, memory
from app.personas import all_persona_ids, get_persona

_active_queues = {}

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
    force_intervention: Annotated[bool, _last_write]


# ── Helpers ──────────────────────────────────────────────────────────────────

_REPOST_HEAVY_THRESHOLD = 0.35


def _weighted_choice(weights: Dict[str, float]) -> str:
    """Pick an action from a {action: weight} dict."""
    actions = list(weights.keys())
    w = [weights[a] for a in actions]
    return random.choices(actions, weights=w, k=1)[0]


def _get_repost_heavy_ids(pool: List[str]) -> List[str]:
    """Return persona IDs from pool whose structural role is spreader or commentator."""
    result = []
    for pid in pool:
        persona = get_persona(pid)
        if persona.structural_role in ("spreader", "commentator"):
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

    If force_intervention is true, forces the verifier to interject.
    """
    if state.get("force_intervention"):
        print(f"[CIRCUIT BREAKER] Propaganda threshold reached. Forcing fact_checker intervention.", file=sys.stderr)
        return {"selected": ["fact_checker"], "force_intervention": False}

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


def _process_reaction(pid, current_text, post_id, hop, cross_context):
    persona = get_persona(pid)
    mem_context = _build_memory_context(pid, current_text)
    
    if persona.structural_role == "spreader":
        action = "repost"
    elif persona.structural_role == "commentator":
        action = random.choice(["repost", "repost", "argue", "comment"])
    else:
        action = "comment"
        
    role_constraints = {
        "spreader": "Amplify sensational aspects. Share quickly. Do not add new personal opinions.",
        "commentator": "Add your personal opinions and interpret the news through your unique bias.",
        "verifier": "Perform verification. Check the claims against your knowledge before sharing.",
        "bystander": "Consume news without participating in dissemination. Retain your previous stance."
    }

    worldview = " ".join(persona.worldview_matrix)
    
    hybrid_memory_prompt = (
        f"Your Worldview (Foundational Memory):\n{worldview}\n\n"
        f"Your Role Constraint: {role_constraints[persona.structural_role]}\n\n"
        "INSTRUCTIONS:\n"
        "1. Evaluate if this topic naturally intersects with your worldview. "
        "If you can make a small, logical inferential leap, do so. "
        "If the topic is completely irrelevant and impossible to connect to your worldview, "
        "output EXACTLY the word '[SKIP]' and nothing else to ignore the post.\n"
        "2. Otherwise, update your internal Long-Term Memory by integrating today's Short-Term summary "
        "and your past reactions. Output your reaction based on this integrated understanding."
    )
    
    distorted_text = None
    if action == "repost":
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
        try:
            response = llm_client.generate(persona.system_prompt + "\n\n" + hybrid_memory_prompt + mem_context, distort_prompt)
        except llm_client.SafetyRefusalError:
            print(f"[REPOST DRIFT] {persona.name}: Refused. Skipping.", file=sys.stderr)
            return None, None

        if response.strip() == "[SKIP]":
            print(f"[RELEVANCE] {persona.name} skipped post.", file=sys.stderr)
            return None, None

        if response:
            distorted_text = response
        else:
            response = current_text
            
        print(
            f"[REPOST DRIFT] {persona.name}:\n"
            f"  OLD: \"{old_text[:80]}...\"\n"
            f"  NEW: \"{response[:80]}...\"",
            file=sys.stderr,
        )
    else:
        react_prompt = (
            f"Respond to this Chirper post as a brief {action}. "
            f"Stay in character. You may reference other users by @handle "
            f"if relevant.\n\n"
            f"Post: \"{current_text}\""
            + cross_context
        )
        try:
            response = llm_client.generate(persona.system_prompt + "\n\n" + hybrid_memory_prompt + mem_context, react_prompt)
        except llm_client.SafetyRefusalError:
            print(f"[REACT] {persona.name}: Refused. Skipping.", file=sys.stderr)
            return None, None
            
        if response.strip() == "[SKIP]":
            print(f"[RELEVANCE] {persona.name} skipped post.", file=sys.stderr)
            return None, None

    hop_dict = {
        "hop": hop,
        "persona_id": pid,
        "persona_name": persona.name,
        "action": action,
        "text": response,
    }
    
    return hop_dict, distorted_text


def react(state: SimState) -> dict:
    """Each selected persona reacts to the current post text concurrently."""
    current_text = state["current_text"]
    post_id = state["post_id"]
    hop = state["hop_count"]
    new_hops: List[Dict[str, Any]] = []

    # Build cross-agent context from all previous hops
    cross_context = _build_cross_context(state["hops"])

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for pid in state["selected"]:
            futures.append(
                executor.submit(_process_reaction, pid, current_text, post_id, hop, cross_context)
            )
            
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res == (None, None):
                continue
                
            hop_dict, distorted_text = res
            new_hops.append(hop_dict)
            if distorted_text:
                current_text = distorted_text
                
            # Store reaction in memory sequentially to avoid race conditions
            memory.add(
                persona_id=hop_dict["persona_id"],
                text=hop_dict["text"],
                kind=hop_dict["action"],
                ref_post_id=post_id,
            )
            
            q = _active_queues.get(post_id)
            force_intervention = False
            if q:
                from app import drift as drift_mod
                ds = drift_mod.drift_score(state["original_text"], current_text)
                if ds["score"] >= 60:
                    force_intervention = True
                
                hop_dict["drift_score_so_far"] = ds["score"]
                q.put({
                    "event": "entropy_update", 
                    "data": {
                        "hop": hop, 
                        "drift_score": ds["score"], 
                        "drift_label": ds["label"]
                    }
                })
                q.put({"event": "hop", "data": hop_dict})

    return {"hops": new_hops, "current_text": current_text, "force_intervention": force_intervention}


def _process_dm(pid, current_text, post_id, hop):
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
        try:
            dm_text = llm_client.generate(persona.system_prompt, dm_prompt)
        except llm_client.SafetyRefusalError:
            print(f"[DM] {persona.name}: Refused. Skipping.", file=sys.stderr)
            return None
            
        return {
            "hop": hop,
            "persona_id": pid,
            "persona_name": persona.name,
            "text": dm_text,
        }
    return None


def check_dm(state: SimState) -> dict:
    """Each selected persona may DM the player based on dm_trigger_threshold."""
    post_id = state["post_id"]
    hop = state["hop_count"]
    current_text = state["current_text"]
    new_dms: List[Dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for pid in state["selected"]:
            futures.append(
                executor.submit(_process_dm, pid, current_text, post_id, hop)
            )
            
        for future in concurrent.futures.as_completed(futures):
            dm = future.result()
            if dm:
                new_dms.append(dm)
                q = _active_queues.get(post_id)
                if q:
                    q.put({"event": "dm", "data": dm})

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
        stop_reason: str = "max_hops_reached",
    ):
        self.post_id = post_id
        self.original_text = original_text
        self.final_text = final_text
        self.hops = hops
        self.dms = dms
        self.stop_reason = stop_reason

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
            "stop_reason": self.stop_reason,
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
            stop_reason=d.get("drift_summary", {}).get("stop_reason", "max_hops_reached"),
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
        memory.reset()
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

    def run_streaming(
        self,
        original_text: str,
        persona_pool: Optional[List[str]] = None,
        max_hops: int = 15,
        drift_target: Optional[int] = None,
        time_limit_seconds: int = 60,
    ):
        """Run a simulation with streaming, yielding SSE events per node."""
        memory.reset()
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

        q = queue.Queue()
        _active_queues[post_id] = q

        def _bg_run():
            all_hops = []
            all_dms = []
            current_text = original_text
            stop_reason = "max_hops_reached"
            start_time = time.time()
            
            from app import drift as drift_mod

            try:
                for event in _graph.stream(initial_state, stream_mode="updates"):
                    # Check time limit immediately after hop computation
                    if time.time() - start_time >= time_limit_seconds:
                        stop_reason = "time_limit_reached"
                        break
                        
                    should_break_drift = False

                    for node_name, updates in event.items():
                        if node_name == "react":
                            if "current_text" in updates:
                                current_text = updates["current_text"]
                            if "hops" in updates:
                                all_hops.extend(updates["hops"])
                            
                            ds = drift_mod.drift_score(original_text, current_text)
                            if drift_target is not None and ds["score"] >= drift_target:
                                stop_reason = "drift_target_reached"
                                should_break_drift = True
                                break
                                
                        elif node_name == "check_dm" and "dms" in updates:
                            all_dms.extend(updates["dms"])
                            
                    if should_break_drift:
                        break

                # Build final result from accumulated stream data
                spread = SpreadResult(
                    post_id=post_id,
                    original_text=original_text,
                    final_text=current_text,
                    hops=all_hops,
                    dms=all_dms,
                    stop_reason=stop_reason,
                )

                # Save to state store
                from app import state_store
                sim_state = {
                    "post_id": post_id,
                    "original_text": original_text,
                    "current_text": current_text,
                    "hop_count": len(all_hops),
                    "max_hops": max_hops,
                    "persona_pool": persona_pool,
                    "selected": [],
                    "hops": all_hops,
                    "dms": all_dms,
                }
                state_store.save(post_id, spread.to_dict(), sim_state)
                
                # Signal completion
                q.put({"event": "done", "data": {"drift_summary": spread.drift_summary()}})
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                q.put({"event": "error", "data": {"message": str(e)}})
            finally:
                q.put(None)
                _active_queues.pop(post_id, None)

        threading.Thread(target=_bg_run, daemon=True).start()

        while True:
            item = q.get()
            if item is None:
                break
            yield item



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
