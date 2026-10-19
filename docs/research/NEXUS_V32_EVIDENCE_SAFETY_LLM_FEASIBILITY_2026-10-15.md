# NEXUS v3.2: evidence safety and local LLM feasibility

Baseline inspected independently: `127edca49be8b0584019dd6acf683669135c89b5`.
Worktree unchanged at entry; original implementation/report and tests inspected.
Branch: `codex/evidence-safety-llm-feasibility-2026-10-15`.
No push, merge, deployment, service installation, credentials, payments or
permission changes. Hardware queries initially denied in the sandbox succeeded
through authorized read-only escalation; no Windows permission was changed.

## Secret Guard: reproduced, preserved, not bypassed

`coordination_kit._SECRET_PATTERNS[6]` matches 60+ characters from the Base64
alphabet. Hex SHA256 consists of 64 characters in that alphabet, so the original
diff triggered it. The original 19 matches were independently located without
printing token values. Original live evidence and verification JSON are unchanged;
original blocker log copied byte-for-byte to `data/research/v32-original-handoff-blocker.json`.
Their SHA256 bindings and diagnostic findings are in `v32-evidence-guard-review.json`.

Added `evidence_digest_review.py`, an EXPERIMENT_ONLY diagnostic. It recomputes
hashes from actual file/document bytes or canonical submitted manifests. It
explains **19/19** original matches as recomputed digests. It does NOT authorize
handoff, suppress findings, change regexes, alter coordination_kit, or return ALLOW.
Original guard decision remains **BLOCK**, zero findings suppressed.

Three original manifest hashes bind mixed/CRLF working bytes, while Git stores
normalized LF. This is a separate reproducibility finding, not evidence of a
credential. `v32-original-byte-bindings.json` preserves original commit, normalized
blob hash, raw hash and CRLF line indexes. Exact bytes reconstruct by reading the
immutable commit blob, splitting with keepends=True and replacing each indexed
LF ending with CRLF. Roundtrip was executed and matched all three original files.
No original evidence was rewritten to make the scanner pass.

Minimal safe remediation proposal: attach typed, independently recomputed digest
proofs to a human security review; distinguish digest findings from unproven opaque
strings. Preserve provider-key, password-context and private-key detection and
block every unexplained match. The proposed proof classifier is implemented and
tested; integrating an authorization decision into the handoff guard is deliberately
NOT promoted. Reviewable diagnostics are the result, not a claim of repaired handoff.
Tests verify wrong bytes, missing files, traversal, unknown hex, password context
and tampered embedded bodies cannot create an allowance. Credential-context findings
remain even when a value equals a known digest. No hash allowlist is introduced.

## Model feasibility: possible hardware, unavailable runtime

Read-only hardware observations:
- RAM: 16,791,048,192 bytes (about 15.64 GiB); available RAM snapshot in hardware JSON.
- CPU: Intel Core i5-13420H, 8 cores / 12 logical processors.
- NVIDIA RTX4050 Laptop: **6141 MiB VRAM**, measured with installed
  `C:/Windows/System32/nvidia-smi.exe --query-gpu=name,memory.total --format=csv,noheader`.
- WMI AdapterRAM reported about 4GiB; do NOT use that as actual VRAM. NVIDIA query
  resolved this discrepancy. Intel integrated GPU also present.

No `ollama`, `llama-server` or `lms` on PATH; conventional Ollama/HuggingFace/LMStudio
model cache directories absent. Checked current project interpreter: torch,
transformers, llama_cpp, onnxruntime, openai and agents absent. This is bounded
inventory, not a claim that no model exists anywhere on the machine. No approved
zero-charge remote model endpoint or usable local model was verified. No credentials
were read or provider inference requests made. ChatGPT subscription access was
not treated as API entitlement.

