# AI Resource Router CI Gate v0.1

Status: HISTORICAL — ORIGINAL GATE SUPERSEDED BY v0.2 HARDENING / PR #57.

This record described the initial integration gate for the governed AI Resource Router introduced in PR #56. The initial PR passed the then-canonical `evals/` workflow, but that workflow did not execute the newly added pytest router suite. The gap was discovered after merge and corrected rather than treated as completed proof.

The effective CI requirement is now:

1. compile the repository;
2. run canonical `python -m unittest discover -s evals -v`;
3. run `pytest -q tests` with `PYTHONPATH=src`;
4. keep FreeLLM discovery-only and prevent self-promotion;
5. default provider sensitivity to public and require explicit policy review for routing;
6. require explicit production approval rather than infer it from role/status strings;
7. introduce no provider call, spend, credential use, deployment, email send or other external effect merely because CI passes.

PR #57 exact head `28d4560a1b800d7a2aa0b576b0a94e8e8c3003e8` passed the corrected full workflow before squash merge to main as `20a5ca50855b0f0721e0cf5e72a01649d9f8de40`.

Promotion beyond merged/tested infrastructure still requires live provider verification, privacy/retention/training review, account/region constraints, workload-specific evals, bounded latency/cost evidence, secrets handling, fallback/retry/rollback proof and explicit production authorization.
