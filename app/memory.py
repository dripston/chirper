"""
Chirper — Per-agent vector memory.

Uses **Pinecone** (one namespace per persona) as the production vector store.
When ECHO_CHAMBER_MOCK=1, falls back to a lightweight in-memory store so the
full pipeline works without Pinecone credentials.

Embeddings:  We use a deterministic numpy hash-embedding for now (zero extra
dependencies).  For production quality, swap _embed() with sentence-transformers
or an API-based embedding service.
"""

import os
import uuid
import hashlib
import numpy as np
from typing import Any, Dict, List, Optional

# ── Embedding helper ─────────────────────────────────────────────────────────

EMBED_DIM = 384


def _embed(text: str) -> List[float]:
    """
    Deterministic hash-based embedding (placeholder).

    Produces a normalized 384-d vector from the text's SHA-256 hash.
    Same text → same vector, so cosine-similarity works directionally.
    For production, replace with sentence-transformers all-MiniLM-L6-v2.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Use multiple 4-byte chunks from hash to seed multiple sub-vectors,
    # then concatenate for richer representation.
    parts = []
    for i in range(0, min(len(h), 32), 4):
        seed = int.from_bytes(h[i : i + 4], "big")
        rng = np.random.RandomState(seed)
        parts.append(rng.randn(EMBED_DIM // 8))
    vec = np.concatenate(parts)
    vec = vec / (np.linalg.norm(vec) + 1e-9)
    return vec.tolist()


# ── In-memory mock store ─────────────────────────────────────────────────────


class _MockStore:
    """Simple in-memory vector store for testing without Pinecone."""

    def __init__(self):
        self._data: Dict[str, List[Dict]] = {}  # namespace -> list of records

    def add(
        self,
        persona_id: str,
        text: str,
        kind: str,
        ref_post_id: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        ns = self._data.setdefault(persona_id, [])
        record_id = str(uuid.uuid4())[:8]
        ns.append(
            {
                "id": record_id,
                "text": text,
                "vector": _embed(text),
                "kind": kind,
                "ref_post_id": ref_post_id,
                "meta": meta or {},
            }
        )
        return record_id

    def recall(
        self, persona_id: str, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        ns = self._data.get(persona_id, [])
        if not ns:
            return []
        q_vec = np.array(_embed(query))
        scored = []
        for rec in ns:
            r_vec = np.array(rec["vector"])
            sim = float(np.dot(q_vec, r_vec))
            scored.append((sim, rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": rec["id"],
                "text": rec["text"],
                "kind": rec["kind"],
                "ref_post_id": rec["ref_post_id"],
                "score": round(score, 4),
                "meta": rec["meta"],
            }
            for score, rec in scored[:top_k]
        ]


# ── Pinecone store ───────────────────────────────────────────────────────────


class _PineconeStore:
    """Production vector store backed by Pinecone (one namespace per persona)."""

    def __init__(self):
        from pinecone import Pinecone, ServerlessSpec

        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise RuntimeError("PINECONE_API_KEY is not set.")

        self._pc = Pinecone(api_key=api_key)
        self._index_name = os.getenv(
            "PINECONE_INDEX_NAME", "chirper-agents"
        )

        # Create index if it doesn't exist
        existing = [idx.name for idx in self._pc.list_indexes()]
        if self._index_name not in existing:
            env = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
            self._pc.create_index(
                name=self._index_name,
                dimension=EMBED_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=env),
            )

        self._index = self._pc.Index(self._index_name)

    def add(
        self,
        persona_id: str,
        text: str,
        kind: str,
        ref_post_id: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        record_id = str(uuid.uuid4())[:8]
        vector = _embed(text)
        metadata = {
            "text": text,
            "kind": kind,
            "ref_post_id": ref_post_id,
            **(meta or {}),
        }
        self._index.upsert(
            vectors=[(record_id, vector, metadata)],
            namespace=persona_id,
        )
        return record_id

    def recall(
        self, persona_id: str, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        vector = _embed(query)
        results = self._index.query(
            vector=vector,
            top_k=top_k,
            namespace=persona_id,
            include_metadata=True,
        )
        return [
            {
                "id": match.id,
                "text": match.metadata.get("text", ""),
                "kind": match.metadata.get("kind", ""),
                "ref_post_id": match.metadata.get("ref_post_id", ""),
                "score": round(match.score, 4),
                "meta": {
                    k: v
                    for k, v in match.metadata.items()
                    if k not in ("text", "kind", "ref_post_id")
                },
            }
            for match in results.matches
        ]


# ── Module-level singleton ───────────────────────────────────────────────────

_store = None


def _get_store():
    global _store
    if _store is None:
        if os.getenv("ECHO_CHAMBER_MOCK", "0") == "1":
            _store = _MockStore()
        else:
            _store = _PineconeStore()
    return _store


def add(
    persona_id: str,
    text: str,
    kind: str,
    ref_post_id: str,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """Store a memory entry for a persona. Returns the record ID."""
    return _get_store().add(persona_id, text, kind, ref_post_id, meta)


def recall(
    persona_id: str, query: str, top_k: int = 5
) -> List[Dict[str, Any]]:
    """Recall the top-k most relevant memories for a persona given a query."""
    return _get_store().recall(persona_id, query, top_k)


def reset():
    """Reset the store (useful between test runs)."""
    global _store
    _store = None