Candidate for a future disposable experiment: Qwen3-0.6B. Official model card:
https://huggingface.co/Qwen/Qwen3-0.6B — Apache-2.0, 0.6B parameters, 32768-token
context; model card supports local inference. Runtime candidate llama.cpp:
https://github.com/ggml-org/llama.cpp and its MIT LICENSE. Both sources refreshed
through web reads on this run. These licenses are evidence for evaluation, not a
claim that every distribution/quantization or jurisdiction has been legally cleared.
Retain attribution/license obligations; use publisher artifacts, pinned revisions
and verified hashes before execution. No quantized third-party artifact was selected.

Weights-only BF16 arithmetic estimate is roughly 1.2GB, excluding tokenizer,
KV cache and runtime buffers. The measured hardware makes a SMALL-context local
trial plausible; actual allocation, throughput and compatibility are unmeasured.
A future trial should start with 2048 context / 128 output tokens, sequential,
read-only public fixtures, hard process timeout and offline network restriction.
Advertised 32768 context is not the proposed task budget or proof it fits comfortably.

Local open weights can avoid provider per-token charges, but electricity/download
and hardware resource use are not literally free; these costs are unmeasured.
No runtime/model is currently installed and approved for this lane, so **operational
zero-charge LLM availability is NOT CONFIRMED**. Privacy of a future local setup
requires verified offline behavior/telemetry controls; it has not been demonstrated.
No LLM selected, downloaded, installed or called. LLM reasoning, hallucination rate,
latency, memory usage and recovery are NOT_MEASURED rather than invented zeroes.

## Deterministic agent improvement and comparisons

Tightened `PublicResearchRuntime.validate_result`: bind the exact repository query
and require integer values for model tokens, API cost and actual expected HTTP-read
count. False/bool counts and invented zero reads are rejected. Existing source
identity/hash/freshness/project/lease checks remain. Three new negative cases cover
query and accounting tampering. Existing shared queue/Supervisor/console retained.

Ten frozen real-payload replays executed with the existing benchmark tool:
60/60 field matches, zero completed replays, zero network/model calls. Median
**0.0153643s**, versus previous frozen entry-point 0.031588s; timing variation alone
does NOT prove an optimization. No new live network sample or commercial yield.
These metrics measure six-field source extraction, not semantic reasoning quality.
Unsupported field edits are rejected; a general hallucination rate is UNKNOWN.
LLM-vs-deterministic comparison remains blocked until an operational model exists.

## Independently executed verification

Python: `C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe`, 3.14.7.
`PYTHONPATH=src`; pytest 8.4.2. No dependencies changed.

```text
python -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-v32-baseline tests/test_public_research_agent.py evals/test_coordination_kit.py
# Baseline: 64 passed, 37.54s
python -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-v32-focused tests/test_evidence_digest_review.py tests/test_public_research_agent.py evals/test_coordination_kit.py
# After changes: 74 passed, 37.00s
python benchmark_public_research_agent.py --capture data/research/public-agent-live-2026-10-15.json --output data/research/v32-deterministic-benchmark.json
python -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-v32-full tests evals
git diff --check
```

Final full result/log/hash and changed-source manifest:
`data/research/v32-verification.json`. Original guard source is unchanged, proven
by comparing its blob with baseline. Registry/Master authority HOLD remains; fresh
bootstrap returns BLOCK. Scoped memory records derived evidence only. No production
or learned-policy promotion; self-improvement result PARTIAL.

## Recovery, rollback, next safe action

Revert the isolated development commit to undo classifier and query/accounting
checks. Keep original evidence, guard logs, queue and memory history; supersede
checkpoint records rather than delete them. No database migration or service to undo.

Next: security review the typed-digest proposal before any handoff-guard integration.
For LLM work, prepare a pinned publisher-model/runtime manifest with hashes,
download size, license, offline behavior, rollback and disposable-path scope;
obtain exact installation/use scope where required. Never infer a paid API budget
or turn account access into authorization. Exact commit/branch publication remains
a separate approval boundary; new remote CI NOT_RUN.
