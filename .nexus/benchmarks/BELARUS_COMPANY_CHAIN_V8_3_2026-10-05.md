# NEXUS v8.3 — Belarus Company-Level Missing-Node Resolution

Date: 2026-10-05
State: EVIDENCE CAPTURED / PARTIAL COMPANY-LEVEL CHAIN

## Repository gate
CI #1074 on prior v8.2 head 011844d85c616dce1f31defff05b98bfd11d5155: SUCCESS.

## Company-level nodes discovered from public evidence

### MetPromKo (Belarus) — STOCKIST / COMMERCIAL SUPPLIER CANDIDATE
Public Belarus product page lists hot-rolled round 70 mm 40ХН2МА, length 2–6 m, with status "Есть в наличии" and a displayed per-ton price.
Evidence: https://metpromko.by/prod-krchrn720
Classification: CANDIDATE stockist/commercial supplier. Current web stock page supports a stock claim at observation time, but does not establish origin, upstream supplier, import record, or a link to the China→Belarus aggregate flow.

### Gidrolast Belarus — DOWNSTREAM INDUSTRIAL USER / MANUFACTURING SIGNAL
Belarus-facing official catalogue states hydraulic-cylinder honed tubes can use 42CrMo4, 40X and 30ХГСА and names OVAKO, STRUCTO and STELMI as producers for those special materials.
Evidence: https://by.gidrolast.com/ru/catalog/gidrotsilindry/gidrotsilindry-dlya-spetstransa/
Classification: CANDIDATE downstream industrial user/manufacturer for special-steel inputs. This does NOT establish purchase from China, MetPromKo, or the benchmark shipment flow.

### Bel TFI — DOWNSTREAM MANUFACTURING/APPLICATION SIGNAL
Official Belarus company page states industrial knives/bending tools may be made from 42CrMo4 and describes Belarus manufacturing activity.
Evidence: https://tfi.by/ru/%D0%BF%D1%80%D0%BE%D0%BC%D1%8B%D1%88%D0%BB%D0%B5%D0%BD%D0%BD%D1%8B%D0%B5-%D0%BD%D0%BE%D0%B6%D0%B8/
Classification: CANDIDATE downstream application/manufacturer. No upstream supplier edge established.

### Mozyr Oil Refinery — DEMAND / END-USE SIGNAL
A 2026 procurement listing includes a Siemens turbine oil-pump driving wheel specified as 42CrMo4+QT.
Evidence: https://energybase.ru/tender/01a03d64-9b50-7216-ba38-e4309162560f
Classification: VERIFIED demand signal for a 42CrMo4+QT component at named Belarus buyer/end-user level; it does not prove procurement of raw 42CrMo4 bar.

## Chain state after resolution
China → Belarus alloy-steel flow: VERIFIED MARKET-LEVEL SIGNAL.
MetPromKo → stocks/offers 40ХН2МА round: CANDIDATE company-level stock node.
Gidrolast → uses/specifies special steel including 42CrMo4 in hydraulic-cylinder products: CANDIDATE downstream-use node.
Bel TFI → 42CrMo4 industrial tooling application: CANDIDATE downstream-use node.
Mozyr Oil Refinery → procurement demand for 42CrMo4+QT turbine component: VERIFIED DEMAND SIGNAL.

## Explicitly unproven edges
China exporter → MetPromKo: UNKNOWN.
China exporter → Gidrolast: UNKNOWN.
MetPromKo → Gidrolast: UNKNOWN.
MetPromKo → Bel TFI: UNKNOWN.
Any benchmark shipment → Mozyr Oil Refinery: UNKNOWN.

## Commercial finding
v8 chain-first discovery exposed named stock/demand/application nodes that a country-flow-only result does not contain. This is discovery/coverage gain, not yet a verified supplier→buyer chain or commercial outcome gain.

## Next missing-node searches
1. Bind a named exporter/importer pair to a relevant Belarus shipment.
2. Identify legal identity and role for MetPromKo and whether stock origin is evidenced.
3. Find procurement/supplier references for Gidrolast / Bel TFI where public.
4. Search Belarus tenders for raw bar/forging demand, not merely finished components.
