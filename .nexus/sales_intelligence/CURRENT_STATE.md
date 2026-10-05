# NEXUS Steel Sales Intelligence — Current State

Updated: 2026-10-05
Owner: ASAK TEJARAT FATER
Execution owner: chatgpt-nexus
Status: ACTIVE_RESEARCH

## Mission
Build an evidence-led sales/export engine for Esfarayen-origin forged/alloy steel products. Discover and qualify buyers, channels, competitors, trade flows, decision makers, customs/compliance constraints, and sales opportunities without treating unverified claims as facts.

## Active markets
Turkey, Iran, Kazakhstan, Russia, Belarus, Tajikistan, Armenia, Oman.

## Product families in scope
20MnCr5/related case-hardening grades; 42CrMo4/related Q&T grades; 8620; C15; C45/CK series; S355J2G3; St52; other forged/alloy steel only when canonical product evidence supports it.
Grade equivalence is never assumed. Standard, condition, chemistry/mechanical properties, dimensions and MTC must be checked.

## Pipeline
live discovery -> company evidence -> material/application evidence -> trade evidence -> product/dimension fit -> competitor/channel classification -> compliance gate -> Apollo free organization resolution -> buyer score -> spend gate -> contact enrichment -> human-approved outreach -> RFQ -> quote -> negotiation -> PO.

## Current evidence-backed operating decisions
- Apollo is a resolver/enrichment/CRM layer, not the sole discovery engine.
- Free Apollo organization lookup is preferred before paid enrichment.
- Paid enrichment requires a spend gate.
- Russia and Belarus require an additional entity/bank/goods/end-use/route/carrier/payment compliance gate before consequential outreach or transaction work.
- End users with explicit material/application evidence outrank generic steel traders for buyer qualification.
- Buyer Fit and Enrichment Spend Confidence are separate scores.
- No external message, quote, order, payment, signature, deployment, merge, or irreversible action is authorized by this file.

## Apollo validation
Organization enrichment validated for Naci Uyar Demir Celik and Salda Metal.
Free organization resolution validated for Erkal Haddecilik, Efor Celik, Hur Celik, Modulsan and ReWeld.
Generic industry phrases produced false negatives; discover names/domains elsewhere first.

## Known candidate patterns
Turkey: gear/gearbox users (8620/20MnCr5), shaft/heavy machinery users (42CrMo4/C45), stockists/distributors, heavy forging.
Oman: machine shops/end users plus material suppliers for oil & gas/industrial maintenance.
Kazakhstan: mining/heavy machinery/repair/shaft/gear focus.
Armenia and Tajikistan: qualify with product-specific trade evidence before scale.
Russia/Belarus: technically relevant markets but compliance-separated from commercial attractiveness.

## Agent/repository adoption policy
External repositories are evidence/implementation candidates, not trusted dependencies. Review license, maintenance, credentials handling, network behavior, scraping/ToS risk, tests and rollback before adoption. Prefer adapters over copying whole systems.

## Continuity protocol
At the start of every substantial steel-sales task:
1. Read this file plus AGENTS.md and project memory.
2. Recover unresolved blockers and the last completed stage.
3. Do not re-run paid enrichment or outreach merely because context is missing.
4. Append durable evidence-backed progress to project memory/UnifiedDataHub where available.
5. Update this state when a material project decision or milestone changes.

## Next work
Build country candidate universes; add provider/capability registry for sales/trade; add deterministic buyer-fit/spend/compliance gates; qualify Tier-A companies; evaluate public agent repos in sandbox; connect approved adapters to existing NEXUS control plane; add tests; then prepare outreach packages for explicit approval.
