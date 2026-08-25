"""
Chirper -- FastAPI entry point.

Provides the API server for the Chirper simulator, including player
interaction endpoints (reply, dm-reply, retract, edit) and SSE streaming.
"""

import json
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.graph import ChirperSimulation, SpreadResult, generate_single_reaction
from app.personas import all_personas, get_persona
from app import state_store

app = FastAPI(
    title="Chirper",
    description="Satirical social-strategy simulator about misinformation spread.",
    version="0.2.6",
)

# Configure CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_sim = ChirperSimulation()


# ── Request / Response models ────────────────────────────────────────────────


class PostRequest(BaseModel):
    text: str
    persona_ids: Optional[List[str]] = None
    max_hops: Optional[int] = 15
    drift_target: Optional[int] = None
    time_limit_seconds: Optional[int] = 60


class ReplyRequest(BaseModel):
    text: str
    target_hop_index: int


class DmReplyRequest(BaseModel):
    text: str
    target_persona_id: str


class EditRequest(BaseModel):
    new_text: str


class PersonaSummary(BaseModel):
    id: str
    name: str
    ideology: str
    engagement_style: dict


# ── Routes ───────────────────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Basic liveness probe."""
    return {"status": "ok", "phase": "2.6"}


@app.get("/personas", response_model=List[PersonaSummary])
async def list_personas():
    """List all available AI personas (public fields only)."""
    return [
        PersonaSummary(
            id=p.id,
            name=p.name,
            ideology=p.ideology,
            engagement_style=p.engagement_style,
        )
        for p in all_personas()
    ]


@app.post("/post")
async def create_post(req: PostRequest):
    """
    Run a full Chirper simulation (non-streaming).

    Send a post into the agent network and watch it propagate, distort,
    and generate DMs across up to max_hops hops.
    """
    spread, sim_state = _sim.run(
        original_text=req.text,
        persona_pool=req.persona_ids,
        max_hops=req.max_hops or 8,
    )
    # Persist state so player can interact with this simulation later
    state_store.save(spread.post_id, spread.to_dict(), sim_state)
    return spread.to_dict()


