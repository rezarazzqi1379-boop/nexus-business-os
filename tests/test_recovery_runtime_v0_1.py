from nexus_control_plane.recovery_runtime import (
    RecoveryAction,
    RecoveryCheckpoint,
    RecoveryInput,
    decide_recovery,
)


def cp() -> RecoveryCheckpoint:
    return RecoveryCheckpoint(
        checkpoint_id="cp-verified-02",
        state_ref="state:verified:02",
        evidence_refs=("evidence:test:02",),
        verified=True,
        reversible=True,
    )


def test_state_corruption_rewinds_to_latest_verified_checkpoint():
    result = decide_recovery(
        RecoveryInput(
            failure_class="state_corruption",
            local_failure=False,
            state_corrupted=True,
            repeated_attempts=1,
            max_retries=2,
            consequential=False,
            checkpoints=(cp(),),
        )
    )
    assert result.action is RecoveryAction.REWIND
    assert result.checkpoint_id == "cp-verified-02"


def test_local_failure_uses_bounded_retry():
    result = decide_recovery(
        RecoveryInput(
            failure_class="transient_tool_timeout",
            local_failure=True,
            state_corrupted=False,
            repeated_attempts=0,
            max_retries=1,
            consequential=False,
            checkpoints=(cp(),),
        )
    )
    assert result.action is RecoveryAction.RETRY_LOCAL


def test_retry_exhaustion_replans_instead_of_blind_retry():
    result = decide_recovery(
        RecoveryInput(
            failure_class="repeated_tool_failure",
            local_failure=True,
            state_corrupted=False,
            repeated_attempts=2,
            max_retries=2,
            consequential=False,
            checkpoints=(cp(),),
        )
    )
    assert result.action is RecoveryAction.REPLAN_FROM_CHECKPOINT


def test_consequential_failure_never_auto_rewinds():
    result = decide_recovery(
        RecoveryInput(
            failure_class="external_action_state_mismatch",
            local_failure=False,
            state_corrupted=True,
            repeated_attempts=1,
            max_retries=2,
            consequential=True,
            checkpoints=(cp(),),
        )
    )
    assert result.action is RecoveryAction.HUMAN_HOLD


def test_corruption_without_checkpoint_fails_closed():
    result = decide_recovery(
        RecoveryInput(
            failure_class="state_corruption",
            local_failure=False,
            state_corrupted=True,
            repeated_attempts=0,
            max_retries=2,
            consequential=False,
            checkpoints=(),
        )
    )
    assert result.action is RecoveryAction.HUMAN_HOLD
