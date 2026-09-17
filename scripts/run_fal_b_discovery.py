"""One-off driver: run a real FAL-B (ferrosilicon export, foreign BUYER) discovery batch
through the existing discovery_pipeline.py machinery, using results gathered via a live web
search done by Claude in this session (see ../data/research/fal_b_ferrosilicon_discoveries_2026-09-17.jsonl).

This does NOT contact, message, or open an account with any of the discovered entities. It only
persists them as unverified CLAIM-level discovery candidates for later human review, exactly as
discovery_pipeline.py's own docstring describes ingest_external_discoveries() for.

Note on batch composition: two candidates surfaced by the underlying web search were deliberately
EXCLUDED from this batch rather than silently included:
  - ferrosilicon.co (an apparent Iranian ferrosilicon exporter's own site) -- role/geography
    mismatch for a foreign-BUYER search; it is a supply-side, Iran-origin listing, not a buyer.
  - Ferroglobe -- a real global ferrosilicon PRODUCER, not a buyer; role mismatch.
Both are noted here (not just in chat) so the exclusion reasoning is preserved alongside the code
that consumes the batch, matching the same evidence-discipline pattern used for FAL-A (where
Ferro Alloys Corporation and the Zaporizhzhia Plant were flagged/caveated rather than silently
folded in).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fal_vertical import assert_lane_scope, PROJECT_ID, LANE_FAL_B
from discovery_pipeline import ingest_external_discoveries, process_discovery_batch
from research_lab import ResearchRun, ResearchLabStore

# Fail-closed lane check first -- same discipline as the rest of this project.
lane = assert_lane_scope(project_id=PROJECT_ID, lane_id=LANE_FAL_B)
print(f"Lane confirmed: {lane.lane_id} ({lane.direction} {lane.product}, "
      f"home={lane.home_market_role}, foreign={lane.foreign_market_role})")

REPO_ROOT = Path(__file__).resolve().parent.parent
jsonl_path = REPO_ROOT / "data" / "research" / "fal_b_ferrosilicon_discoveries_2026-09-17.jsonl"
results = ingest_external_discoveries(jsonl_path, project_id=PROJECT_ID, lane_id=LANE_FAL_B)
print(f"Ingested {len(results)} raw discovery rows (all forced to CLAIM/unverified).")

run = ResearchRun(
    run_id="fal-b-ferrosilicon-live-2026-09-17",
    project_id=PROJECT_ID,
    lane_id=LANE_FAL_B,
    query_set_version="claude-manual-v1",
    objective="Identify candidate foreign BUYER entities (foundries, steel mills, importers, "
              "traders) for ferrosilicon export (FAL-B) across Gulf/UAE and global B2B "
              "directories, via live public web search.",
    created_at=datetime.now(timezone.utc).isoformat(),
)

store = ResearchLabStore(root=REPO_ROOT)
outcome = process_discovery_batch(run, results, store=store)

print(f"\nGroups: {len(outcome.groups)} | Entities resolved: {len(outcome.entities)} | "
      f"Verification queue: {len(outcome.verification_queue)}")
print(f"Source diversity: {outcome.metrics.source_diversity}")

print("\n--- Entities (resolution_state / classification) ---")
class_by_id = {c.entity_candidate_id: c for c in outcome.classifications}
for e in outcome.entities:
    c = class_by_id.get(e.candidate_id)
    print(f"- {e.normalized_name!r}: resolution={e.resolution_state}, "
          f"category={c.category if c else 'n/a'}, reason={e.reason}")

print("\n--- Verification queue (ranked) ---")
for item in outcome.verification_queue:
    print(f"- entity={item.entity_candidate_id} score={item.score:.3f} "
          f"requirement={item.requirement} reason={item.reason}")

print(f"\nPersisted under: {store.root}")