@app.post("/post/stream")
async def create_post_stream(req: PostRequest):
    """
    Run a Chirper simulation with Server-Sent Events (SSE) streaming.

    Each hop/DM is streamed as it happens so you don't have to wait
    for the full simulation to complete. Events:
      - event: hop     -- a persona reacted (comment/argue/repost)
      - event: dm      -- a persona sent a DM
      - event: done    -- simulation complete, full result with drift scoring
    """
    def event_generator():
        try:
            for event in _sim.run_streaming(
                original_text=req.text,
                persona_pool=req.persona_ids,
                max_hops=req.max_hops or 15,
                drift_target=req.drift_target,
                time_limit_seconds=req.time_limit_seconds or 60,
            ):
                event_type = event["event"]
                data = json.dumps(event["data"], ensure_ascii=False)
                yield f"event: {event_type}\ndata: {data}\n\n"
        except Exception as e:
            error_data = json.dumps({"message": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Player interaction endpoints ─────────────────────────────────────────────


@app.post("/post/{post_id}/reply")
async def reply_to_post(post_id: str, req: ReplyRequest, extra_hops: int = 1):
    """
    Player replies to a specific hop in the feed.

    The replied-to persona (and possibly others) react to the player's
    reply on the next hop cycle.
    """
    loaded = state_store.load(post_id)
    if not loaded:
        raise HTTPException(status_code=404, detail=f"Simulation {post_id} not found")

    spread_dict, sim_state = loaded
    spread = SpreadResult.from_dict(spread_dict)

    # Validate target_hop_index
    if req.target_hop_index < 0 or req.target_hop_index >= len(spread.hops):
        raise HTTPException(status_code=400, detail="Invalid target_hop_index")

    target_hop = spread.hops[req.target_hop_index]
    target_persona_id = target_hop["persona_id"]

    # Add player's reply to the feed
    player_hop = {
        "hop": sim_state.get("hop_count", 0),
        "persona_id": "player",
        "persona_name": "You",
        "action": "player_reply",
        "text": req.text,
    }
    spread.hops.append(player_hop)
    sim_state["hops"] = spread.hops

    # Generate reaction from the target persona
    context = f"@You replied to @{target_hop['persona_name']}: \"{target_hop['text'][:120]}\""
    reaction = generate_single_reaction(
        target_persona_id, req.text, context=context, action="comment"
    )
    reaction_hop = {
        "hop": sim_state.get("hop_count", 0) + 1,
        "persona_id": target_persona_id,
        "persona_name": target_hop["persona_name"],
        "action": "comment",
        "text": reaction,
    }
    spread.hops.append(reaction_hop)
    sim_state["hops"] = spread.hops
    sim_state["hop_count"] = sim_state.get("hop_count", 0) + 1

    # Continue simulation for extra hops if requested
    if extra_hops > 1:
        sim_state["current_text"] = sim_state.get("current_text", spread.final_text)
        continued_spread, sim_state = _sim.continue_simulation(sim_state, extra_hops - 1)
        spread.hops = sim_state["hops"]
        spread.dms.extend(continued_spread.dms)
        spread.final_text = continued_spread.final_text

    # Persist updated state
    state_store.save(post_id, spread.to_dict(), sim_state)
    return spread.to_dict()


@app.post("/post/{post_id}/dm-reply")
async def dm_reply(post_id: str, req: DmReplyRequest):
    """
    Player responds to a DM. The sending persona generates a follow-up.
    """
    loaded = state_store.load(post_id)
    if not loaded:
        raise HTTPException(status_code=404, detail=f"Simulation {post_id} not found")

    spread_dict, sim_state = loaded
    spread = SpreadResult.from_dict(spread_dict)

    # Validate persona exists
    try:
        persona = get_persona(req.target_persona_id)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Unknown persona: {req.target_persona_id}")

    # Find original DM for context
    original_dm_text = ""
    for dm in spread.dms:
        if dm["persona_id"] == req.target_persona_id:
            original_dm_text = dm["text"]
            break

    context = ""
    if original_dm_text:
        context = f"Your previous DM: \"{original_dm_text[:120]}\"\nPlayer replied: \"{req.text[:120]}\""

    # Generate follow-up DM
    followup = generate_single_reaction(
        req.target_persona_id, req.text, context=context, action="dm"
    )

    # Add player's DM and persona's followup to DMs
    player_dm = {
        "hop": sim_state.get("hop_count", 0),
        "persona_id": "player",
        "persona_name": "You",
        "text": req.text,
    }
    followup_dm = {
        "hop": sim_state.get("hop_count", 0),
        "persona_id": req.target_persona_id,
        "persona_name": persona.name,
        "text": followup,
    }
    spread.dms.append(player_dm)
    spread.dms.append(followup_dm)

    # Persist
    state_store.save(post_id, spread.to_dict(), sim_state)
    return {
        "player_dm": player_dm,
        "followup_dm": followup_dm,
        "all_dms": spread.dms,
    }


@app.post("/post/{post_id}/retract")
async def retract_post(post_id: str, extra_hops: int = 2):
    """
    Player retracts their original post mid-spread.

    Some personas (engagement_farmer, conspiracist) react to the retraction
    itself as suspicious rather than stopping the spread.
    """
    loaded = state_store.load(post_id)
    if not loaded:
        raise HTTPException(status_code=404, detail=f"Simulation {post_id} not found")

    spread_dict, sim_state = loaded
    spread = SpreadResult.from_dict(spread_dict)

    # Add retraction event to feed
    retraction_hop = {
        "hop": sim_state.get("hop_count", 0),
        "persona_id": "player",
        "persona_name": "You",
        "action": "retraction",
        "text": "[RETRACTED by original poster]",
    }
    spread.hops.append(retraction_hop)
    sim_state["hops"] = spread.hops

    # Set current text to retraction notice so agents react to it
    sim_state["current_text"] = (
        f"[POST RETRACTED] The original poster deleted their post. "
        f"The post originally said: \"{spread.original_text}\""
    )

    # Continue simulation — agents react to the retraction
    continued_spread, sim_state = _sim.continue_simulation(sim_state, extra_hops)
    spread.hops = sim_state["hops"]
    spread.dms.extend(continued_spread.dms)
    spread.final_text = continued_spread.final_text

    # Persist
    state_store.save(post_id, spread.to_dict(), sim_state)
    return spread.to_dict()


@app.post("/post/{post_id}/edit")
async def edit_post(post_id: str, req: EditRequest, extra_hops: int = 2):
    """
    Player edits their original post before further hops.

    Already-spread distortions are NOT retroactively changed (drift already
    happened), but future hops react to the edited text, and at least one
    persona should call out the edit.
    """
    loaded = state_store.load(post_id)
    if not loaded:
        raise HTTPException(status_code=404, detail=f"Simulation {post_id} not found")

    spread_dict, sim_state = loaded
    spread = SpreadResult.from_dict(spread_dict)

    # Add edit event to feed
    edit_hop = {
        "hop": sim_state.get("hop_count", 0),
        "persona_id": "player",
        "persona_name": "You",
        "action": "edit",
        "text": f"[EDITED] {req.new_text}",
    }
    spread.hops.append(edit_hop)
    sim_state["hops"] = spread.hops

    # Update current text so future hops see the edit, but preserve original
    sim_state["current_text"] = (
        f"[EDITED POST] Originally said: \"{spread.original_text[:100]}\" "
        f"Now says: \"{req.new_text}\""
    )

    # Continue simulation
    continued_spread, sim_state = _sim.continue_simulation(sim_state, extra_hops)
    spread.hops = sim_state["hops"]
    spread.dms.extend(continued_spread.dms)
    spread.final_text = continued_spread.final_text

    # Persist
    state_store.save(post_id, spread.to_dict(), sim_state)
    return spread.to_dict()
