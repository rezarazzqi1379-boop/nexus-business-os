# PRJ-HYD-01 Live Qualification Replay — 2026-08-28

Status: INTERNAL EVIDENCE REVIEW. Vendor messages/attachments are Tier B live evidence, not canonical authority.

## Canonical buyer basis
Source: Hydrostatic_Tester_Engineering_Master_v1.1_2026-08-24
- OD 89-180 mm
- WT 6-20 mm
- length 9-12 m
- upper capability 120 MPa, duty dependent
- hold 5-10 s
- buyer throughput basis 60 pipes/hour
- signed pressure/dimension/end-condition envelope required
- one unambiguous calibrated pressure pass/fail rule required
- signed structural calculations/FEA for worst contractual axial load required
- FAT/TPI/ITP and complete tooling/scope must close before manufacturing release

## GH Petro — new 28 Aug signed evidence
Source: Gmail message `1a048bfc44a30ac6`, attachment `120Mpa 89-180mm Hydrostatic Testing Machine-20260828.pdf`.

### Supported / improved
- CLAIM/SIGNED EVIDENCE: confirms 120 MPa capability at agreed critical pipe dimensions and hold time.
- CLAIM/SIGNED EVIDENCE: states 60 pipes/hour for OD 168.3 mm at 70 or 120 MPa with 7 s hold.
- MEASUREMENT/CLAIM: supplies cycle components totaling 55 s: loading 5, alignment 5, sealing 2, filling/venting 20, pressurization 6, hold 7, depressurization 3, draining 3, unloading 4. This is internally compatible with a nominal 60/h claim if sequence assumptions hold, but FAT remains required.
- CLAIM: says plain/upset/threaded/coupled end conditions are supported.
- CLAIM: acknowledges 120 MPa FAT, ten consecutive tests, one-hour capacity and continuous operation.

### Still open / defective
- MISSING EVIDENCE: pressure sensing accuracy ±0.25% and gauge class 1.6 do not define the single contractual pressure pass/fail/stability criterion required by the master.
- MISSING EVIDENCE: the signed appendix table includes OD, thickness, length, pressure, hold and capacity but omits steel grade and end condition, so it is not the complete requested capability envelope.
- MISSING EVIDENCE: structural response is a 310 metric-ton axial-force summary plus dimensions and a promise of a certificate after contract; it is not signed calculations/FEA with worst-case load envelope and safety factor.
- DEVIATION: only three test mould sizes are included. Additional sizes cost USD 12,000 per pair/set. Therefore the complete contractual tooling scope is not included at unchanged price unless contractual sizes are intentionally limited to the included three.
- PARTIAL: standards answer uses 'latest valid API version agreed by both parties' but leaves other standards at a vague manufacturing-industry level.
- PARTIAL: FAT is simply 'confirmed'; detailed measurement methods, calibrated instruments, acceptance criteria and ITP dossier are not yet closed.
- PARTIAL/COMMERCIAL CONFLICT: row 10 says unchanged scope/price confirmed while row 6 creates extra tooling charges. Commercial scope must be reconciled before normalization.

Decision: **GH remains CONDITIONAL TECHNICAL LEAD; NOT PO-READY.**

## Marley — new 28 Aug point-by-point reply
Source: Gmail message `1a0474872759cd97`.

### Critical contradiction
- DEVIATION: Marley states guaranteed cycle time is approximately **3-4 minutes per pipe** including handling through discharge. That implies only about **15-20 pipes/hour**, which directly conflicts with the buyer basis of 60 pipes/hour and with the requested guaranteed 60 pipes/hour at high-pressure duty points.

### Other state
- CLAIM: ±0.5 MPa fluctuation at agreed duty points and ~0.2% full-scale measurement/control accuracy; FAT verification promised.
- CLAIM/PENDING: signed structural calculations are promised, not yet supplied.
- CLAIM: 120 MPa FAT, ten consecutive tests, one-hour capacity and continuous-operation test are accepted in principle.
- CLAIM: all contractual tooling included in price.
- CLAIM: complete BOM/sealing/safety/data/PLC documentation can be provided.
- COMMERCIAL: Marley keeps full balance due before shipment, despite buyer request to bind final balance to passed FAT + punch-list closure + approved documentation. Shipment is promised only after buyer inspection/confirmation; payment risk remains unresolved.

Decision: **Marley remains COMMERCIAL BENCHMARK but now has a material technical throughput deviation; NOT PO-READY.**

## Portfolio consequence
The previous 27 Aug operational state 'await signed replies' is stale. Both GH and Marley have replied. Current next action is internal normalization and blocker closure, not duplicate follow-up.

Current ranking is not final procurement authority:
1. GH: stronger on throughput claim but still incomplete on structural proof, acceptance rule, tooling/scope reconciliation and full envelope.
2. Marley: lower quoted commercial benchmark but current 3-4 min/pipe cycle materially misses 60/h buyer basis unless corrected with a different parallelized/dual-station definition and guaranteed evidence.

No vendor should be advanced to PO readiness from these messages alone.
