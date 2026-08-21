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
| Wuxi Marley Technology / Eli | Direct manufacturer/seller channel | Wuxi Marley Machinery Technology Co., Ltd., Wuxi, Jiangsu | Received 11-page technical solution: OD 89–180; 6–12 m; 5–12 mm; 0–120 MPa; 5–30 s adjustable; EXW USD 238,461.55; 90-day manufacture; 2-year warranty. Official Marley machinery site independently lists the same Eli email/phone, Wuxi address and hydro-testing-machine product category, and states the company integrates R&D, production and sales. | IDENTITY VERIFIED; no proven collision | Technical clarification only: throughput/cycle, 260 kVA vs 30 kW, pressure envelope vs pipe ID/OD, axial restraint basis, references/FAT |
| Yaxing / Alisa (yxgd.com.cn; yaxingmachines.com) | Direct manufacturer/seller channel | Dezhou Yaxing Steel Tube Equipment Factory, Dezhou, Shandong | Alisa quoted CNY 3,400,000 FOB Tianjin and 1 pc/min. Official Yaxing site uses Alisa's yxgd.com.cn email and Dezhou factory address, describes Yaxing as a hydrotester manufacturer with its own R&D team, states up to 150 MPa and about 50–60 s/cycle for customized hydrotesters. A third-party supplier profile also names Dezhou Yaxing Steel Tube Equipment Factory as manufacturer established in 1996. | IDENTITY VERIFIED; no proven collision | Request project-specific guarantee: 120 MPa envelope for OD/ID/wall, 6–12 m range, axial-force/end-restraint capacity, exact cycle at our parameters, lead time, payment, FAT, Iran support |
| Yedi Mavi / Ali Mahdian | Sourcing agent | Turkish specialist/OEM identity not disclosed | Reports no Turkish manufacturer capable of complete 120 MPa pipe hydrotester; says Turkish practical complete-machine ceiling around 500 bar; reports another party contacted same specialist | POSSIBLE CHANNEL COLLISION | Do not broaden outreach yet. Require identity of contacted specialist/OEMs before authorization; compare against registry |
| ANZ Global | Sourcing/integration channel | Not yet disclosed | Evaluating prospective OEMs; requested confirmed technical inputs | UNRESOLVED | Require OEM/manufacturer disclosure before further parallel RFQ distribution |
| SinoQAT | Sourcing/QC channel | Not yet disclosed | States it has a channel to handle Iran; commercial model benefits from closed order | UNRESOLVED | Require proposed OEM identity before supplier contact; run dedup check first |
| GH Petro | Direct manufacturer / turnkey OCTG-equipment channel | GH-Petro (official site states founded 2004; China) | Official site describes GH-Petro as a steel pipe/tube mill manufacturer and explicitly lists hydro-testers within full OCTG production-line supply. Product pages show multiple hydrotester configurations, including 60–168 mm / 70 MPa, 60–219 mm / 80 MPa, 114–219 mm / 80 MPa and other customized configurations. | MANUFACTURER STATUS VERIFIED; 120 MPa capability for our exact range NOT VERIFIED | Treat as direct OEM candidate. Request exact 89–180 mm / 6–12 m / 5–12 mm / 120 MPa capability envelope and commercial proposal; do not treat generic 70–80 MPa catalogue models as proof of 120 MPa |

## Evidence classification

### Facts supported by received documents/emails

- Marley supplied a technical solution explicitly describing a 120 MPa machine for OD 89–180 mm and 6–12 m pipe length.
- Marley quoted EXW USD 238,461.55 plus USD 23,077 for installation/training.
- Alisa/Yaxing stated a budgetary price around CNY 3,400,000 FOB Tianjin and test efficiency of 1 pc/min.
- Yedi Mavi reported that another party had already contacted the same Turkish specialist about the same requirement.

### Facts independently verified from public manufacturer sources

- Marley maintains hydro-testing-machine product pages and lists the same Eli contact details and Wuxi address as the received quotation channel.
- Yaxing publicly identifies itself as a hydrotester manufacturer in Dezhou, uses Alisa's yxgd.com.cn email, and states customized hydrotester capability up to 150 MPa with about 50–60 seconds per cycle as a general product claim.
- GH-Petro publicly identifies itself as a steel pipe/OCTG equipment manufacturer and lists hydrotesters among its manufactured line equipment; public product pages show several 70–80 MPa catalogue configurations.

### Claims requiring independent/project-specific verification

- Yedi Mavi's statement that no Turkish manufacturer can build a complete 120 MPa pipe hydrotester and that the practical Turkish ceiling is around 500 bar.
- Any supplier claim of continuous 120 MPa capability across the entire OD range without a pressure/ID/axial-force envelope.
- Yaxing's general public statement of maximum 150 MPa does not prove 120 MPa at every pipe size in our project.
- GH-Petro manufacturer status is verified, but 120 MPa capability for the required 89–180 mm range is not yet verified.

### Unknowns blocking clean comparison

- Exact required test pressure by pipe OD/ID and grade.
- Required production throughput/cycle time. The earlier 40–60 pipes/min figure is not accepted as a hydrotester requirement until engineering reconfirms it.
- Pipe-end geometry and sealing interface.
- Required governing standard/API acceptance criteria and pressure-recording/FAT protocol.
- Underlying OEM identities for intermediary channels (Yedi Mavi, ANZ Global, SinoQAT).

## Procurement gate

No new intermediary may distribute this RFQ to an undisclosed supplier without first returning at least the proposed OEM legal name and domain/factory identity for collision checking.

This gate does not block direct technical clarification with already identified candidate manufacturers.

## Next verification target

Resolve the remaining intermediary-backed OEM identities before any new broad RFQ distribution. Direct technical clarification may continue with Marley, Yaxing and GH-Petro because their manufacturer status is now independently supported; project-specific pressure capability remains separately gated.