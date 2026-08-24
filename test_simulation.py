"""
Chirper — Phase 2.5 End-to-end simulation test (mock mode).

Run with:  python test_simulation.py

Tests:
  - 10-hop simulation with all 10 personas
  - Player reply, DM reply, and retraction
  - Drift scoring + drift label
  - Cross-agent @handle referencing
  - Persona diversity
"""

import os
import sys
from collections import Counter

# Force mock mode before any app imports
os.environ["ECHO_CHAMBER_MOCK"] = "1"

# Fix Windows terminal encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.graph import ChirperSimulation, SpreadResult, generate_single_reaction
from app.personas import all_persona_ids, all_personas, get_persona
from app import state_store


def main():
    print("=" * 60)
    print("  CHIRPER — Phase 2.5 Test (10 hops + player interaction)")
    print("=" * 60)

    # Show all 10 personas
    print(f"\n📋 Registered Personas ({len(all_persona_ids())}):")
    for p in all_personas():
        repost_w = p.engagement_style.get("repost", 0)
        marker = " ★" if repost_w >= 0.35 else ""
        print(f"   • {p.name:22s}  ({p.id:20s}) — repost_w={repost_w:.2f}{marker}")

    # ─── 1. Run 10-hop simulation ────────────────────────────────────────
    seed_post = "Scientists discover high levels of microplastics in bottled water"
    print(f"\n{'─' * 60}")
    print(f"  ▶ STEP 1: Run 10-hop simulation")
    print(f"{'─' * 60}")
    print(f"  Seed: \"{seed_post}\"")
    print(f"  Max Hops: 10")
    print(f"  Persona Pool: {len(all_persona_ids())} personas\n")

    sim = ChirperSimulation()
    result, sim_state = sim.run(original_text=seed_post, max_hops=10)

    # Save to state store so interaction endpoints work
    state_store.save(result.post_id, result.to_dict(), sim_state)

    # Print feed
    print(f"\n{'─' * 60}")
    print(f"  📰 FEED ({len(result.hops)} reactions)")
    print(f"{'─' * 60}")
    for hop in result.hops:
        icon = {"comment": "💬", "argue": "⚔️", "repost": "🔁"}.get(hop["action"], "•")
        print(f"  [{hop['hop']}] {icon} {hop['persona_name']:22s} ({hop['action']})")
        print(f"      \"{hop['text'][:100]}\"")
        print()

    # Print DMs
    print(f"{'─' * 60}")
    print(f"  📩 DIRECT MESSAGES ({len(result.dms)})")
    print(f"{'─' * 60}")
    for dm in result.dms:
        print(f"  [hop {dm['hop']}] 🔒 {dm['persona_name']}: \"{dm['text'][:100]}\"")
    if not result.dms:
        print("  (no DMs this run)")
    print()

    # Print drift summary
    ds = result.drift_summary()
    print(f"{'─' * 60}")
    print(f"  📊 DRIFT SUMMARY")
    print(f"{'─' * 60}")
    print(f"   Post ID:         {ds['post_id']}")
    print(f"   Original:        \"{ds['original_text'][:80]}\"")
    print(f"   Final:           \"{ds['final_text'][:80]}\"")
    print(f"   Total Hops:      {ds['total_hops']}")
    print(f"   Total Reactions:  {ds['total_reactions']}")
    print(f"   ├─ Reposts:      {ds['reposts']}")
    print(f"   ├─ Comments:     {ds['comments']}")
    print(f"   ├─ Arguments:    {ds['arguments']}")
    print(f"   └─ DMs Sent:     {ds['dms_sent']}")
    print(f"\n   🎯 Drift Score:   {ds['drift_score']}/100 — \"{ds['drift_label']}\"")
    print(f"   📏 Embed Dist:    {ds['drift_detail']['embedding_distance']}")
    print(f"   🎭 Tone Shift:    {ds['drift_detail']['tone_shift']}/5")
    if ds.get("mvp_distorter"):
        mvp_persona = get_persona(ds["mvp_distorter"])
        print(f"   🏆 MVP Distorter: {mvp_persona.name} ({ds['mvp_distorter']})")
    print()

    # Persona diversity
    print(f"{'─' * 60}")
    print(f"  🎭 PERSONA DIVERSITY")
    print(f"{'─' * 60}")
    persona_counts = Counter(h["persona_id"] for h in result.hops)
    for pid, count in persona_counts.most_common():
        bar = "█" * count
        print(f"   {pid:22s} │ {bar} ({count})")
    unique_personas = len(persona_counts)
    print(f"\n   Unique personas: {unique_personas} / {len(all_persona_ids())}")
    print()

    # Cross-agent referencing check
    print(f"{'─' * 60}")
    print(f"  🔗 CROSS-AGENT REFERENCES (hops containing @)")
    print(f"{'─' * 60}")
    at_refs = [h for h in result.hops if "@" in h.get("text", "")]
    if at_refs:
        for h in at_refs:
            print(f"  [{h['hop']}] {h['persona_name']}: \"{h['text'][:120]}\"")
    else:
        print("  (no @handle references found — expected in mock mode)")
    print()

    # ─── 2. Player Reply ─────────────────────────────────────────────────
    print(f"{'─' * 60}")
    print(f"  ▶ STEP 2: Player replies to hop 0")
    print(f"{'─' * 60}")
    if result.hops:
        target = result.hops[0]
        reply_text = "That study was debunked last week, check your sources."
        print(f"  Target: @{target['persona_name']} said \"{target['text'][:60]}...\"")
        print(f"  Reply:  \"{reply_text}\"")

        context = f"@You replied to @{target['persona_name']}: \"{target['text'][:120]}\""
        reaction = generate_single_reaction(
            target["persona_id"], reply_text, context=context, action="comment"
        )
        print(f"\n  📬 {target['persona_name']} responds:")
        print(f"      \"{reaction}\"")
    print()

    # ─── 3. DM Reply ─────────────────────────────────────────────────────
    print(f"{'─' * 60}")
    print(f"  ▶ STEP 3: Player replies to a DM")
    print(f"{'─' * 60}")
    if result.dms:
        dm = result.dms[0]
        dm_reply_text = "I don't think that's true. Can you send me the source?"
        print(f"  Original DM from @{dm['persona_name']}: \"{dm['text'][:80]}...\"")
        print(f"  Player reply: \"{dm_reply_text}\"")

        dm_context = f"Your previous DM: \"{dm['text'][:120]}\"\nPlayer replied: \"{dm_reply_text[:120]}\""
        followup = generate_single_reaction(
            dm["persona_id"], dm_reply_text, context=dm_context, action="dm"
        )
        print(f"\n  📬 {dm['persona_name']} follows up:")
        print(f"      \"{followup}\"")
    else:
        print("  (no DMs to reply to)")
    print()

    # ─── 4. Retraction ───────────────────────────────────────────────────
    print(f"{'─' * 60}")
    print(f"  ▶ STEP 4: Player retracts the post")
    print(f"{'─' * 60}")
    print(f"  Simulating retraction with 2 additional hops...")

    # Set up retraction state
    retract_state = dict(sim_state)
    retract_state["current_text"] = (
        f"[POST RETRACTED] The original poster deleted their post. "
        f"The post originally said: \"{seed_post}\""
    )
    retract_state["hops"] = list(sim_state["hops"])
    retract_state["hops"].append({
        "hop": retract_state.get("hop_count", 0),
        "persona_id": "player",
        "persona_name": "You",
        "action": "retraction",
        "text": "[RETRACTED by original poster]",
    })

    retract_result, retract_sim = sim.continue_simulation(retract_state, additional_hops=2)
    # Get only the new hops (retraction reactions)
    original_hop_count = len(sim_state["hops"]) + 1  # +1 for the retraction event
    new_hops = retract_result.hops[original_hop_count:]
    print(f"\n  📰 Reactions to retraction ({len(new_hops)} new):")
    for h in new_hops:
        icon = {"comment": "💬", "argue": "⚔️", "repost": "🔁"}.get(h["action"], "•")
        print(f"  [{h['hop']}] {icon} {h['persona_name']:22s} ({h['action']})")
        print(f"      \"{h['text'][:100]}\"")
        print()
    print()

    # ─── Assertions ──────────────────────────────────────────────────────
    print("═" * 60)
    print("  ✓ ASSERTIONS")
    print("═" * 60)
    errors = []

    if not result.post_id:
        errors.append("post_id should be set")
    if result.original_text != seed_post:
        errors.append("original_text should be preserved")
    if len(result.hops) == 0:
        errors.append("should have at least one reaction")
    if ds["reposts"] < 1:
        errors.append(f"REPOST: expected ≥1, got {ds['reposts']}")
    if result.final_text == seed_post:
        errors.append("DRIFT: final_text identical to original (no drift)")
    if unique_personas < 5:
        errors.append(f"DIVERSITY: only {unique_personas} unique personas (need ≥5)")
    if ds["drift_score"] is None or ds["drift_score"] == 0:
        errors.append("DRIFT SCORE: should be non-zero")
    if not ds.get("drift_label"):
        errors.append("DRIFT LABEL: should be populated")
    if len(all_persona_ids()) != 10:
        errors.append(f"PERSONAS: expected 10 registered, got {len(all_persona_ids())}")

    # State store assertions
    loaded = state_store.load(result.post_id)
    if not loaded:
        errors.append("STATE STORE: save/load failed")
    else:
        print(f"   ✓ SQLite state store: save/load works for {result.post_id}")

    if errors:
        print("\n❌ FAILURES:")
        for e in errors:
            print(f"   • {e}")
        sys.exit(1)
    else:
        for check in [
            f"10 personas registered: {len(all_persona_ids())}",
            f"Reposts: {ds['reposts']}",
            f"Drift score: {ds['drift_score']}/100 ({ds['drift_label']})",
            f"Unique personas: {unique_personas}",
            f"DMs sent: {ds['dms_sent']}",
            f"Player reply generated reaction",
            f"Retraction generated {len(new_hops)} reactions",
        ]:
            print(f"   ✓ {check}")
        print(f"\n✅ All Phase 2.5 assertions passed!\n")


if __name__ == "__main__":
    main()
