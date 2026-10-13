from restorable_context_ledger import *
def E(**kw):
 d=dict(project_id="CHAIN",checkpoint_id="C1",git_sha="abcdef123",summary="tested buyer graph",evidence_refs=("R1",),ci_run="1267",ci_state="SUCCESS");d.update(kw);return LedgerEntry(**d)
def test_exact_head_and_green_ci_required(): assert resumable(E(),"CHAIN","abcdef123")
def test_stale_head_not_resumable(): assert not resumable(E(),"CHAIN","other123")
def test_cross_project_not_resumable(): assert not resumable(E(),"HYD","abcdef123")
def test_memory_never_authorizes(): assert not memory_authorizes(E())
def test_rehydrate_requires_reverification(): assert rehydrate_request(E())["verify_after_rehydrate"] is True
