# NEXUS CONTINUE v10.19 — LIVE TENDER SPEC RESOLVER + OCDS COVERAGE BENCHMARK

Continue from latest valid state.

FIRST resolve latest CI.
GREEN -> procurement_adapter_gate + deep-search regressions -> TESTED.
RED -> exact failure -> minimal fix -> regression -> rerun. NO EXPANSION ON RED.

MEASURED v10.18:
Fresh auditable EICO stock rows = 0/8.
Current-open procurement leads retained = 2.
Current-open named + exact large geometry = 1: RINL GEM/2026/B/8049767.
RINL exact grade mapping = UNRESOLVED.
Current-open named + exact geometry + verified 42CrMo4 = 0.
PGO ~120t 42CrMo4 future-demand watch = 1.
EICO relationship refs = 0.
EVIDENCE_READY = 0.
OCDS GitHub candidates = 3; integrated = 0.

MISSION:
Resolve high-information live tender specifications first. Benchmark open procurement-data tooling only where it adds measurable unique qualified evidence.

1 CI GATE.
2 RINL SPEC RESOLUTION: retrieve/resolve BOQ + specification for GEM/2026/B/8049767. Map each forged-round row to grade, diameter, length, qty, standard, condition, UT/NDT, certificate and origin/eligibility. No inferred grade.
3 RINL FIT: compare only resolved grades/geometry against EICO capability; current stock remains UNKNOWN until fresh confirmation.
4 TN BHEL SPEC: resolve GEM/2026/B/8093618 only if technical docs become accessible; otherwise keep missing-spec.
5 PGO WATCH: search new notices tied to planned 42CrMo4 purchases; dedup historical plan from actual new RFQ.
6 STOCK INTAKE: validate any fresh EICO confirmation through all 11 required fields.
7 LIVE DEMAND: deep-search current/open named buyer + exact geometry + exact grade. Closed tenders are DNA/history only.
8 OCDS COVERAGE BENCHMARK: identify target procurement publishers used by NEXUS; measure which publish OCDS. Run adapter_decision using coverage, incremental qualified hits and maintenance cost. No install on HOLD.
9 GITHUB RESEARCH: inspect upstream activity/license/security/fit for only benchmark-surviving adapter. Prefer official Open Contracting repos.
10 TECHNICAL ACCEPTANCE: standard/edition, HT, chemistry, mechanics, UT/NDT, machining, certificate, origin.
11 RELATIONSHIP: exact EICO/Esfarayen relationship evidence only.
12 RED TEAM: tender title->grade; category->spec; cached active->currently open; geometry->technical fit; capability->stock; popular repo->needed integration; OCDS availability->useful coverage.
13 MEASURE: resolved live tender rows; verified grade+geometry leads; fresh stock rows; technical accepts; relationship refs; unique evidence gain from adapter benchmark; EVIDENCE_READY.
14 PERSIST GitHub + Notion + Drive with read-back where exact authority exists. Generate v10.20 from measured bottleneck.

NO OUTREACH. NO PAID CREDIT. NO MERGE. NO PRODUCTION DEPLOY. COMMERCIAL OUTCOME = UNPROVEN.
