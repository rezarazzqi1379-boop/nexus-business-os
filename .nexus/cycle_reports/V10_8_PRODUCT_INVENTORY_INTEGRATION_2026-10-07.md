# NEXUS v10.8 Product/Inventory Integration — 2026-10-07

## CI gate
#1129 SUCCESS. currentness_engine and its profile-update regression are TESTED.

## New user-provided evidence
Two physical sheets were supplied in-chat:
1 capability/grade/form sheet;
2 ready-stock snapshot.

Ready-stock snapshot was transcribed as:
20MnCrS5 280-500 mm, 3-10 m, ~700 t
42CrMo4 290-760 mm, 2-7 m, ~80 t
8620 350-450 mm, 3-7 m, ~140 t
C15 300-450 mm, 3-8 m, ~1141 t
C45 290-980 mm, 2-8 m, ~156 t
S355J2G3 300-500 mm, 3-7 m, ~419 t
St52 300-500 mm, 3-8 m, ~64 t
CK Series 100-980 mm, 2-10 m, ~1100 t

Sheet total states approximately 3800 t.

## Evidence semantics
The sheet date is not visible. Therefore every stock row is CURRENTNESS=UNKNOWN and must be reconfirmed before quotation/availability claims.
Capability evidence and inventory evidence are separate.
Russian-grade column is reference evidence only; equivalence to European grades is not established.

## Commercial impact
Demand-first discovery can now prioritize exact grade + diameter + length against the snapshot. A dimensional match becomes SNAPSHOT_MATCH_RECONFIRM_STOCK until fresh inventory confirmation.
