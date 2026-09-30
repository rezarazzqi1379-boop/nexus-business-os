# NEXUS × Claude — Constitution v4.0 implementation audit (READ-ONLY)

**Date:** 2026-09-30
**Scope:** read-only audit. Nothing was installed, merged, pushed, published, sent, or mutated in any external system. No agents were spawned for this audit.
**Evidence base:**
- this session's direct tool use (listed per row);
- `origin/main` at `49ba5a0`;
- the open PR heads.

**Labels:** FACT = directly observed this session · ASSUMPTION · UNKNOWN.

---

## خلاصهٔ فارسی (برای مدیر)

1. **تعارض مرجع؛ باز است و تصمیمش با شماست.**
   - متن همراه قانون اساسی می‌گوید مرجع فعال «Source Registry v1.8 و Master Context v2.1» است.
   - سند رسمی مخزن، `docs/authority/AUTHORITY_STATUS.md` (۲۰۲۶-۰۹-۱۷، با تأیید خود شما)، چیز دیگری می‌گوید: **Master v1.4 و Registry v1.1** مرجع‌اند، و v1.8/v2.1 **ارتقا نیافته‌اند**. دلیلش این است که v2.1 با خودش تناقض دارد: بخش Authority آن v1.8 را حاکم می‌داند و بخش Activation آن v1.9/v1.6 را.
   - طبق قاعدهٔ خود قانون اساسی (بند II: «تازه‌تر بودن نام فایل مرجعیت نمی‌آورد»)، من v1.8/v2.1 را مرجع فرض **نمی‌کنم** تا شما صریحاً تصمیم بگیرید.
   - ضمناً این اسناد در دسترس Claude نیستند. نه در مخزن هستند و نه در پروژهٔ Claude.
2. **بیشتر قانون اساسی از قبل در مخزن وجود دارد** (AGENTS.md، CLAUDE.md، nexus_checks، حافظهٔ خطا، وظایف زمان‌بندی‌شده). نباید کل متن ۵۳ بندی را در CLAUDE.md بگذاریم، چون هر جلسه حدود ۸ هزار توکن خرج می‌کند. فقط ۷ قاعدهٔ واقعاً جدید اضافه شود.
3. **بزرگ‌ترین شکاف واقعی: «ازسرگیری» (checkpoint/resume).**
   - حالت پروژه روی برنچ‌های مرج‌نشده و برنچ‌های push‌نشده پخش است.
   - در همین جلسه یک مطالعهٔ کامل تکراری انجام شد (FM-013)، چون اجرای قبلی بعد از فشرده‌سازی حافظه دیده نمی‌شد. هزینه‌اش حدود یک میلیون توکن بود و هیچ ارزش تصمیمی اضافه نکرد.
4. **ماژول‌های NEXUS ساخته و تست شده‌اند، ولی در کار واقعی Claude استفاده نمی‌شوند.** نمونه‌ها: project_control_plane، nexus_chat_bootstrap، owner_decision_runtime و UnifiedDataHub. AGENTS.md استفاده از آن‌ها را الزامی کرده، ولی در عمل اجرا نمی‌شوند. یا باید به کار گرفته شوند، یا الزامشان برداشته شود.
5. **اولین آزمون عمودی پیشنهادی: RESUME-01.** یک جلسهٔ تازه، فقط از روی مخزن و بدون چت، باید وضعیت همهٔ پروژه‌ها را درست بازیابی کند و کار تکراری شروع نکند. سازوکار لازم کوچک است: یک «بستهٔ ازسرگیری» خواندنی، روی ماژول‌های موجود.
6. **تأییدهای لازم:**
   - (الف) تعیین مرجع: v1.4/v1.1 یا v1.8/v2.1.
   - (ب) مرج PRهای #99، #100 و #101، و push برنچ‌های حالت.
   - (ج) اختیاری: یک دسترسی محدود GitHub (فقط push روی برنچ‌های غیراصلی و ساخت PR، بدون merge) تا چرخهٔ دستی push/PR حذف شود.

---

## 1. Current architecture

