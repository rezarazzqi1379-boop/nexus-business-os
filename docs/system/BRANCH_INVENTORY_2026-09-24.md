# Branch Inventory — nexus-business-os

Generated 2026-09-24. Scope: every remote branch except `origin/main` (129 branches total). `origin/main` is at `49ba5a0`.

Methodology: for each `origin/<branch>` we computed the tip SHA, last commit date, and ahead/behind vs `origin/main` (`git rev-list --left-right --count`). A branch is **MERGED** when `git merge-base --is-ancestor origin/<b> origin/main` is true. Otherwise we ran `git cherry origin/main origin/<b>` (patch-id equivalence) and, as a further and decisive check, diffed every file the branch changed relative to its merge-base against main's *current* blob for that path (CR-stripped) — this is what "unique files" counts below. Several branches whose patches show as `git cherry`-equivalent (`-`) but whose current-tip file differs were individually confirmed via `git patch-id` against the exact main commit that carries the same patch (main had simply edited the file again afterward) — these are called out by SHA in their notes. `git merge-base --is-ancestor` was also used pairwise between branches to find strict-subset/superset (duplicate) relationships, independent of main.

## 1. Summary counts

| Class | Count |
|---|---|
| MERGED (ancestor of main) | 23 |
| CONTENT-MERGED (patch/content already in main, under different SHAs) | 24 |
| UNIQUE (real content not on main) | 79 |
| BACKUP/SNAPSHOT (name convention) | 3 |
| **Total (excl. main)** | **129** |

Of the 3 BACKUP/SNAPSHOT-named branches: `backup/2026-08-19-pre-work-transfer` and `backup/pre-cloud-rc2-2026-08-24` are genuine point-in-time backups and are also fully merged (0 unique content). `feature/nexus-brain-v0-3-live-snapshot` is misleadingly named — "snapshot" here refers to a live-evidence-snapshot *feature*, not a repo backup — and it holds 4 files of real unmerged feature code; it is **not** a deletion candidate.

## 2. Full branch table

