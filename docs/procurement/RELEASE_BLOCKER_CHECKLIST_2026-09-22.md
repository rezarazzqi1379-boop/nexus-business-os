# Release-Blocker Checklist — Before Any Pre-RFQ/RFI Document Is Sent (v4, 2026-09-22)

Status: **NOTHING HAS BEEN SENT. NOTHING SHOULD BE SENT UNTIL THIS CHECKLIST IS CLEARED AND YOU GIVE EXPLICIT APPROVAL.**

## A. Blockers that must clear before ANY document is sent to ANY vendor

- [ ] **Legal identity verification.** For each suggested recipient, confirm legal company name, unified social credit code (统一社会信用代码), and registered status via China's national enterprise credit information system (国家企业信用信息公示系统) or an equivalent verified source. Not yet done for any recipient — the sourcing study's names are unverified.
- [ ] **Explicit send approval from you**, per document, per recipient. Verified identity is a precondition, not a substitute, for this approval.
- [ ] **No historical-warning content in the outgoing copy.** Before sending, re-grep the exact file being sent for "上海东方电气" and the other 4 previously-fabricated names, to catch any accidental reintroduction from copy-paste or template reuse. (Currently: zero occurrences confirmed in all 8 v4 documents, per `RFQ_BILINGUAL_PARITY_MATRIX_2026-09-22.md`.)
- [ ] **Sender company details filled in.** All 8 documents currently have `[Reza / ATF — company details to be inserted before sending]` as a placeholder — this must be completed with real, approved company information before send.
- [ ] **Ref number finalized.** All 8 documents use a placeholder ref (`PRE-RFQ-STEEL-<ITEM>-2026-09-XX`) — the `XX` must be assigned before send.

## B. Blockers specific to upgrading from Pre-RFQ/RFI to a formal RFQ round

These do not block sending the *current* Pre-RFQ/RFI documents (which exist precisely to gather the information below), but they block treating any response as comparable, formal RFQ pricing:

- [ ] Final billet/bloom/slab cross-section and grade fixed on our side.
- [ ] Pass schedule fixed (or at least the governing pass parameters) so vendor speed/torque/power responses can be checked against our own engineering basis.
- [ ] Required throughput (t/h and, for the furnace, kg/(m²·h)) fixed.
- [ ] Acceptance criteria (FAT/SAT/performance-test basis) defined well enough to be stated consistently across all vendor responses.

## C. Item-specific unresolved technical questions (informational — not a hard blocker to sending an RFI, since resolving them is partly the purpose of the RFI)

- [ ] Gearbox ratio: is the broker's 25:1 a rough-stand ratio (plausible) or a mismatch? — Being put to vendors via the A/B/C question in `RFQ-MAIN-GEARBOX_*`.
- [ ] "Center 600 mm": which physical parameter does this refer to? — Being put to the stand vendor via `RFQ-REVERSING-STAND_*`; remains UNKNOWN until equipment nameplate/GA drawing is available.
- [ ] "35 tons": which parameter does this refer to? — Explicitly reframed as undefined/unranked in the manager report v4; not resolvable without a nameplate or packing list.
- [ ] Furnace ~30 t/h estimate: screening hypothesis only, not usable for design or budget until Heat Balance / Charging Pattern / Residence Time data is available from a real candidate furnace.

## D. Company/PRJ-CAN-01 item (separate, unrelated project — reminder, not a blocker for this project)

- [ ] Two attachments for the unrelated can-forming sourcing project (`NEXUS_Claude_Deep_Sourcing_Execution_Pack_v1.0.zip`, `NEXUS_Claude_Industrial_Sourcing_Pack_v1.0_FA.docx`) remain unopened and unreviewed, pending your explicit go-ahead, including their noted internal version conflict (Master Context v1.9 vs v2.1; Source Registry v1.6 vs v1.8).

## Summary

**Recommended next action, per your own stated decision:** do not approve sending. Proceed to company legal-identity verification first. Only after that, and only with your explicit approval, send the split Pre-RFQ/RFI documents (not the old combined document, which is superseded).