| Layer | What exists | Maturity |
|---|---|---|
| Operating contract | `AGENTS.md` (1,638 words, loaded every session) and `CLAUDE.md`. The kernel is 957 words on the experiments branch; main still has the ruflo-era file until PR merges | MERGED on main (AGENTS); PUSHED, not merged (new CLAUDE.md is on #97 main; §2/§5 updates on unmerged branches) |
| Authority record | `docs/authority/AUTHORITY_STATUS.md`: tuple v1.4/v1.1 promoted 2026-09-17; v1.6–v2.1 pending | MERGED |
| State / memory | `.nexus/state/CURRENT_STATE.md`, `.nexus/steel/{KERNEL,CHECKPOINT,CHANGELOG}.md`, project control docs, `.nexus/memory/*.jsonl` (`nexus_core.project_memory`) and `ENGINEERING_FAILURE_MEMORY.md` (FM-001…FM-012; FM-013 still to be recorded) | Main's `CURRENT_STATE.md` is **stale**: it says authority is "UNRESOLVED, BLOCKING", which contradicts AUTHORITY_STATUS. The corrected copy is on an unmerged branch |
| Executable checks | `nexus_checks`: hygiene, EN/ZH parity, superseded values, git health (on main); transmission and state freshness (unmerged `feat/steel-experiments-v0.1`); CI runs pytest on `evals` (unmerged #100) | TESTED; partly INTEGRATED |
| NEXUS runtime modules | `agent_supervisor`, `autonomy`, `execution_scheduler`, `agent_catalog`, `mcp_broker`, `research_lab`, `project_control_plane`, `continuous_research`, `self_improvement_runtime`, `adoption_gate`, `resource_router`, `conversation_control`, `owner_decision_runtime`, `portfolio_watchdog`, `nexus_chat_bootstrap`, `project_memory`, `collaboration_growth`, `unified_data_environment` (UnifiedDataHub) | IMPLEMENTED + unit TESTED. **Not INTEGRATED into Claude's actual workflow**: none was invoked in this session's recorded work (FACT for the visible context; earlier compacted turns UNKNOWN) |
| Recurring execution | Claude scheduled tasks: weekly stock radar (cloud, Sonnet), laptop-browser radar (device-bound), weekly health check (cloud, Sonnet), Ops Deck refresh (6-hourly) | ACTIVE. The laptop task was auto-suspended once (device absent) and re-enabled |
| Human gates | push / merge / PR creation / branch deletion / vendor contact are owner actions | By design; FACT: no git credentials exist in either the cloud or the device |

## 2. Capability inventory

| Capability | Status (highest level reached) | Evidence / limits |
|---|---|---|
| Main model (configured `claude-opus-5-5`) | TESTED | this session |
| Subagents with a model tier (haiku / sonnet / default) | TESTED | sonnet and default used; per-run cost 146k–367k tokens (measured) |
| Workflow tool (multi-agent orchestration) | AVAILABLE | gated on the owner's explicit opt-in; never run |
| Cloud shell container | WRITE_ENABLED, TESTED | ephemeral; git clone and ls-remote work; `api.github.com` returns 403 from here (FACT) |
| Device bridge: laptop shell and file transfer | CONNECTED (intermittent), WRITE_ENABLED, TESTED | cannot write `.claude/`; delete disabled by default; git bundles transferred OK |
| Built-in browser (laptop) | READ_VERIFIED, TESTED | GitHub API reads, Baidu, 51chuli; not logged in to GitHub; some sites need login (JD, Taobao) |
| Claude in Chrome; computer use | AVAILABLE | not tested this session |
| WebSearch / WebFetch | TESTED | search is US-only; WebFetch returns summaries (FACT: numbers must be re-read live) |
| Exa MCP | CONNECTED | not used directly |
| Gmail, Drive, Calendar MCP | CONNECTED | READ_VERIFIED is UNKNOWN in this session (the Ops Deck task uses Gmail; its last run was PENDING) |
| Notion, HubSpot, Railway, Figma, Canva, Adobe MCP | CONNECTED | untested; Notion and Figma disconnected and reconnected mid-session (FACT) |
| Scheduled tasks (claude-code-remote) | WRITE_ENABLED, TESTED | a device-bound task's model cannot be patched remotely (FACT) |
| Cross-surface memory (memory MCP) | WRITE_ENABLED, TESTED | project-scoped writes only |
| Claude Project attached to this session | AVAILABLE | it is the generic "How to use Claude" project. **The NEXUS Masters and Registry are not in it** |
| Skills (synced) | TESTED | nexus-steel-rolling-line, device-git-plumbing-workflow (updated 2026-09-26), respond-to-engineering-review, skill-creator, office skills, deep-research |
| Git write to remote | **ABSENT** | no credentials anywhere (FACT: push dry-run failed); the owner pushes |
| GitHub CI | READ_VERIFIED | read through the laptop browser |
| Artifact publishing | AVAILABLE | not used this session |

## 3. Gap analysis against v4.0

| v4.0 section | Status | Gap |
|---|---|---|
| II Authority first | **PARTIAL, CONFLICTED** | The Masters are not reachable by Claude. The owner's brief names v1.8/v2.1, while the repo record says v1.4/v1.1. Main's CURRENT_STATE is stale |
| III Isolation | MET | reroll vs slab line kept separate; FM-009/010 |
| IV Truth system | MET | labels used; the Phase 1.5 correction proved it works when challenged |
| V Maturity | MET | — |
| VII/VIII Continue and blocker engine | PARTIAL | blockers are handled ad hoc; there is no classification record |
| X Context independence | **GAP (largest)** | state is scattered across unmerged or unpushed branches; compaction hid a finished study → duplicate run (FM-013) |
| XI/XII Model router and token governor | PARTIAL | tiers are used and measured (CLAUDE.md §4); no per-mission budget |
| XIII ExpertForge | PARTIAL | the literature validation exists; no domain-map step or exam |
| XVII Independent calculation | PARTIAL | the reroll "independent" check shared physics → corrected to "limited independence" |
| XVIII/XIX Shadow Scientist, Red Team | MET in practice | red-team and transmission audits found 6 P0s; not codified as a step |
| XXI/XXII Experience and Failure library | MET | FM register + executable checks; no CASE_ID format |
| XXIII Expert exam | GAP | no benchmark set for the steel specialist workflow |
| XXIV–XXVI Adaptive Arena | AVAILABLE (Workflow tool) | no escalation policy tied to measured cost |
| XXIX Tool status ladder | GAP | no maintained capability registry for Claude-side tools (this table is the first) |
| XXXVIII Outbound gate with Persian translation | **NEW RULE** | not in CLAUDE.md; worth adding |
| XXXIX Security | PARTIAL | no secrets in repo (FACT: never written); connector scopes UNKNOWN |
| XLIV Anti-fake-autonomy | PARTIAL | NEXUS runtime modules are mandated in AGENTS.md but not used (a contract-vs-practice gap) |

## 4. KEEP (proven by measured outcome)

- **Independent reviewer before merge or vendor release.** Red-team 177k tokens → 2 P0s; transmission audit 367k → 4 wrong vendor numbers.
- `nexus_checks`, with its transmission and state checks, in CI.
- The failure memory, where each lesson becomes a test.
- Scheduled weekly tasks on Sonnet.
- The evidence and maturity vocabularies.
- The owner-controlled push/merge gate.
- Phase-limited execution (Phase 1 → 1.5 → wait for data). It stopped token burn when the inputs were missing.

## 5. MODIFY

1. **CLAUDE.md:** add only the v4.0 deltas as ≤15 lines. Do not paste the constitution, because every session would pay about 8k tokens. The deltas:
   - the Shadow-Scientist question;
   - no voting for truth;
   - the outbound gate with a Persian rendering;
   - the capability ladder;
   - blocker classes;
   - anti-theater reporting;
   - the arena escalation limits.
2. **AGENTS.md mandatory preflight:** it requires `nexus_chat_bootstrap`, `build_coordination_plan` and the rest before consequential results, but practice does not do this. Either wire the useful ones into the resume packet (§11) or downgrade them to "optional". Owner decision.
3. **Main `CURRENT_STATE.md`:** stale on authority. Fixed on an unmerged branch; it lands when the PRs merge.
4. **Failure memory entries:** add CASE_ID, missed-signal and detection-method fields (v4.0 §XXI), keeping the existing FM numbering.

## 6. REMOVE or RETIRE (complexity tax)

- **40 archive branches.** Triaged, with SHAs recorded; deletion awaits the owner's yes.
- **The run-2 reroll branch** `feat/reroll-01-v0.1`. It duplicates run 1, and its unique content is the independent model plus the metallurgy doc. Merge those two items or archive the branch; do not maintain two models.
- **The ruflo leftovers** (OPS-04, `.claude/settings.json` plugins). This needs the owner's commit.
- **Long pre-filled PR-link bodies in chat.** Use short PR bodies instead.

## 7. Missing mechanisms worth building (ranked)

1. **Resume packet (P1, Priority 1).** One read-only command prints a compact recovery digest (details in §11).
2. **Duplicate-work guard (FM-013).** Search the project ID across all local refs, worktrees and remote refs before starting a project. Part of 1.
3. **Authority pointer.** Add the Masters to the repo or the Claude Project once the owner decides the tuple, so Claude can actually recover them.
4. **Specialist exam for the steel workflow.** Pin 5–10 published worked examples as tests; the list is already proposed in `MODEL_LITERATURE_VALIDATION`.
5. **Capability registry file.** This table, kept current by the weekly health task.

**Not worth building now:** a new arena framework (the Workflow tool exists), GraphRAG, a vector DB, a new agent catalog (one exists), or a new memory service (`project_memory` exists).

## 8. Token and compute waste (measured, subagent tokens)

| Item | Tokens | Value |
|---|---|---|
| Duplicate reroll run (3 agents + setup), 2026-09-29 | ≈ 0.8–1.0 M | ≈ 0: the conclusion was identical to run 1. **Cause:** no branch/worktree check, and compaction |
| Branch inventory + triage | 425 k | partial: 57 branches deleted; 40 decisions still pending |
| Transmission audit / red team | 367 k / 177 k | high: 6 P0 |
| Builders on precise specs (state, transmission, batch, experiments) | 146–240 k each | high, done first time |
| Always-loaded context (AGENTS.md + CLAUDE.md) | ≈ 3.5–4 k per turn (cached) | acceptable; the constitution in full would roughly triple it |

## 9. ExpertForge plan

Reuse, don't build. For each specialist problem:

1. **Domain map.** A 10-line list of disciplines and failure modes, written into the project control doc.
2. **Frontier.** Run `deep-research` or one Sonnet research agent over standards, handbooks and OEM documents, and record the results in the existing literature-validation format.
3. **Exam.** Pinned worked-example tests in `evals/` (§7.4).
4. **Promotion rule.** A workflow counts as "expert" only after it passes the exam; this reuses `adoption_gate`.

**First target:** steel rolling. The inputs already exist.

## 10. Adaptive Arena plan

- **Mechanism:** the Workflow tool (already available, owner opt-in) plus the Agent tool.
- **Escalation, tied to measured cost** (~150–350 k tokens per agent):
  - 1 worker by default;
  - 2–4 workers only for a contradiction or a consequential number;
  - ≥5 only with the owner's explicit opt-in, stating the expected information value.
- **Participant diversity is mandatory.** Participants must use different methods, as v4.0 §XXV requires. This session's "independent" models shared the same physics, and that was a lesson.

## 11. Persistent checkpoint/resume plan

- **What exists:** state files, `project_memory`, the state-freshness check and the weekly health task.
- **Gaps:**
  - (a) truth lives on unmerged or unpushed branches;
  - (b) there is no single digest;
  - (c) there is no worktree or ref awareness.
- **Build `nexus_checks --resume` (read-only).** It reuses `project_memory.bootstrap_context()`, `state_freshness` and git. Output of at most ~3k tokens:
  - per PROJECT_ID: phase, stop gate, awaited inputs and next action (from control docs);
  - open PRs (`ls-remote refs/pull`), unpushed local branches and worktrees, and project-ID hits across all refs (the FM-013 guard);
  - the authority tuple and the latest FM entries.
- **Policy:** push state-bearing branches the same day; merge state PRs first.

## 12. Experience and Failure Library plan

Keep `ENGINEERING_FAILURE_MEMORY.md` as the library.

- Add a template with the v4.0 fields: CASE_ID, hypothesis, hidden constraint, missed signal, detection method, permanent test and limits.
- Rule: no FM entry closes without a linked test or check, or an explicit "lesson only".
- FM-013 (duplicate project run) is the first new-format entry, and its test is the §11 guard.

## 13. Capability escalation plan

Use the v4.0 ladder: AVAILABLE → CONNECTED → AUTHENTICATED → READ_VERIFIED → WRITE_ENABLED → TESTED → PRODUCTION_APPROVED.

- The highest-value escalation is **GitHub write with least privilege**:
  - a fine-grained token or the official GitHub connector, scoped to this repository only;
  - contents write on non-default branches plus PR creation;
  - **no merge or admin rights**, and branch protection on `main`.

  It removes the most frequent manual loop in this project (push → open PR → report back), about 15 round trips so far. **It needs the owner's action and approval;** Claude must not create or handle the credential.
- Second: log the laptop browser in to GitHub. This is the owner's action; it would give CI log access.

## 14. Security and credential architecture

**Facts:**
- No secrets have been written to the repo, prompts or logs in this session.
- There are no git credentials in the cloud or on the device.
- Connectors are authenticated through claude.ai OAuth, with **scopes UNKNOWN**.

**Plan:**
- Record each connector's scope in the capability registry. The owner can read the scopes in claude.ai settings.
- Keep separate read, write and production credentials.
- Any new credential is created by the owner and referenced by locator only (AGENTS.md rule).
- The Railway connector can deploy, so treat it as production. It needs an explicit YELLOW gate per action.

## 15. Smallest end-to-end vertical acceptance test: RESUME-01

**Goal:** a cold session recovers the project state correctly without the chat.

**Procedure:**
1. Take a fresh clone of `origin` and run `python -m nexus_checks --resume`.
2. Give a fresh subagent with no chat context (Sonnet) **only** the packet.
3. Ask it 8 fixed questions and score them against an answer key:
   1. the active projects and their phases;
   2. the reroll stop gate and the five awaited inputs;
   3. the open PRs and their merge order;
   4. the unpushed or unmerged state-bearing branches;
   5. the authority tuple and its open conflict;
   6. the last 3 FM lessons;
   7. the next safe action per project;
   8. "Should you start PRJ-STEEL-REROLL-01 from scratch?" (must be **no**).
4. Run a **baseline** first: the same 8 questions from the current `main` without the packet.

**Measure:** correct answers, packet tokens, wall time, and whether the duplicate-work guard fires.

**Pass:** 8/8 with a packet under 3k tokens, versus the baseline, which is expected to fail at least questions 2, 4 and 5.

## 16. Exact implementation sequence

1. **Owner:** decide the authority tuple (§0.1).
2. **Owner:** merge #99 → #100 → #101, push `feat/steel-experiments-v0.1` and open its PR, then push `feat/steel-reroll-01`.
3. **Claude:** record FM-013 in the new format and add the CLAUDE.md v4.0 delta lines (≤15). This is a local branch, not a merge.
4. **Claude:** build `--resume` with tests. One Sonnet builder on a precise spec, or done directly.
5. **Claude:** run the RESUME-01 baseline, then the treatment. Report the scores and token numbers.
6. **Keep or roll back** based on the score.
7. **Only then** move to Priority 2 or 3, i.e. the ExpertForge exam.

## 17. Rollback plan

Every step is additive and read-only at runtime:
- `--resume` is one module plus one test file; delete both and revert the CLAUDE.md lines.
- FM-013 is an append-only entry and stays even on rollback, because failure knowledge is kept.
- No external system is touched. The GitHub credential, if the owner creates it, is revoked in GitHub settings.

## 18. Estimated impact

| Step | One-off cost | Recurring effect |
|---|---|---|
| CLAUDE.md delta | ≈ 5 k tokens | +≈ 300 tokens/turn (cached) |
| `--resume` build and tests | ≈ 60–120 k (ASSUMPTION, from measured builder runs) | the boot reads one digest instead of 5–8 files |
| RESUME-01 run | ≈ 20–40 k | — |
| Avoided duplicate runs | — | the one observed case cost ≈ 0.8–1.0 M tokens |
| GitHub least-privilege write (if approved) | owner setup ≈ 10 min | removes about 3 chat round trips per PR |

**Stop point:** the audit is complete. The next safe internal step (§16.3–16.4) is ready, but the owner decides §16.1–16.2 first. The authority conflict is the one decision that must not be made by Claude.
