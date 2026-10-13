from prompt_compiler import compile_prompt

def test_conversion_prompt_blocks_volume_proxy():
 p=compile_prompt(project_id="P",stage="CONVERSION",blocker="buyer",adapters=())
 assert "NO_VOLUME_PROXY" in p and "canonical conversion/readiness/stock gates" in p

def test_source_roi_is_sandbox_only():
 assert "SANDBOX_ONLY" in compile_prompt(project_id="P",stage="SOURCE_ROI",blocker="yield",adapters=("GitHub",))

def test_action_gate_requires_exact_payload_approval():
 p=compile_prompt(project_id="P",stage="ACTION_GATE",blocker="approval",adapters=())
 assert "exact target/payload/version approval required" in p
