"""
Chirper — FastAPI entry point.

Provides the API server for the Chirper simulator.
"""

from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from app.graph import ChirperSimulation
from app.personas import all_personas

app = FastAPI(
    title="Chirper",
    description="Satirical social-strategy simulator about misinformation spread.",
    version="0.1.0",
)


# ── Request / Response models ────────────────────────────────────────────────


class PostRequest(BaseModel):
    text: str
    persona_ids: Optional[List[str]] = None
    max_hops: Optional[int] = 8


class PersonaSummary(BaseModel):
    id: str
    name: str
    ideology: str
    engagement_style: dict


# ── Routes ───────────────────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Basic liveness probe."""
    return {"status": "ok", "phase": 1}


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
    Run a full Chirper simulation.

    Send a post into the agent network and watch it propagate, distort,
    and generate DMs across up to max_hops hops.
    """
    sim = ChirperSimulation()
    result = sim.run(
        original_text=req.text,
        persona_pool=req.persona_ids,
        max_hops=req.max_hops or 8,
    )
    return result.to_dict()
