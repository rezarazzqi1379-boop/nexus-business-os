# Bilingual Parity Matrix — Split Pre-RFQ/RFI Documents (2026-09-22, v4)

Confirms that each EN/ZH document pair among the 4 split Pre-RFQ/RFI documents requests the **same substantive information**, field by field. This matrix was built by reproducing the round-3 review's parity objection directly against the combined v3 files first (see `CHINA_SOURCING_STUDY_2026-09-22_v4_ADDENDUM.md`, Section 9, Point 2), then verifying that every field present in either language of the split v4 documents is also present in the other.

## Method

1. Every technical bullet/ask in each ZH v3 item was checked against the corresponding EN v3 item — direction ZH→EN.
2. Every technical bullet/ask in each EN v3 item was checked against the corresponding ZH v3 item — direction EN→ZH (to catch gaps in the other direction).
3. Gaps found were translated and inserted into the missing-language version when building the v4 split documents.
4. Each v4 split document pair was re-checked field-by-field after drafting (this table).

## Result of the v3 gap check

| Direction | Gaps found |
|---|---|
| ZH → EN (in ZH, missing from EN) | 5 (furnace kg/(m²·h); motor continuous-power basis; stand roughing/finishing + line speed; gearbox roll-speed-at-ratio; business license copy) |
| EN → ZH (in EN, missing from ZH) | 0 |

## Field-by-field parity — v4 split documents

### RFQ-FURNACE (EN / ZH)

| Field | EN | ZH |
|---|---|---|
| Furnace type, dimensions | ✅ | ✅ |
| Cold/hot capacity t/h | ✅ | ✅ |
| Specific throughput kg/(m²·h) | ✅ (added) | ✅ |
| Design billet/bloom/slab size & grade | ✅ | ✅ |
| Entry/exit temperature range | ✅ | ✅ |
| Fuel type & heating value | ✅ | ✅ |
| Specific energy consumption | ✅ | ✅ |
| Oxidation/scale-loss guarantee | ✅ | ✅ |
| Temperature uniformity guarantee | ✅ | ✅ |
| Burner type & count | ✅ | ✅ |
| Heat recovery type | ✅ | ✅ |
| NOx guarantee | ✅ | ✅ |
| Beam cooling system | ✅ | ✅ |
| Charging/discharging method | ✅ | ✅ |
| Control level | ✅ | ✅ |
| Scope itemization (in/out) | ✅ | ✅ |
| Commercial terms block | ✅ | ✅ |
| Identity declaration + business license | ✅ | ✅ |
| Pre-RFQ/RFI status framing | ✅ | ✅ |

### RFQ-DC-MOTOR-DRIVE (EN / ZH)

| Field | EN | ZH |
|---|---|---|
| Model | ✅ | ✅ |
| Continuous & short-time overload power | ✅ | ✅ |
| **Continuous-power basis (ambient/altitude/duty S1–S6)** | ✅ (added) | ✅ |
| Armature voltage, base/max speed, field-weakening ratio | ✅ | ✅ |
| Thermal + commutation overload by speed region | ✅ | ✅ |
| Rated reversals/hour | ✅ | ✅ |
| IP rating, cooling | ✅ | ✅ |
| Encoder/tacho type | ✅ | ✅ |
| Moment of inertia | ✅ | ✅ |
| Insulation class, weight | ✅ | ✅ |
| Motor/drive/transformer/reactor/panels as separate line items | ✅ | ✅ |
| Commercial terms block | ✅ | ✅ |
| Identity declaration + business license | ✅ | ✅ |
| Pre-RFQ/RFI status framing | ✅ | ✅ |

### RFQ-REVERSING-STAND (EN / ZH)

| Field | EN | ZH |
|---|---|---|
| Center-distance / weight convention question (600mm / 35t, unverified) | ✅ | ✅ |
| **Explicit roughing vs. finishing classification + design line speed** | ✅ (added) | ✅ |
| Gearbox output speed at 4 motor-input speeds | ✅ | ✅ |
| Rated/peak torque | ✅ | ✅ |
| Roll diameter assumption | ✅ | ✅ |
| Service factor, bite-shock allowance | ✅ | ✅ |
| Lubrication/cooling | ✅ | ✅ |
| Gear type, design life | ✅ | ✅ |
| Center distance, shaft geometry | ✅ | ✅ |
| Full scope itemization (18 sub-items, in/out) | ✅ | ✅ |
| Commercial terms block | ✅ | ✅ |
| Identity declaration + business license | ✅ | ✅ |
| Pre-RFQ/RFI status framing | ✅ | ✅ |

### RFQ-MAIN-GEARBOX (EN / ZH)

| Field | EN | ZH |
|---|---|---|
| 25:1 reframed as unverified broker reference (not "target") | ✅ | ✅ |
| Three-option request (A: 25:1, B: ~7.1:1, C: vendor's own) with speed-torque justification | ✅ | ✅ |
| **Roll surface speed at 600mm diameter, per option** | ✅ (added) | ✅ |
| Standard vs. custom design per option | ✅ | ✅ |
| Power rating, torque (continuous/peak), input/output speed range | ✅ | ✅ |
| Shaft diameter, center distance, rotation direction | ✅ | ✅ |
| Gear type / used-refurbished condition | ✅ | ✅ |
| Commercial terms block | ✅ | ✅ |
| Identity declaration + business license | ✅ | ✅ |
| Pre-RFQ/RFI status framing | ✅ | ✅ |

## Historical-warning content check

Searched all 8 v4 split documents for "上海东方电气" and for the other 4 previously-fabricated names ("南京年达", "无锡宇顺", "上海臻工", "杭州新恒力"): **zero occurrences in any of the 8 vendor-facing files.** These strings exist only in `QA_LOG_INTERNAL_ONLY_2026-09-22.md`, which is marked internal-only and is not part of any vendor-facing set.

## Conclusion

All 4 items now have full field-by-field substantive parity between their English and Chinese Pre-RFQ/RFI documents. No unilateral gap remains in either direction.
