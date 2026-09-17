"""Second FAL-A (ferromanganese import, foreign SUPPLIER) discovery run -- this one combines the
original single-provider batch (claude-web-search-manual, 2026-09-17) with a genuinely independent
second provider (exa-agent-run, via the newly-connected Exa plugin's agent_run tool) covering new
geographies (China, South Africa, India, Kazakhstan, Malaysia, Norway) not searched in the first
pass. This is the first FAL run with real multi-provider source diversity rather than a single
provider labeled once -- directly testing whether the pipeline's fail-closed scoring behaves
differently (promotes anything further) once genuine independent-source corroboration exists.

Still does NOT contact, message, or open an account with any of the discovered entities. Persists
them as unverified CLAIM-level discovery candidates for later human review only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fal_vertical import assert_lane_scope, PROJECT_ID, LANE_FAL_A
from discovery_pipeline import ingest_external_discoveries, process_discovery_batch
from research_lab import ResearchRun, ResearchLabStore

lane = assert_lane_scope(project_id=PROJECT_ID, lane_id=LANE_FAL_A)
print(f"Lane confirmed: {lane.lane_id} ({lane.direction} {lane.product}, "
      f"home={lane.home_market_role}, foreign={lane.foreign_market_role})")

REPO_ROOT = Path(__file__).resolve().parent.parent

original_path = REPO_ROOT / "data" / "research" / "fal_a_ferromanganese_discoveries_2026-09-17.jsonl"
exa_path = REPO_ROOT / "data" / "research" / "fal_a_ferromanganese_discoveries_exa_2026-09-17.jsonl"

original_results = ingest_external_discoveries(original_path, project_id=PROJECT_ID, lane_id=LANE_FAL_A)
exa_results = ingest_external_discoveries(exa_path, project_id=PROJECT_ID, lane_id=LANE_FAL_A)
combined_results = original_results + exa_results
print(f"Ingested {len(original_results)} rows from claude-web-search-manual "
      f"+ {len(exa_results)} rows from exa-agent-run = {len(combined_results)} total "
      f"(all forced to CLAIM/unverified).")

run = ResearchRun(
    run_id="fal-a-ferromanganese-live-multiprovider-2026-09-17",
    project_id=PROJECT_ID,
    lane_id=LANE_FAL_A,
    query_set_version="claude-manual-v1+exa-agent-run-v1",
    objective="Identify candidate foreign SUPPLIER entities for ferromanganese import (FAL-A) "
              "combining an initial manual web-search pass with a genuinely independent "
              "exa-agent-run pass covering China/South Africa/India/Kazakhstan/Malaysia/Norway, "
              "to test real multi-provider source diversity for the first time in this project.",
    created_at=datetime.now(timezone.utc).isoformat(),
)

store = ResearchLabStore(root=REPO_ROOT)
outcome = process_discovery_batch(run, combined_results, store=store)

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
