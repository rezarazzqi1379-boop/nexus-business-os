# Steel Intelligence Expansion v6 — 2026-10-07
Status: RESEARCHED + IMPLEMENTED / PENDING CI

## Verified candidates
- UN/CEFACT spec-untp: official organization repository, currently archived. Mill Test Report credential work demonstrates issuer/status/certificate/product/heat/inspection structured provenance. PATTERN DONOR, not runtime dependency.
- jjakubow/pdm-steel-datasets: public benchmark code tied to TCM predictive-maintenance datasets. Use as BENCHMARK DATA only; synthetic/benchmark anomaly is not customer demand.
- opencdd/opencdd-ruby: active public project with same-day 2026-10-07 surfaced commit; IEC CDD / 61360 / 62656-oriented typed dictionary validation. STUDY/SANDBOX candidate for future component/BOM dictionary, not installed runtime.
- scroberts/Engineering-Materials-Database: active schema-validated engineering reference dataset. RESEARCH REFERENCE candidate; not standards authority and not an equivalence engine.

## New governed graph
Customer/Plant → Process → Equipment → Component → Failure/Wear → Part → Spec/Grade → MTC/Heat → Supplier → Trade Relationship → Procurement Trigger → Buyer Role.
Edges are OBSERVED, DERIVED or HYPOTHESIS. Only OBSERVED current evidence can support current-demand promotion.

## Grade rule
Designation similarity, chemistry similarity, clustering, third-party crosswalk or a material database entry must never be represented as official grade equivalence. Equivalence requires the governing standard/specification and application acceptance criteria.

## Digital MTC direction
Future proof should separate:
1. extraction accuracy,
2. issuer/document authenticity,
3. heat/lot traceability,
4. standard compliance,
5. commercial acceptance.
Passing one does not imply the others.
