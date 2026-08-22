def release_allowed(stage, hard_blocks, human_approved=False):
    if hard_blocks:
        return False
    if stage == "RELEASED" and not human_approved:
        return False
    return True


def test_hard_block_prevents_release():
    assert not release_allowed("RELEASED", ["unverified_logo"], True)


def test_human_approval_required_for_release():
    assert not release_allowed("RELEASED", [], False)


def test_clean_approved_artifact_can_release():
    assert release_allowed("RELEASED", [], True)


def test_human_visual_rejection_is_a_hard_block():
    assert not release_allowed("RELEASED", ["human_visual_rejection"], True)


def test_stale_historical_field_is_a_hard_block():
    assert not release_allowed("RELEASED", ["historical_field_leak"], True)
