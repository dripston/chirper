"""
Chirper — End-to-end simulation test (mock mode).

Run with:  python test_simulation.py

This sets ECHO_CHAMBER_MOCK=1 so no API keys are needed.
"""

import os
import sys
from collections import Counter

# Force mock mode before any app imports
os.environ["ECHO_CHAMBER_MOCK"] = "1"

# Fix Windows terminal encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.graph import ChirperSimulation
from app.personas import all_persona_ids, all_personas


def main():
    print("=" * 60)
    print("  CHIRPER — Phase 2 Mock Simulation Test (10 hops)")
    print("=" * 60)

    # Show personas
    print("\n📋 Registered Personas:")
    for p in all_personas():
        repost_w = p.engagement_style.get("repost", 0)
        marker = " ★" if repost_w >= 0.35 else ""
        print(f"   • {p.name:20s}  ({p.id}) — repost_w={repost_w:.2f}{marker}")

    # Run simulation
    seed_post = "Scientists discover high levels of microplastics in bottled water"

    print(f"\n✏️  Seed Post: \"{seed_post}\"")
    print(f"   Persona Pool: {all_persona_ids()}")
    print(f"   Max Hops: 10")
    print("\n⏳ Running simulation...\n")

    sim = ChirperSimulation()
    result = sim.run(
        original_text=seed_post,
        max_hops=10,
    )

    # Print feed
    print("─" * 60)
    print("  📰 FEED")
    print("─" * 60)
    for i, hop in enumerate(result.hops):
        icon = {"comment": "💬", "argue": "⚔️", "repost": "🔁"}.get(
            hop["action"], "•"
        )
        print(
            f"  [{hop['hop']}] {icon} {hop['persona_name']:20s} "
            f"({hop['action']})"
        )
        print(f"      \"{hop['text']}\"\n")

    # Print DMs
    print("─" * 60)
    print("  📩 DIRECT MESSAGES")
    print("─" * 60)
    if result.dms:
        for dm in result.dms:
            print(
                f"  [hop {dm['hop']}] 🔒 {dm['persona_name']}:"
            )
            print(f"      \"{dm['text']}\"\n")
    else:
        print("  (no DMs this run)\n")

    # Print drift summary
    print("─" * 60)
    print("  📊 DRIFT SUMMARY")
    print("─" * 60)
    ds = result.drift_summary()
    print(f"   Post ID:         {ds['post_id']}")
    print(f"   Original:        \"{ds['original_text']}\"")
    print(f"   Final:           \"{ds['final_text']}\"")
    print(f"   Total Hops:      {ds['total_hops']}")
    print(f"   Total Reactions:  {ds['total_reactions']}")
    print(f"   ├─ Reposts:      {ds['reposts']}")
    print(f"   ├─ Comments:     {ds['comments']}")
    print(f"   ├─ Arguments:    {ds['arguments']}")
    print(f"   └─ DMs Sent:     {ds['dms_sent']}")
    print()

    # ── Persona diversity report ─────────────────────────────────────────
    print("─" * 60)
    print("  🎭 PERSONA DIVERSITY")
    print("─" * 60)
    persona_counts = Counter(h["persona_id"] for h in result.hops)
    for pid, count in persona_counts.most_common():
        bar = "█" * count
        print(f"   {pid:20s} │ {bar} ({count})")
    unique_personas = len(persona_counts)
    print(f"\n   Unique personas selected: {unique_personas} / {len(all_persona_ids())}")
    print()

    # ── Assertions ───────────────────────────────────────────────────────
    errors = []

    if not result.post_id:
        errors.append("post_id should be set")

    if result.original_text != seed_post:
        errors.append("original_text should be preserved")

    if len(result.hops) == 0:
        errors.append("should have at least one reaction")

    if ds["total_reactions"] != len(result.hops):
        errors.append("reaction count mismatch")

    # Phase 2 assertions
    if ds["reposts"] < 1:
        errors.append(f"REPOST CHECK FAILED: expected ≥1 repost, got {ds['reposts']}")

    if result.final_text == seed_post:
        errors.append("DRIFT CHECK FAILED: final_text is identical to original_text (no drift occurred)")

    if unique_personas < 3:
        errors.append(f"DIVERSITY CHECK FAILED: only {unique_personas} unique personas selected (need ≥3)")

    if ds["dms_sent"] < 1:
        errors.append(f"DM CHECK FAILED: expected ≥1 DM, got {ds['dms_sent']}")

    if errors:
        print("❌ ASSERTION FAILURES:")
        for e in errors:
            print(f"   • {e}")
        print()
        sys.exit(1)
    else:
        print("✅ All Phase 2 assertions passed!\n")


if __name__ == "__main__":
    main()
