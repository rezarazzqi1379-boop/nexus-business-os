# Hydrostatic Tester Source Map — 2026-08-21

Status: ACTIVE
Scope: OCTG/steel-pipe hydrostatic tester, approx. OD 89–180 mm, pipe length 6–12 m, wall thickness 5–12 mm, hold 5–10 s, target maximum machine rating up to 120 MPa.

## Control rule

A sourcing lead is not counted as a new supplier until the underlying OEM/manufacturer identity is resolved.

Before any new outreach:

1. Resolve legal manufacturer/OEM name where possible.
2. Normalize manufacturer domain, factory location, brand, model family, contact details and catalogue evidence.
3. Compare against the supplier registry.
4. If the same OEM/domain/identity is already present: `HOLD_DUPLICATE_SOURCE`.
5. If location + model overlap suggests a collision but identity is not proven: `REVIEW_POSSIBLE_COLLISION`.
6. Agents/referrers are channels, not unique OEMs.
7. Do not grant an intermediary exclusive project ownership without an explicit commercial decision.

## Current map

| Channel | Role | Underlying OEM / factory | Evidence currently known | Collision status | Next action |
|---|---|---|---|---|---|
| Wuxi Marley Technology / Eli | Direct-looking manufacturer/seller channel | WUXI MARLEY TECHNOLOGY CO., LTD (as stated in technical solution) | 11-page technical solution; OD 89–180; 6–12 m; 5–12 mm; 0–120 MPa; 5–30 s adjustable; EXW USD 238,461.55; 90-day manufacture; 2-year warranty | No proven collision yet | Technical clarification: throughput/cycle, 260 kVA vs 30 kW, pressure envelope vs pipe ID/OD, axial restraint basis, references/FAT |
| Yaxing/Karat / Alisa (yxgd.com.cn) | Direct manufacturer/seller channel claimed through catalogue/site | Yaxing/Karat identity needs legal-name confirmation | Budgetary price CNY 3,400,000 FOB Tianjin; stated efficiency 1 pc/min; customized machine | No proven collision yet | Obtain legal manufacturer name, factory address, guaranteed pressure envelope, 6–12 m confirmation, axial force, lead time, payment, Iran support |
| Yedi Mavi / Ali Mahdian | Sourcing agent | Turkish specialist/OEM identity not disclosed | Reports no Turkish manufacturer capable of complete 120 MPa pipe hydrotester; says Turkish practical complete-machine ceiling around 500 bar; reports another party contacted same specialist | POSSIBLE CHANNEL COLLISION | Do not broaden outreach yet. Ask for identity of contacted specialist/OEMs before authorizing further sourcing; compare identities to registry |
| ANZ Global | Sourcing/integration channel | Not yet disclosed | Evaluating prospective OEMs; requested confirmed technical inputs | UNRESOLVED | Require OEM/manufacturer disclosure before further parallel RFQ distribution |
| SinoQAT | Sourcing/QC channel | Not yet disclosed | States it has a channel to handle Iran; commercial model benefits from closed order | UNRESOLVED | Require proposed OEM identity before supplier contact; run dedup check first |
| GH Petro | Supplier/integration channel | Not yet resolved in this snapshot | Existing hydrotester correspondence | UNRESOLVED | Resolve legal OEM/factory and domain before next outreach |

## Evidence classification

### Facts supported by received documents/emails

- Marley supplied a technical solution explicitly describing a 120 MPa machine for OD 89–180 mm and 6–12 m pipe length.
- Marley quoted EXW USD 238,461.55 plus USD 23,077 for installation/training.
- Alisa/Yaxing stated a budgetary price around CNY 3,400,000 FOB Tianjin and test efficiency of 1 pc/min.
- Yedi Mavi reported that another party had already contacted the same Turkish specialist about the same requirement.

### Claims requiring independent verification

- Yedi Mavi's statement that no Turkish manufacturer can build a complete 120 MPa pipe hydrotester and that the practical Turkish ceiling is around 500 bar.
- Any supplier claim of continuous 120 MPa capability across the entire OD range without a pressure/ID/axial-force envelope.
- Manufacturer status of any channel until legal entity/factory evidence is confirmed.

### Unknowns blocking clean comparison

- Exact required test pressure by pipe OD/ID and grade.
- Required production throughput/cycle time. The earlier 40–60 pipes/min figure is not accepted as a hydrotester requirement until engineering reconfirms it.
- Pipe-end geometry and sealing interface.
- Required governing standard/API acceptance criteria and pressure-recording/FAT protocol.
- Underlying OEM identities for intermediary channels.

## Procurement gate

No new intermediary may distribute this RFQ to an undisclosed supplier without first returning at least the proposed OEM legal name and domain/factory identity for collision checking.

This gate does not block direct technical clarification with already identified candidate manufacturers.
