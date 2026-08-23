"""
Echo Chamber — FastAPI entry point.

Provides the core API server for the Echo Chamber simulator.
Currently only exposes a health-check endpoint; game routes will
be added in later phases.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Echo Chamber",
    description="Satirical social-strategy simulator about misinformation spread.",
    version="0.0.1",
)


@app.get("/health")
async def health_check():
    """Basic liveness probe."""
    return {"status": "ok", "phase": 0}
