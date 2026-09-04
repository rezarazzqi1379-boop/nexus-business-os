# research_lab/

File-backed shared environment for `research_lab.py`'s `ResearchLabStore`. JSON for run
metadata and derived reports, JSONL for the append-only raw-candidate log. No database.

This directory (and everything `research_lab.py` writes) is project/lane-neutral: it holds
whatever `project_id`/`lane_id` a run declares, without interpreting what those values mean.
Project/lane authority (e.g. what lanes a given project has, what may or may not cross
between them) belongs to a separate, not-yet-built policy layer.

## Implemented (backed by `ResearchLabStore` methods)

- `runs/<run_id>.json` — one `ResearchRun`'s identity/config (`create_run`, `read_run`).
- `candidates/<run_id>.jsonl` — the immutable, append-only raw-discovery log for a run
  (`append_candidates`, `read_candidates`).
- `scores/<run_id>.json` — the materialized ranked-opportunity report for a run
  (`write_score_report`), produced by `rank_opportunities`/`run_summary` over already-persisted
  candidates. Never written by `append_candidates` itself.
- `benchmarks/<provider_id>__<evaluated_at>.json` — one provider's measured
  `ResearchProviderBenchmark` record (`write_benchmark`), gated by `ResearchBenchmarkPolicy`.

## Reserved, not yet implemented

These pipeline stages need either a live search provider or an LLM classifier, neither of
which this slice ships (see `research_evidence.py`'s `NullSearchProvider` for why: no
provider is accepted merely for existing, and none has been benchmarked yet).

- `sources/` — normalized per-provider raw page/document dumps prior to entity extraction.
- `entities/` — resolved entity records (post entity-extraction and entity-resolution).
- `reports/` — synthesized decision packs (depends on `entities/` and a verification queue).

Task handoffs are **not** duplicated here — they continue to live in `.nexus/handoffs/` via
`task_handoff.py`'s `HandoffStore`, which already covers that concern; this directory
intentionally has no `handoffs/` subdirectory of its own.
