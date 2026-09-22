> **INTERNAL ONLY — DO NOT SEND TO ANY VENDOR OR THIRD PARTY.** This document exists solely as an internal audit record. It must never be copied, pasted, or merged into any RFQ, RFI, or other vendor-facing document. If any vendor-facing draft is found to reference this document or its contents, treat that as a release blocker until removed.

# Internal QA Log — Historical Naming-Risk Note (2026-09-22)

## Background

The first version of the Chinese-language RFQ draft (`RFQ_DRAFT_ZH_2026-09-22.md`, v1) contained Chinese company names for several suggested recipients that had been back-translated from English names rather than sourced from verifiable records. One of these back-translated names was highly similar to the name of a large, entirely unrelated real enterprise:

- **Back-translated (incorrect) name used in v1 for a suggested DC-motor recipient:** 上海东方电气
- **Risk:** This string is highly similar to the name of a large, well-known Chinese electrical-equipment enterprise group that is unrelated to the supplier the sourcing study intended to reference. Sending an RFQ using this name, or a company-lookup using this name, could misdirect an inquiry to the wrong company or create a false impression of association.

## Corrective action taken

- v2 of the Chinese RFQ removed all back-translated Chinese names and replaced them with the English names as sourced, marked "中文名称待核实" (Chinese name pending verification).
- A caution note referencing "上海东方电气" was carried in the v2/v3 RFQ drafts as a **warning to the preparer**, instructing that this name must not be confused with the correct recipient.
- **Round-3 review (2026-09-22) correctly identified that this warning note, despite being framed as a caution, still placed a real, unrelated company's name inside a document intended to eventually be sent to a vendor.** This is a residual brand/misdirection risk regardless of framing, and was removed from all vendor-facing documents.

## Current state (v4, this date)

- None of the 8 split Pre-RFQ/RFI documents (`RFQ-FURNACE`, `RFQ-DC-MOTOR-DRIVE`, `RFQ-REVERSING-STAND`, `RFQ-MAIN-GEARBOX`, EN + ZH each) contain the string "上海东方电气" or any back-translated Chinese company name.
- The verified/sourced suggested recipient for the DC motor item is listed in English only, with an instruction to verify the legal Chinese name independently before any send, and a general caution (without naming the confusable company) to verify the name carefully.
- This QA log is the only document in the project where "上海东方电气" appears, and it is explicitly marked internal-only.

## Action item before any future recipient-name work

Any Chinese company name added to a future vendor-facing document must be sourced from a verifiable primary source (company website, official registry, or a document the preparer can cite) — never back-translated from an English name by inference. If a name cannot be verified this way, it stays out of vendor-facing text and is listed as "pending verification" with the English name only, as done in v2 onward.
