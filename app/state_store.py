"""
Chirper — Simulation state persistence (SQLite).

Stores SpreadResult + SimState as serialized JSON keyed by post_id,
so player interaction endpoints can resume/modify existing simulations.

Uses SQLite (stdlib) for zero-dependency persistence that survives
server restarts during development.

TODO: Replace with PostgreSQL or Redis for production multi-process/
multiplayer support.
"""

import json
import os
import sqlite3
from typing import Any, Dict, Optional, Tuple

# ── Database setup ───────────────────────────────────────────────────────────

_DB_PATH = os.getenv("CHIRPER_DB_PATH", "chirper_state.db")


def _get_conn() -> sqlite3.Connection:
    """Return a connection to the SQLite database, creating the table if needed."""
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS simulations (
            post_id TEXT PRIMARY KEY,
            spread_result TEXT NOT NULL,
            sim_state TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


# ── Public API ───────────────────────────────────────────────────────────────


def save(post_id: str, spread_result_dict: Dict[str, Any], sim_state: Dict[str, Any]) -> None:
    """Persist a simulation's SpreadResult and SimState."""
    conn = _get_conn()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO simulations (post_id, spread_result, sim_state)
            VALUES (?, ?, ?)
            """,
            (post_id, json.dumps(spread_result_dict), json.dumps(sim_state)),
        )
        conn.commit()
    finally:
        conn.close()


def load(post_id: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Load a simulation by post_id. Returns (spread_result_dict, sim_state) or None."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT spread_result, sim_state FROM simulations WHERE post_id = ?",
            (post_id,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0]), json.loads(row[1])
    finally:
        conn.close()


def exists(post_id: str) -> bool:
    """Check if a simulation with the given post_id exists."""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT 1 FROM simulations WHERE post_id = ?",
            (post_id,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()
