"""
Chirper — End-to-end simulation test (mock mode).

Run with:  python test_simulation.py

This sets ECHO_CHAMBER_MOCK=1 so no API keys are needed.
"""

import os
import sys

# Force mock mode before any app imports
os.environ["ECHO_CHAMBER_MOCK"] = "1"

# Fix Windows terminal encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.graph import ChirperSimulation
from app.personas import all_persona_ids, all_personas


def main():
    print("=" * 60)
    print("  CHIRPER — Mock Simulation Test")
    print("=" * 60)

    # Show personas
    print("\n📋 Registered Personas:")
    for p in all_personas():
        print(f"   • {p.name:20s}  ({p.id}) — {p.ideology}")

    # Run simulation
    seed_post = "Scientists discover high levels of microplastics in bottled water"

    print(f"\n✏️  Seed Post: \"{seed_post}\"")
    print(f"   Persona Pool: {all_persona_ids()}")
    print(f"   Max Hops: 4")
    print("\n⏳ Running simulation...\n")

    sim = ChirperSimulation()
    result = sim.run(
        original_text=seed_post,
        max_hops=4,
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

    # Quick sanity checks
    assert result.post_id, "post_id should be set"
    assert result.original_text == seed_post, "original_text should be preserved"
    assert len(result.hops) > 0, "should have at least one reaction"
    assert ds["total_reactions"] == len(result.hops), "reaction count mismatch"

    print("✅ All assertions passed. Phase 1 is working!\n")


if __name__ == "__main__":
    main()
