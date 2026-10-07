# NEXUS v8.2 — Real Multi-Hop Steel Benchmark: China → Belarus Alloy/Tool Steel

Date: 2026-10-05
State: BENCHMARK INPUT CAPTURED; commercial chain remains PARTIAL.
Purpose: test whether chain-first discovery exposes actor classes and missing nodes that a company-list search would not.

## Public evidence captured
1. WITS/UN Comtrade HS 722830 reports 2024 exports to Belarus from China: USD 159.62k / 80,630 kg; Turkey: USD 44.22k / 43,140 kg; Poland: USD 24.59k / 6,929 kg.
2. Volza public result snippets expose product-level Belarus import observations under HS 7228, including Chinese-origin forged/hot-rolled tool/alloy steel bars and multiple HS 722840 observations. Public snippets do not establish a named buyer/supplier edge without the underlying record.
3. Therefore China → Belarus alloy/tool-steel flow is an aggregate/product shipment SIGNAL, not a named-company transaction.

## Chain graph
China / exporters --[AGGREGATE_TRADE_SIGNAL]--> Belarus market : VERIFIED MARKET-LEVEL SIGNAL
China exporter --[SUPPLIED_TO]--> Belarus importer : UNKNOWN
Belarus importer --[SUPPLIED_TO]--> stockist/processor : UNKNOWN
stockist/processor --[SUPPLIED_TO]--> mill/OEM/end-user : UNKNOWN
end-user --[USES]--> project/product : UNKNOWN

## Missing-node hunter
Priority discovery targets:
- named Belarus importer/consignee for relevant 722830/722840 records;
- Chinese exporter/supplier bound to the same shipment;
- importer economic role: trader, stockist, processor, mill, OEM or end-user;
- downstream transformation/use;
- procurement/decision-maker only after company identity and role are evidenced.

## Anti-attribution rule
The WITS country flow MUST NOT create a named buyer edge. Volza snippets showing product/date/value also MUST NOT create a named company edge when buyer/supplier identity is not visible/evidenced.

## Coverage gain vs company-list approach
New actor classes explicitly searched by v8: exporter, importer/consignee, logistics/shipment, processor, stockist, downstream mill/OEM/end-user, procurement decision-maker.
This is a structural coverage gain, not yet proof of commercial outcome gain.

## Metrics
new actor classes targeted: 7
verified market-level edges: 1
verified company-level edges: 0
candidate company-level edges: 0
explicit missing-node classes: >=5
false company attribution prevented: 1 mandatory trap
commercially actionable opportunity: NOT YET VERIFIED
search cost: public web only in this benchmark cycle; no paid credits consumed.

## Evidence URLs
- https://wits.worldbank.org/trade/comtrade/en/country/All/year/2024/tradeflow/Exports/partner/BLR/product/722830
- https://www.volza.com/p/iron-or-or-steel-or-article/hsn-code-7228/import-data/imports-in-belarus/

## Benchmark conclusion
v8 improves discovery STRUCTURE by converting an aggregate market signal into explicit missing-node searches across the chain. It has not yet demonstrated better real commercial conversion or a verified named-company chain. Next benchmark step is company-level shipment/entity resolution using lawful accessible evidence, followed by downstream role and use tracing.
