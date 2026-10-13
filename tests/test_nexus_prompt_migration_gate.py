from nexus_prompt_migration_gate import MigrationScenario, migration_gate

def test_clean_verified_scenario_allowed_for_sandbox():
    assert migration_gate(MigrationScenario()) == (True, ())

def test_dirty_tree_blocks_mutation():
    assert "local_mutation_blocked" in migration_gate(MigrationScenario(dirty_local_tree=True))[1]

def test_missing_canonical_sources_blocks():
    assert "canonical_authority_missing" in migration_gate(MigrationScenario(canonical_sources_available=False))[1]

def test_cross_project_evidence_blocks():
    assert "cross_project_evidence_blocked" in migration_gate(MigrationScenario(project_scope_matches=False))[1]

def test_red_ci_blocks():
    assert "red_or_unknown_ci" in migration_gate(MigrationScenario(exact_head_ci_green=False))[1]

def test_unapproved_paid_action_blocks():
    assert "unapproved_paid_action" in migration_gate(MigrationScenario(paid_action_requested=True))[1]

def test_approved_paid_action_not_blocked_by_this_gate():
    assert migration_gate(MigrationScenario(paid_action_requested=True,exact_paid_approval=True))[0]

def test_unapproved_outbound_blocks():
    assert "unapproved_outbound" in migration_gate(MigrationScenario(outbound_requested=True))[1]

def test_global_activation_claim_without_readback_blocks():
    assert "unverified_global_activation" in migration_gate(MigrationScenario(global_activation_claimed_without_readback=True))[1]
