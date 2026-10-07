# EICO Reverse Commercial Graph — Seed v1 — 2026-10-07

## Breakthrough
Public trade-data surfaces expose both outbound and inbound named-party edges around Esfarayen Industrial Complex. These are discovery-grade evidence, not a complete or canonical customs ledger.

### Outbound
Volza profile reports 109 export shipments to 11 buyers and exposes a sample 2024 shipment of 23,960 kg FORGED ALLOY STEEL ROD to GUNES METALURJI VE KIMYA TICARET LTD in Turkey. A separate HS7228 page reports EICO among active Iranian exporters and 11 buyers.

### Inbound
A separate Volza EICO profile reports 35 imports from one Turkish supplier, Gunes Metallurgy and Chemical Trade Limited Company, under HS7228, updated 2026-10-03. Its supplier profile exposes a sample shipment to EICO for round alloy steel bar 10–80 mm, 705 kg.

This creates a potentially bidirectional Gunes/EICO commercial chain, but exact shipment dates/product families must be bound before classifying recurrence or current supplier state.

### Source conflict / entity resolution warning
Different trade-data profiles report materially different shipment/buyer counts for EICO. Eximpedia also exposes inconsistent-looking destination/customer aggregation. Treat counts as source-scoped observations, not canonical totals. This is a useful entity-resolution benchmark target.

## New commercial discovery hypothesis
The strongest next lane is no longer generic company search:
EICO -> named historical buyer/trader -> buyer's other suppliers/products -> lookalike buyers -> application graph.

Parallel lane:
named supplier/trader -> represented mills/origins -> other Iranian buyers -> competing material routes -> import-substitution candidates.

## Falsification
Do not infer current relationship from historical shipment.
Do not infer end-user from trader.
Do not infer exact grade from HS7228.
Do not infer EICO manufactured every exported line.
Do not merge similarly named EICO profiles without identity evidence.