| Branch | Class | Ahead/Behind | Last date | Uniq files | Note |
|---|---|---|---|---|---|
| `adapter-work` | UNIQUE | 14/196 | 2026-08-19 | 2 | 14 unique commits, 2/8 files not on main. Gist: eval: initialize deterministic evaluation package eval: add deterministic structured-output... |
| `architecture/convergence-wave-v0-1` | UNIQUE | 2/157 | 2026-08-27 | 2 | 2 unique commits, 2/2 files not on main. Gist: ops: record PR convergence wave v0.1 docs: define convergence wave and execution sequence  |
| `architecture/core-consolidation-v0-1` | UNIQUE | 4/186 | 2026-08-24 | 2 | 4 unique commits, 2/2 files not on main. Gist: docs: add NEXUS core consolidation plan v0.1 docs: apply Forge project-wide consolidation policy... |
| `architecture/zero-day-deal-desk-v1` | UNIQUE | 2/166 | 2026-08-26 | 2 | 2 unique commits, 2/2 files not on main. Gist: docs: add zero-day Deal Desk execution contract docs: apply NEXUS executive kernel project-wide  |
| `backup/2026-08-19-pre-work-transfer` | BACKUP/SNAPSHOT | 0/196 | 2026-08-19 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). Also fully merged/ancestor -- pure historical snapshot commit, 0 unique content. |
| `backup/pre-cloud-rc2-2026-08-24` | BACKUP/SNAPSHOT | 0/169 | 2026-08-24 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). Also fully merged/ancestor -- pure historical snapshot commit, 0 unique content. |
| `chore/restore-main-ci-v0-1` | UNIQUE | 2/166 | 2026-08-27 | 1 | 2 unique commits, 1/1 files not on main. Gist: ci: restore canonical main test workflow ci: update official actions to Node 24 runtimes  |
| `docs/ai-router-v0-2-promotion` | CONTENT-MERGED | 3/163 | 2026-08-27 | 0 | cherry: 0- /3+ of 3; blob-check: 0/3 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `docs/nexus-brain-v0-2-state-sync` | CONTENT-MERGED | 1/178 | 2026-08-24 | 0 | cherry: 1-/0+ (patch-id equivalent). git patch-id of commit f8b13e0 (0b1ef246...) exactly matches main ancestor commit 036df174 (git patch-id... |
| `docs/plo-consolidation-review-v0-1` | CONTENT-MERGED | 1/174 | 2026-08-24 | 0 | cherry: 1-/0+ (patch-id equivalent). git patch-id of commit d926c63 (03c1f100...) exactly matches main ancestor commit c7037cff. Confirmed landed;... |
| `docs/readme-brain-v0-2` | CONTENT-MERGED | 1/177 | 2026-08-24 | 0 | cherry: 1-/0+ (patch-id equivalent). git patch-id of commit c357788 (584fa57b...) exactly matches main ancestor commit 115db55b (same commit... |
| `experiment/altari-public-patterns-v0-1` | UNIQUE | 23/180 | 2026-08-23 | 21 | 23 unique commits, 21/21 files not on main. Gist: experiment: add provenance-aware workforce registry test: verify workforce registry safety... |
| `experiment/coding-sandbox-benchmark-v0-1` | CONTENT-MERGED | 5/153 | 2026-08-28 | 0 | cherry: 0- /5+ of 5; blob-check: 0/5 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `experiment/model-runner-arena-v0-1` | UNIQUE | 6/157 | 2026-08-27 | 2 | 6 unique commits, 2/6 files not on main. Gist: feat: add governed OpenCode shadow runner contract test: harden OpenCode sandbox runner boundaries... |
| `experiment/opencode-shadow-adapter-v0-1` | UNIQUE | 3/157 | 2026-08-27 | 2 | 3 unique commits, 2/3 files not on main. Gist: feat: add governed OpenCode shadow runner contract test: harden OpenCode sandbox runner boundaries... |
| `experiment/productization-contract-v0-1` | UNIQUE | 5/180 | 2026-08-24 | 3 | 5 unique commits, 3/3 files not on main. Gist: Add productization contract v0.1 Add productization contract regression tests Harden synthetic... |
| `experiment/research-data-mesh-v0-1` | UNIQUE | 36/196 | 2026-08-21 | 2 | 36 unique commits, 2/16 files not on main. Gist: feat: add nexus core package feat: add evidence-backed capability registry feat: add human... |
| `feat/authority-reconciliation-status-v0.1` | UNIQUE | 1/145 | 2026-09-07 | 1 | 1 unique commits, 1/1 files not on main. Gist: docs: record authority reconciliation hold and current evidence state  |
| `feat/capability-governor-code` | MERGED | 0/186 | 2026-08-22 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/capability-governor-engine` | MERGED | 0/186 | 2026-08-22 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/capability-governor-eval` | MERGED | 0/186 | 2026-08-22 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/capability-governor-impl` | MERGED | 0/186 | 2026-08-22 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/capability-governor-implementation` | CONTENT-MERGED | 5/186 | 2026-08-22 | 0 | cherry: 0- /5+ of 5; blob-check: 0/4 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feat/capability-governor-runtime` | MERGED | 0/186 | 2026-08-22 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/capability-governor-v01` | MERGED | 0/186 | 2026-08-22 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/capability-governor-v02` | MERGED | 0/186 | 2026-08-22 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/claude-session-kernel-v0.1` | MERGED | 0/12 | 2026-09-24 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/connector-control-plane-v0.1` | MERGED | 0/117 | 2026-09-11 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/deep-research-discovery-pipeline-v0.1` | MERGED | 0/139 | 2026-09-04 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/deep-research-lab-v0.1` | MERGED | 0/144 | 2026-09-04 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/deep-search-fabric-v2-core-engine` | MERGED | 0/136 | 2026-09-04 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/deep-search-market-intelligence-v0.1` | MERGED | 0/130 | 2026-09-07 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/dual-ai-task-handoff-v0.1` | UNIQUE | 1/147 | 2026-09-03 | 1 | 1 unique commits, 1/2 files not on main. Gist: feat: add dual-AI task-handoff schema and file-backed registry v0.1  |
| `feat/expert-foundry-ingestion-v0.2` | CONTENT-MERGED | 2/140 | 2026-09-08 | 0 | cherry: 2-/0+ (both commits patch-id equivalent to main ancestors ce5227a4 and c0d9067c respectively, verified via git patch-id). Files... |
| `feat/expert-foundry-ingestion-v0.2-integration` | MERGED | 0/136 | 2026-09-08 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/expert-foundry-v0.1` | MERGED | 0/142 | 2026-09-08 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/external-access-broker-v0-1` | UNIQUE | 20/147 | 2026-09-02 | 10 | 20 unique commits, 10/13 files not on main. Gist: feat: add governed external access broker test: prove external access broker gates Expand... |
| `feat/fal-vertical-binding-v0.1` | UNIQUE | 3/134 | 2026-09-07 | 2 | 3 unique commits, 2/2 files not on main. Gist: feat: add PRJ-FAL-01 canonical lane binding test: add PRJ-FAL-01 lane isolation coverage docs(fal):... |
| `feat/meta-orchestrator-control-plane` | UNIQUE | 4/186 | 2026-08-22 | 4 | 4 unique commits, 4/4 files not on main. Gist: feat: add NEXUS meta-orchestrator control plane feat: expose control-plane API test: add... |
| `feat/nexus-capability-portfolio` | UNIQUE | 4/149 | 2026-08-28 | 2 | 4 unique commits, 2/4 files not on main. Gist: feat: expand governed capability portfolio test: verify capability rollout controls docs: record... |
| `feat/nexus-coordination-kit-v0.2` | UNIQUE | 3/145 | 2026-09-05 | 3 | 3 unique commits, 3/4 files not on main. Gist: feat: add dual-AI task-handoff schema and file-backed registry v0.1 Merge branch... |
| `feat/nexus-herdr-runtime` | UNIQUE | 7/152 | 2026-08-28 | 2 | 7 unique commits, 2/7 files not on main. Gist: feat: register Herdr as experimental NEXUS runner feat: add fail-closed Herdr execution planner... |
| `feat/nexus-state-tracking-v0.1` | MERGED | 0/144 | 2026-09-08 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/posthog-observability-v0-1` | UNIQUE | 3/147 | 2026-09-02 | 3 | 3 unique commits, 3/3 files not on main. Gist: feat: add gated PostHog observability adapter test: cover gated PostHog adapter docs: add PostHog... |
| `feat/prj-hyd-01-engineering-review-v0.1` | MERGED | 0/146 | 2026-09-03 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/production-proof-v1` | CONTENT-MERGED | 4/148 | 2026-08-31 | 0 | cherry: 0- /4+ of 4; blob-check: 0/4 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feat/public-handoff-mirror-contract-v0.1` | UNIQUE | 6/145 | 2026-09-05 | 7 | 6 unique commits, 7/8 files not on main. Gist: feat: add dual-AI task-handoff schema and file-backed registry v0.1 Merge branch... |
| `feat/railway-control-layer-v0-1` | UNIQUE | 3/147 | 2026-08-31 | 3 | 3 unique commits, 3/3 files not on main. Gist: feat: add governed Railway API control client test: cover Railway auth and GraphQL safety docs: add... |
| `feat/research-evidence-provider-v0.1` | MERGED | 0/143 | 2026-09-03 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feat/steel-recovery-v0.1` | UNIQUE | 5/14 | 2026-09-22 | 9 | 5 unique commits, 9/9 files not on main. Gist: fix(steel): four errors in the slab-line study, found by external review feat(steel): vendor-ready... |
| `feat/trade-intel-vertical-proof-v0.1` | UNIQUE | 1/138 | 2026-09-04 | 2 | 1 unique commits, 2/2 files not on main. Gist: fix: harden approval pack and JSONL ingest per review  |
| `feat/unified-system-governance-v0.1` | UNIQUE | 1/100 | 2026-09-19 | 20 | 1 unique commits, 20/20 files not on main. Gist: feat(governance): sandbox-only agent lifecycles, FAL reconciliation, capability registry  |
| `feature/access-authority-registry-v0-1` | CONTENT-MERGED | 20/149 | 2026-08-29 | 0 | cherry: 0- /20+ of 20; blob-check: 0/16 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feature/agent-catalog-v0-1` | CONTENT-MERGED | 3/156 | 2026-08-28 | 0 | cherry: 0- /3+ of 3; blob-check: 0/3 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feature/agent-evolution-kernel-v0-1` | UNIQUE | 261/196 | 2026-08-21 | 155 | 261 unique commits, 155/159 files not on main. Gist: feat: add nexus core package feat: add evidence-backed capability registry feat: add human... |
| `feature/ai-resource-router-v0-1` | UNIQUE | 7/166 | 2026-08-27 | 6 | 7 unique commits, 6/7 files not on main. Gist: feat: add fail-closed AI resource router data: add governed AI provider registry feat: add provider... |
| `feature/ai-router-v0-2-hardening` | UNIQUE | 7/164 | 2026-08-27 | 2 | 7 unique commits, 2/6 files not on main. Gist: fix: harden AI router sensitivity and production gates fix: default provider approvals to... |
| `feature/ai-router-v0-3-economy` | CONTENT-MERGED | 3/162 | 2026-08-27 | 0 | cherry: 0- /3+ of 3; blob-check: 0/3 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feature/ai-router-v0-4-provider-evidence` | CONTENT-MERGED | 6/161 | 2026-08-27 | 0 | cherry: 0- /6+ of 6; blob-check: 0/6 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feature/ai-router-v0-5-public-shadow-probe` | UNIQUE | 3/160 | 2026-08-27 | 2 | 3 unique commits, 2/3 files not on main. Gist: feat: add gated public-only provider shadow probe test: add public shadow probe safety gates docs:... |
| `feature/audit-event-envelope-v0-1` | UNIQUE | 24/196 | 2026-08-19 | 5 | 24 unique commits, 5/13 files not on main. Gist: eval: initialize deterministic evaluation package eval: add deterministic structured-output... |
| `feature/autonomy-fabric-v0-1` | UNIQUE | 225/196 | 2026-08-20 | 128 | 225 unique commits, 128/132 files not on main. Gist: feat: add nexus core package feat: add evidence-backed capability registry feat: add human... |
| `feature/autonomy-runner-v0-1` | UNIQUE | 256/196 | 2026-08-21 | 155 | 256 unique commits, 155/159 files not on main. Gist: feat: add nexus core package feat: add evidence-backed capability registry feat: add human... |
| `feature/business-genome-opportunity-engine-v01` | UNIQUE | 33/185 | 2026-08-22 | 25 | 33 unique commits, 25/25 files not on main. Gist: feat: add business genome and opportunity scoring kernel test: cover genome dedupe opportunity... |
| `feature/capability-forge-v0-1` | CONTENT-MERGED | 3/155 | 2026-08-28 | 0 | cherry: 0- /3+ of 3; blob-check: 0/3 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feature/capability-runtime-v0-1` | UNIQUE | 13/196 | 2026-08-19 | 1 | 13 unique commits, 1/5 files not on main. Gist: feat: add nexus core package feat: add evidence-backed capability registry feat: add human... |
| `feature/decision-learning-v0-1` | CONTENT-MERGED | 6/196 | 2026-08-19 | 0 | cherry: 0- /6+ of 6; blob-check: 0/3 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feature/durable-shadow-queue-v0-1` | UNIQUE | 5/171 | 2026-08-24 | 2 | 5 unique commits, 2/2 files not on main. Gist: feat: add durable shadow queue contract test: adversarial durable shadow queue semantics fix: align... |
| `feature/engineering-proposal-delta-v0-1` | CONTENT-MERGED | 2/154 | 2026-08-28 | 0 | cherry: 0- /2+ of 2; blob-check: 0/2 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feature/eval-harness-v0-1` | UNIQUE | 5/196 | 2026-08-19 | 3 | 5 unique commits, 3/3 files not on main. Gist: feat: add deterministic NEXUS eval harness contract test: cover eval validity and promotion... |
| `feature/evaluation-harness-v0-1` | UNIQUE | 16/196 | 2026-08-19 | 2 | 16 unique commits, 2/10 files not on main. Gist: eval: initialize deterministic evaluation package eval: add deterministic structured-output... |
| `feature/evaluation-harness-v0-1-adapters` | UNIQUE | 14/196 | 2026-08-19 | 2 | 14 unique commits, 2/8 files not on main. Gist: eval: initialize deterministic evaluation package eval: add deterministic structured-output... |
| `feature/evaluation-harness-v0-1-shadow-adapters` | UNIQUE | 16/196 | 2026-08-19 | 2 | 16 unique commits, 2/10 files not on main. Gist: eval: initialize deterministic evaluation package eval: add deterministic structured-output... |
| `feature/evidence-classification` | UNIQUE | 8/200 | 2026-08-19 | 4 | 8 unique commits, 4/4 files not on main. Gist: feat: classify evidence epistemic type test: cover evidence epistemic classification test: classify... |
| `feature/execution-intent-v0-1` | UNIQUE | 3/173 | 2026-08-24 | 2 | 3 unique commits, 2/2 files not on main. Gist: feat: add immutable read-only ExecutionIntent contract test: cover immutable ExecutionIntent... |
| `feature/execution-shadow-bridge-v0-1` | UNIQUE | 2/172 | 2026-08-24 | 2 | 2 unique commits, 2/2 files not on main. Gist: feat: add PLO-compatible shadow execution bridge test: verify shadow execution bridge boundaries  |
| `feature/future-agent-lab-v0-1` | CONTENT-MERGED | 8/153 | 2026-08-28 | 0 | cherry: 0- /8+ of 8; blob-check: 0/8 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feature/future-proof-kernel-v0-1` | CONTENT-MERGED | 9/154 | 2026-08-28 | 0 | cherry: 0- /9+ of 9; blob-check: 0/9 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feature/hydrotester-qualification-matrix-v0-1` | UNIQUE | 4/190 | 2026-08-21 | 2 | 4 unique commits, 2/4 files not on main. Gist: Add SupplierTR unresolved hydrotester channel Add hydrotester technical qualification matrix v0.1... |
| `feature/hydrotester-readiness-engine-v0-1` | UNIQUE | 2/189 | 2026-08-21 | 2 | 2 unique commits, 2/2 files not on main. Gist: Add evidence-aware hydrotester readiness engine Add readiness engine adversarial tests  |
| `feature/hydrotester-registry-v0-1` | MERGED | 0/187 | 2026-08-21 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `feature/nexus-brain-plo-contract-v0-5` | UNIQUE | 4/175 | 2026-08-24 | 4 | 4 unique commits, 4/4 files not on main. Gist: feat: add integrated Brain shadow loop contract test: prove integrated shadow loop stays... |
| `feature/nexus-brain-v0-1` | UNIQUE | 8/180 | 2026-08-24 | 7 | 8 unique commits, 7/7 files not on main. Gist: feat: initialize governed NEXUS Brain package feat: add NEXUS Brain ontology primitives feat:... |
| `feature/nexus-brain-v0-2` | UNIQUE | 5/179 | 2026-08-24 | 5 | 5 unique commits, 5/5 files not on main. Gist: feat: add read-only NEXUS Brain projections feat: add authority-aligned portfolio fixtures test:... |
| `feature/nexus-brain-v0-3-live-snapshot` | BACKUP/SNAPSHOT | 7/176 | 2026-08-24 | 4 | Name matches snapshot pattern but content is real unpublished feature work (NOT a repo backup): 4 files not on main. Gist: feat: add fail-safe... |
| `feature/nexus-brain-v0-4-command-live` | UNIQUE | 2/175 | 2026-08-24 | 2 | 2 unique commits, 2/2 files not on main. Gist: feat: add live command snapshot projection test: cover live command snapshot projection  |
| `feature/nexus-forge-loop-v0-1` | UNIQUE | 105/180 | 2026-08-24 | 78 | 105 unique commits, 78/78 files not on main. Gist: experiment: add provenance-aware workforce registry test: verify workforce registry safety... |
| `feature/nexus-integrated-shadow-loop-v0-4` | UNIQUE | 3/175 | 2026-08-25 | 2 | 3 unique commits, 2/2 files not on main. Gist: feat: add integrated Brain shadow loop contract test: prove integrated shadow loop stays... |
| `feature/omniroute-evaluation-v0-1` | UNIQUE | 4/155 | 2026-08-28 | 3 | 4 unique commits, 3/4 files not on main. Gist: feat: add governed OmniRoute evaluation contract test: add adversarial OmniRoute gateway checks... |
| `feature/p0-benchmark-pair-v0-1` | UNIQUE | 22/189 | 2026-08-22 | 2 | 22 unique commits, 2/16 files not on main. Gist: feat: add P0 authority and benchmark contracts test: cover P0 authority and benchmark pair docs:... |
| `feature/portfolio-control-plane-v0-1` | CONTENT-MERGED | 15/157 | 2026-08-27 | 0 | cherry: 0- /15+ of 15; blob-check: 0/13 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `feature/postgres-shadow-queue-v0-1` | UNIQUE | 4/169 | 2026-08-24 | 4 | 4 unique commits, 4/4 files not on main. Gist: feat: add PostgreSQL durable shadow queue build: add optional PostgreSQL queue dependency test: add... |
| `feature/requirement-readiness-shadow` | UNIQUE | 6/199 | 2026-08-19 | 1 | 6 unique commits, 1/4 files not on main. Gist: feat: add shadow-mode requirement readiness gate test: cover requirement readiness shadow gate... |
| `feature/shadow-worker-v0-1` | UNIQUE | 2/170 | 2026-08-24 | 2 | 2 unique commits, 2/2 files not on main. Gist: feat: add read-only shadow worker test: cover shadow worker end-to-end semantics  |
| `feature/temporal-evidence-opportunity-radar-v0-1` | UNIQUE | 14/152 | 2026-08-28 | 14 | 14 unique commits, 14/14 files not on main. Gist: feat: add temporal evidence graph primitive feat: add evidence-bound opportunity radar test:... |
| `feature/trace-envelope-v0-1` | UNIQUE | 10/196 | 2026-08-19 | 4 | 10 unique commits, 4/4 files not on main. Gist: Initialize observability package trace: add privacy-first portable event envelope feat: add... |
| `feature/vertical-acceptance-observability-v0-1` | UNIQUE | 14/151 | 2026-08-29 | 5 | 14 unique commits, 5/5 files not on main. Gist: feat: add measured vertical acceptance harness test: add adversarial vertical acceptance coverage... |
| `fix/canonical-authority-v2` | UNIQUE | 8/158 | 2026-08-27 | 1 | 8 unique commits, 1/3 files not on main. Gist: fix: preserve canonical source versions and obey registry authority test: prove registry-governed... |
| `fix/harden-openai-live-gate-v0-1` | UNIQUE | 2/152 | 2026-08-28 | 2 | 2 unique commits, 2/2 files not on main. Gist: fix: require exact approval gate before OpenAI client creation test: prove API key and boolean... |
| `fix/hydrotester-readiness-drift-20260822` | MERGED | 0/186 | 2026-08-22 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `fix/hydrotester-readiness-usable-evidence-v0-1` | UNIQUE | 2/188 | 2026-08-21 | 2 | 2 unique commits, 2/2 files not on main. Gist: Count only qualified evidence as readiness Add regression tests for usable evidence readiness  |
| `fix/hydrotester-rev1-2-authority` | MERGED | 0/180 | 2026-08-22 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `fix/mobile-login-session-v1` | UNIQUE | 8/149 | 2026-08-31 | 3 | 8 unique commits, 3/5 files not on main. Gist: fix(auth): add secure browser session login feat(auth): add mobile-friendly login routes... |
| `fix/nexus-supervisor-adr-newline` | CONTENT-MERGED | 2/150 | 2026-08-28 | 0 | cherry: 1- /1+ of 2; blob-check: 0/1 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `fix/nexus-supervisor-adr-status` | CONTENT-MERGED | 1/151 | 2026-08-28 | 0 | cherry: 1-/0+ (patch-id equivalent). git patch-id of commit a2d1478 (079ee527...) exactly matches main ancestor commit 0e93684d. Subsequent... |
| `fix/owner-login-separation-v1` | UNIQUE | 8/147 | 2026-08-31 | 4 | 8 unique commits, 4/4 files not on main. Gist: Separate owner login credentials from API token Use independent owner login and expose migration... |
| `fix/redact-public-shadow-probe-secrets-v0-1` | CONTENT-MERGED | 2/159 | 2026-08-27 | 0 | cherry: 0- /2+ of 2; blob-check: 0/2 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `fix/supervisor-exact-approval-boundary-v0-1` | UNIQUE | 2/150 | 2026-08-28 | 2 | 2 unique commits, 2/2 files not on main. Gist: fix: fail closed on supervisor human-approval boundary test: prove supervisor boolean cannot bypass... |
| `governance/global-cross-chat-directive-v1` | UNIQUE | 3/187 | 2026-08-22 | 3 | 3 unique commits, 3/3 files not on main. Gist: Add canonical cross-chat operating directive Add ChatGPT project instructions bootstrap Add ChatGPT... |
| `hardening/core-exact-external-action-v0-1` | UNIQUE | 17/196 | 2026-08-23 | 3 | 17 unique commits, 3/7 files not on main. Gist: feat: add nexus core package feat: add evidence-backed capability registry feat: add human... |
| `hardening/exact-external-gate-v0-2` | UNIQUE | 5/157 | 2026-08-27 | 4 | 5 unique commits, 4/4 files not on main. Gist: security: extract self-contained exact external action gate test: add adversarial exact-action... |
| `hardening/external-ingress-guard-v0-2` | UNIQUE | 9/157 | 2026-08-27 | 7 | 9 unique commits, 7/7 files not on main. Gist: security: extract self-contained exact external action gate test: add adversarial exact-action... |
| `hardening/outreach-per-send-approval-v0-1` | UNIQUE | 233/196 | 2026-08-21 | 132 | 233 unique commits, 132/136 files not on main. Gist: feat: add nexus core package feat: add evidence-backed capability registry feat: add human... |
| `hardening/prompt-injection-e2e-v0-1` | UNIQUE | 220/196 | 2026-08-20 | 130 | 220 unique commits, 130/134 files not on main. Gist: feat: add nexus core package feat: add evidence-backed capability registry feat: add human... |
| `hardening/supabase-data-api-v0-1` | CONTENT-MERGED | 10/196 | 2026-08-23 | 0 | cherry: 0- /10+ of 10; blob-check: 0/4 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `hardening/supplier-collision-gate-v0-1` | UNIQUE | 4/193 | 2026-08-21 | 1 | 4 unique commits, 1/2 files not on main. Gist: Harden supplier collision matching against false positives Add adversarial supplier collision tests... |
| `integration/pr19-pr33-e2e` | UNIQUE | 28/185 | 2026-08-22 | 19 | 28 unique commits, 19/19 files not on main. Gist: feat: add business genome and opportunity scoring kernel test: cover genome dedupe opportunity... |
| `integration/shadow-pr1-pr2-pr4-pr7-pr8` | UNIQUE | 77/196 | 2026-08-19 | 26 | 77 unique commits, 26/31 files not on main. Gist: integration: apply PR1 evidence classification integration: apply PR1 evidence tests... |
| `nexus-vnext-hydrotester-vertical` | UNIQUE | 6/147 | 2026-08-31 | 6 | 6 unique commits, 6/6 files not on main. Gist: Add NEXUS vNext Hydrotester vertical acceptance spec Harden EventStore project and type isolation... |
| `nexus/oig-integration-v01` | UNIQUE | 1/186 | 2026-08-22 | 1 | 1 unique commits, 1/1 files not on main. Gist: docs: add NEXUS cross-project integration contract v0.1  |
| `plo-v0.2-linux-runtime` | UNIQUE | 65/180 | 2026-08-24 | 20 | 65 unique commits, 20/20 files not on main. Gist: Add cloud-native PLO core v0.2.1 Add Gmail read-only adapter Add provider reconciliation policy... |
| `reconcile/omniroute-evaluation-v0-1` | CONTENT-MERGED | 4/154 | 2026-08-28 | 0 | cherry: 0- /4+ of 4; blob-check: 0/4 files differ from main (CR-stripped) -- fully absorbed into main under different SHAs. |
| `research/agent-catalog-scout-2026-08-31` | UNIQUE | 7/156 | 2026-08-31 | 4 | 7 unique commits, 4/7 files not on main. Gist: feat: add persistent agent catalog lifecycle registry test: add agent catalog lifecycle and revisit... |
| `research/china-sourcing-v0.1` | CONTENT-MERGED | 14/100 | 2026-09-23 | 0 | Superseded by research/china-sourcing-v0.2 (merged PR#98). 9 procurement commits cherry-picked into v0.2->main (8 match by patch-id, 1 [3e12c60]... |
| `research/china-sourcing-v0.2` | MERGED | 0/1 | 2026-09-24 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `security/exact-send-core-v0-1` | UNIQUE | 6/180 | 2026-08-23 | 2 | 6 unique commits, 2/2 files not on main. Gist: security: add exact-send approval binding primitive test: prove exact-send approval cannot... |
| `security/policy-threat-model-v0-1` | UNIQUE | 2/196 | 2026-08-19 | 2 | 2 unique commits, 2/2 files not on main. Gist: security: define NEXUS repository security policy security: add NEXUS threat model v0.1  |
| `test/supplier-collision-gate-ci` | MERGED | 0/193 | 2026-08-21 | 0 | Ancestor of origin/main (git merge-base --is-ancestor = true). |
| `tmp-noop` | UNIQUE | 14/196 | 2026-08-19 | 2 | 14 unique commits, 2/8 files not on main. Gist: eval: initialize deterministic evaluation package eval: add deterministic structured-output... |
## 3. Duplicate / near-duplicate groups

### 3.1 The `feat/capability-governor-*` octet (identical tip)
`feat/capability-governor-code`, `-engine`, `-eval`, `-impl`, `-runtime`, `-v01`, `-v02`, and (unrelated name) `fix/hydrotester-readiness-drift-20260822` all point at the **exact same commit** `2f93dc6f` and are already MERGED (ancestor of main, 0 unique). They were evidently created as parallel-naming checkpoints of the same work and never diverged.
`feat/capability-governor-implementation` (tip `9aa8cf2`) is a **strict superset**: `git merge-base --is-ancestor 2f93dc6f origin/feat/capability-governor-implementation` = true, plus 5 more commits (`capability_governor.py`, `agent_lab.py` + tests). Blob-check confirms those files are byte-identical to main today (0/4 unique). All 9 branches are fully redundant with main.

### 3.2 The eval-harness / adapter-work chain
Verified nested ancestry:
```
backup/2026-08-19-pre-work-transfer (MERGED)
 └─ tmp-noop = adapter-work = feature/evaluation-harness-v0-1-adapters   (identical tip eea650e, 14 commits)
     └─ feature/evaluation-harness-v0-1 = feature/evaluation-harness-v0-1-shadow-adapters (identical tip 3a23ddc2, 16 commits)
         └─ feature/audit-event-envelope-v0-1  (24 commits) ← MOST COMPLETE
```
Each `⊂` is a confirmed `git merge-base --is-ancestor`. `feature/audit-event-envelope-v0-1` is the superset and still carries 5 files not on main (real content — keep/review). Everything below it in the chain is a strict subset and can be deleted without losing anything, once `audit-event-envelope-v0-1` is kept.
`feature/eval-harness-v0-1` (src/nexus_core/eval_harness.py) looks similarly named but is an **independent, non-overlapping implementation** (different files) — not part of this chain, not a subset of anything.

### 3.3 The `feature/capability-runtime-v0-1` base
`feature/capability-runtime-v0-1` (13 commits, tip `c8362dc`) is a confirmed ancestor of **six** much larger branches: `experiment/research-data-mesh-v0-1`, `feature/agent-evolution-kernel-v0-1`, `feature/autonomy-fabric-v0-1`, `feature/autonomy-runner-v0-1`, `hardening/core-exact-external-action-v0-1`, `hardening/prompt-injection-e2e-v0-1`. It is a pure historical base checkpoint; every commit it has is already inside each of those six. Safe to delete regardless of which of the six survive review.

### 3.4 `feature/autonomy-fabric-v0-1` vs `feature/autonomy-runner-v0-1` vs `hardening/outreach-per-send-approval-v0-1`
`feature/autonomy-fabric-v0-1` (225 commits, tip `2c58ea6`) is a confirmed ancestor of **both** `feature/autonomy-runner-v0-1` (256 commits) and `hardening/outreach-per-send-approval-v0-1` (233 commits). `feature/autonomy-runner-v0-1` is the largest/most complete of the three (256 commits, 155 unique files vs main). `autonomy-runner` and `outreach-per-send-approval` are themselves independent of each other (neither is an ancestor of the other) — two separate large lines that both grew out of `autonomy-fabric`. All three still carry massive genuinely-unmerged content (128–155 unique files each) and should go to keep/review, not deletion — only `autonomy-fabric` itself is redundant as a pure subset.

### 3.5 `experiment/opencode-shadow-adapter-v0-1` ⊂ `experiment/model-runner-arena-v0-1`
Confirmed ancestor relationship (3 commits inside 6). `model-runner-arena-v0-1` is the superset/most-complete; `opencode-shadow-adapter-v0-1` is a strict subset, safe to delete once the arena branch is kept. (Note: both still have 2 files each not on main relative to main directly — but everything opencode-shadow-adapter has is fully contained in model-runner-arena.)

### 3.6 `feature/agent-catalog-v0-1` ⊂ `research/agent-catalog-scout-2026-08-31`
`feature/agent-catalog-v0-1` (3 commits) is both CONTENT-MERGED on its own (0 unique files vs main) **and** a confirmed ancestor of `research/agent-catalog-scout-2026-08-31` (7 commits, 4 files still not on main — keep/review). Double-safe to delete.

### 3.7 `test/supplier-collision-gate-ci` ⊂ `hardening/supplier-collision-gate-v0-1`
The CI-only branch (already MERGED/ancestor of main) is also a confirmed ancestor of the larger hardening branch, which itself still has 1 file not on main (keep/review, low priority).

### 3.8 Related-but-independent series (not true duplicates — flagged for awareness only)
- **AI router v0.2–v0.5**: `docs/ai-router-v0-2-promotion`, `feature/ai-router-v0-2-hardening`, `-v0-3-economy`, `-v0-4-provider-evidence`, `-v0-5-public-shadow-probe` are five branches on the same theme, each forked independently from main (none is an ancestor of another). Two (`v0-2-promotion`, `v0-3-economy`, `v0-4-provider-evidence`) are fully content-merged; two (`v0-2-hardening`, `v0-5-public-shadow-probe`) each retain 2 files of real unmerged content.
- **Hydrotester family**: `feature/hydrotester-registry-v0-1` (MERGED), `fix/hydrotester-rev1-2-authority` (MERGED), `fix/hydrotester-readiness-drift-20260822` (MERGED, = capability-governor tip), `feature/hydrotester-qualification-matrix-v0-1`, `feature/hydrotester-readiness-engine-v0-1`, `fix/hydrotester-readiness-usable-evidence-v0-1`, `nexus-vnext-hydrotester-vertical` — same problem domain, but no ancestor relationships among the non-merged ones; each carries distinct unmerged content.
- **NEXUS Brain family** (`feature/nexus-brain-v0-1/-v0-2/-v0-3-live-snapshot/-v0-4-command-live`, `feature/nexus-brain-plo-contract-v0-5`, `feature/nexus-integrated-shadow-loop-v0-4`, `docs/nexus-brain-v0-2-state-sync`, `docs/readme-brain-v0-2`): sequential naming, but only the two `docs/*` ones are content-merged; the rest are independent unmerged increments.

## 4. Safe to delete

Only branches whose *entire* history/content is demonstrably already on `origin/main`, or whose entire history is a literal ancestor of another branch that is being kept, are listed. **No branch with any confirmed unique file is included** (see §3.4/3.8 for large branches like `autonomy-runner`, `outreach-per-send-approval`, `audit-event-envelope`, etc., which are explicitly excluded despite containing a redundant subset).

**A. MERGED — literal ancestor of `origin/main` (evidence: `git merge-base --is-ancestor origin/<b> origin/main` = true, 0 unique files)** — 23 branches:
`feat/capability-governor-code`, `-engine`, `-eval`, `-impl`, `-runtime`, `-v01`, `-v02`, `feat/claude-session-kernel-v0.1` (PR#97), `feat/connector-control-plane-v0.1`, `feat/deep-research-discovery-pipeline-v0.1`, `feat/deep-research-lab-v0.1`, `feat/deep-search-fabric-v2-core-engine`, `feat/deep-search-market-intelligence-v0.1`, `feat/expert-foundry-ingestion-v0.2-integration`, `feat/expert-foundry-v0.1`, `feat/nexus-state-tracking-v0.1`, `feat/prj-hyd-01-engineering-review-v0.1`, `feat/research-evidence-provider-v0.1`, `feature/hydrotester-registry-v0-1`, `fix/hydrotester-readiness-drift-20260822`, `fix/hydrotester-rev1-2-authority`, `research/china-sourcing-v0.2` (PR#98), `test/supplier-collision-gate-ci`.

**B. BACKUP, also fully merged** — `backup/2026-08-19-pre-work-transfer`, `backup/pre-cloud-rc2-2026-08-24` (both ancestors of main, 0 unique).

**C. CONTENT-MERGED — every commit's patch verified already in main, 0 unique files (evidence: `git cherry` + CR-stripped blob diff, with `git patch-id` cross-checks where the file was edited again after landing)** — 24 branches:
`docs/ai-router-v0-2-promotion`, `docs/nexus-brain-v0-2-state-sync` (patch-id match to main `036df174`), `docs/plo-consolidation-review-v0-1` (→`c7037cff`), `docs/readme-brain-v0-2` (→`115db55b`), `experiment/coding-sandbox-benchmark-v0-1`, `feat/capability-governor-implementation`, `feat/expert-foundry-ingestion-v0.2` (→`ce5227a4`,`c0d9067c`), `feat/production-proof-v1`, `feature/access-authority-registry-v0-1`, `feature/agent-catalog-v0-1`, `feature/ai-router-v0-3-economy`, `feature/ai-router-v0-4-provider-evidence`, `feature/capability-forge-v0-1`, `feature/decision-learning-v0-1`, `feature/engineering-proposal-delta-v0-1`, `feature/future-agent-lab-v0-1`, `feature/future-proof-kernel-v0-1`, `feature/portfolio-control-plane-v0-1`, `fix/nexus-supervisor-adr-newline`, `fix/nexus-supervisor-adr-status` (→`0e93684d`), `fix/redact-public-shadow-probe-secrets-v0-1`, `hardening/supabase-data-api-v0-1`, `reconcile/omniroute-evaluation-v0-1`, `research/china-sourcing-v0.1` (see detailed evidence below).

  - `research/china-sourcing-v0.1` detail: superseded by `research/china-sourcing-v0.2` (merged PR#98). Its 9 procurement commits are cherry-picked into v0.2→main (8 match by patch-id; the 9th, `3e12c60`, matches main's `a1cb255` by final file blob hash `41d6b4e` despite a differing patch-id, because main's copy of that file already had a head start). Its other 4 non-procurement commits (ST1 roll-diameter fix, round-4/5 questionnaires, claims closure) are confirmed present verbatim in main's current `ROLLING_MILL_ENGINEERING_INTAKE.json` and `ROLLING_MILL_ENGINEER_QUESTIONNAIRE_FA_ROUND4/5_2026-09-19.md`. Its 14th commit, `2451722` (governance), is genuinely **not** on main — but it is fully preserved as the entire content of `feat/unified-system-governance-v0.1`, which is kept separately under active review. Deleting `research/china-sourcing-v0.1` loses nothing.

**D. Strict-subset duplicates (ancestor of a branch being kept — evidence is the `git merge-base --is-ancestor` call itself, which by definition means every commit of the smaller branch already exists in the bigger one)** — 8 additional branches:
- `adapter-work`, `tmp-noop`, `feature/evaluation-harness-v0-1-adapters` (identical tip `eea650e`) — ancestor of `feature/audit-event-envelope-v0-1` (kept, §3.2).
- `feature/evaluation-harness-v0-1`, `feature/evaluation-harness-v0-1-shadow-adapters` (identical tip `3a23ddc2`) — ancestor of `feature/audit-event-envelope-v0-1` (kept, §3.2).
- `feature/capability-runtime-v0-1` — ancestor of 6 kept branches (§3.3).
- `feature/autonomy-fabric-v0-1` — ancestor of `feature/autonomy-runner-v0-1` and `hardening/outreach-per-send-approval-v0-1`, both kept (§3.4).
- `experiment/opencode-shadow-adapter-v0-1` — ancestor of `experiment/model-runner-arena-v0-1`, kept (§3.5).

**Total safe to delete: 23 + 2 + 24 + 8 = 57 branches.**

## 5. Keep / needs owner review (72 branches)

Everything else: all 79 UNIQUE branches minus the 8 strict-subset duplicates already counted above (= 71), plus `feature/nexus-brain-v0-3-live-snapshot` (BACKUP/SNAPSHOT by name, real content) = **72 branches**. These range from single-commit docs/config branches (e.g. `nexus/oig-integration-v01`, `feat/authority-reconciliation-status-v0.1`) to very large, fully independent alternate-history branches with hundreds of unmerged commits (`feature/agent-evolution-kernel-v0-1` 261, `hardening/outreach-per-send-approval-v0-1` 233, `feature/autonomy-runner-v0-1` 256, `hardening/prompt-injection-e2e-v0-1` 220, `feature/nexus-forge-loop-v0-1` 105, `plo-v0.2-linux-runtime` 65, `integration/shadow-pr1-pr2-pr4-pr7-pr8` 77). Full detail, gists and per-branch unique-file counts are in the table in §2 and in `branch_inventory.tsv`. Special flags:
- `feat/unified-system-governance-v0.1` — holds commit `2451722`, explicitly under separate review; do not delete regardless of file-overlap noise.
- `feature/nexus-brain-v0-3-live-snapshot` — misleading name (see §1); real content, not a backup.
- The large orphaned alternate-history branches (`feature/agent-evolution-kernel-v0-1`, `feature/autonomy-runner-v0-1`, `hardening/outreach-per-send-approval-v0-1`, `hardening/prompt-injection-e2e-v0-1`) share almost identical early gists ("add nexus core package", "evidence-backed capability registry", etc.) — they look like parallel/experimental full-repo forks rather than small feature branches, and are worth an explicit product decision (revive, cherry-pick, or archive) rather than a quick delete/keep call.

## Appendix — tip SHAs of the 57 delete candidates (restore record)

Verified independently on 2026-09-24:
- 25 branches are ancestors of main (MERGED + 2 backups).
- 8 are ancestors of a kept branch.
- 24 are CONTENT-MERGED. Of these, 19 have every changed file byte-identical to main after stripping CR, and 5 have every patch already in main by `git cherry`.
- `research/china-sourcing-v0.1` is included. Its procurement tree equals main, and its only other commit, 2451722, is kept on `feat/unified-system-governance-v0.1`.

To restore one: `git push origin <sha>:refs/heads/<branch>`

| branch | tip sha |
|---|---|
| `feat/capability-governor-code` | `2f93dc6fd32a40dad948db2233a76d348925242f` |
| `feat/capability-governor-engine` | `2f93dc6fd32a40dad948db2233a76d348925242f` |
| `feat/capability-governor-eval` | `2f93dc6fd32a40dad948db2233a76d348925242f` |
| `feat/capability-governor-impl` | `2f93dc6fd32a40dad948db2233a76d348925242f` |
| `feat/capability-governor-runtime` | `2f93dc6fd32a40dad948db2233a76d348925242f` |
| `feat/capability-governor-v01` | `2f93dc6fd32a40dad948db2233a76d348925242f` |
| `feat/capability-governor-v02` | `2f93dc6fd32a40dad948db2233a76d348925242f` |
| `feat/claude-session-kernel-v0.1` | `946c7c5c7e3045b6ab157f813a7337cc849c3d00` |
| `feat/connector-control-plane-v0.1` | `c58d24f0c4ff621b6847c604589a6a7ea14b1493` |
| `feat/deep-research-discovery-pipeline-v0.1` | `9d831e3aa67a4c19272f899db6abce662bb1ddea` |
| `feat/deep-research-lab-v0.1` | `efb8190743def9cea4d2e7173c0833ec5480dbb1` |
| `feat/deep-search-fabric-v2-core-engine` | `d02c0ade94f43f04f722855b0b167bf87df9116f` |
| `feat/deep-search-market-intelligence-v0.1` | `0dbb775122e04ffdebaddb8df516a8fd03be5e85` |
| `feat/expert-foundry-ingestion-v0.2-integration` | `ed3bf37ab67350f7da5eefae9d92f2929a6ef67f` |
| `feat/expert-foundry-v0.1` | `0b44e7d049d60736cb18ea84c6949c1290a0d402` |
| `feat/nexus-state-tracking-v0.1` | `e07869ddcb05e6ff6ad6de1381511d7304ed8b06` |
| `feat/prj-hyd-01-engineering-review-v0.1` | `1c85dbbc56370762ffe44ebd682cff2292f06b20` |
| `feat/research-evidence-provider-v0.1` | `53ce215fcdc9c2ca551f6ec1794a318f628c175e` |
| `feature/hydrotester-registry-v0-1` | `0cd4ddd934abb1042978cb41baaa7dbd0bb6eab0` |
| `fix/hydrotester-readiness-drift-20260822` | `2f93dc6fd32a40dad948db2233a76d348925242f` |
| `fix/hydrotester-rev1-2-authority` | `c8ead1bfb1039c30c7fa6fa04dfa2a2d99f4ebd1` |
| `research/china-sourcing-v0.2` | `dd831b6fadafa20f67ec363f6aa5953b2ad9d78a` |
| `test/supplier-collision-gate-ci` | `4db84733775c9d86bc14878662af0a8d1c30fe97` |
| `backup/2026-08-19-pre-work-transfer` | `68d61bb64f96dcce94c341ab0707776f5a8a50c8` |
| `backup/pre-cloud-rc2-2026-08-24` | `38fb911b5430f810b0617e10efa1685ce00868bb` |
| `docs/ai-router-v0-2-promotion` | `56e88aa12915729790d7eeef29695b24564b2f50` |
| `docs/nexus-brain-v0-2-state-sync` | `f8b13e00346c30de482aaeb4ba62facdf436ec38` |
| `docs/plo-consolidation-review-v0-1` | `d926c633bbb0ea6887cec9b8b652ba7f7b79eef2` |
| `docs/readme-brain-v0-2` | `c357788891695cd5bb1ef466aa208984df798901` |
| `experiment/coding-sandbox-benchmark-v0-1` | `cce217c724c2e0603a937a15a5ca679e39ce609f` |
| `feat/capability-governor-implementation` | `9aa8cf2aeddf647cae3562b29dd170a7ec7c87b0` |
| `feat/expert-foundry-ingestion-v0.2` | `98ef2070f878ea4789c024845e6a0de0c3a19eb5` |
| `feat/production-proof-v1` | `d5df643daaf424da5e3fb6bf5c5cdcb5c8190f3e` |
| `feature/access-authority-registry-v0-1` | `916eacfa58aee41059fa8b35edc6418d44e2d5e4` |
| `feature/agent-catalog-v0-1` | `e19a896547da79951dc2635d796183c94fe88008` |
| `feature/ai-router-v0-3-economy` | `cce72e575b4492642ef6c027fb7385b844164ee0` |
| `feature/ai-router-v0-4-provider-evidence` | `7004999892813209e52eedcb0565de3c579f19da` |
| `feature/capability-forge-v0-1` | `8822be71c2ea5b2862eb454d3b803762403af70e` |
| `feature/decision-learning-v0-1` | `d3c951d3f8b20c82911caff1dd69251e42531c59` |
| `feature/engineering-proposal-delta-v0-1` | `5c424dac338d0b2a78842b2af9206a7c8b8f951a` |
| `feature/future-agent-lab-v0-1` | `eccaca83074f0e143010c1a6a82be2a6b0357238` |
| `feature/future-proof-kernel-v0-1` | `2126cec4cc99a5a08d24a86dfc623dcf85882675` |
| `feature/portfolio-control-plane-v0-1` | `31b28e62fa3394b88b42536af0e157c644804271` |
| `fix/nexus-supervisor-adr-newline` | `23959c194fe9864c0edf24311312867c7e0c3f4d` |
| `fix/nexus-supervisor-adr-status` | `a2d1478bd02b9dc57c5db587722ff516f0e066b5` |
| `fix/redact-public-shadow-probe-secrets-v0-1` | `303a0cf1aa7aa9a4b171f7cb080523b677fbe627` |
| `hardening/supabase-data-api-v0-1` | `7728abe631e384dd2ee329d3c84fda193041c091` |
| `reconcile/omniroute-evaluation-v0-1` | `fb1fd09a63f64435890c21e4e57090dc4d55aed0` |
| `adapter-work` | `eea650eef81565738b2ea6f633c47af1a7c476f3` |
| `tmp-noop` | `eea650eef81565738b2ea6f633c47af1a7c476f3` |
| `feature/evaluation-harness-v0-1-adapters` | `eea650eef81565738b2ea6f633c47af1a7c476f3` |
| `feature/evaluation-harness-v0-1` | `3a23ddc2051f359865745236a60f070b464e1610` |
| `feature/evaluation-harness-v0-1-shadow-adapters` | `3a23ddc2051f359865745236a60f070b464e1610` |
| `feature/capability-runtime-v0-1` | `c8362dc951d5228d409ef44d9ff03990e331c610` |
| `feature/autonomy-fabric-v0-1` | `2c58ea6ccb4be8f634d765fba0667fd96328d79d` |
| `experiment/opencode-shadow-adapter-v0-1` | `cf8bf231ab93ccdae8de7d18a73db03ff46dce9c` |
| `research/china-sourcing-v0.1` | `fea723a5d2472cbef6b8be562185fcaa89d924f3` |
