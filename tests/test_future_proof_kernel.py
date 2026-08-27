from nexus_core.future_proof_kernel import CapabilityCandidate, assess_capability


def candidate(**overrides):
    base = dict(
        capability_id="CAP-TEMPORAL-MEMORY",
        solves_repeated_problem=True,
        existing_capability_sufficient=False,
        acceptance_test_defined=True,
        rollback_defined=True,
        project_isolation_proven=True,
        provenance_supported=True,
        approval_boundary_preserved=True,
        portable_data_contract=True,
        measurable_outcome_defined=True,
    )
    base.update(overrides)
    return CapabilityCandidate(**base)


def test_rejects_architecture_for_architecture_sake():
    assert assess_capability(candidate(solves_repeated_problem=False)).lifecycle == "REJECT"


def test_rejects_duplicate_capability_when_existing_is_sufficient():
    assert assess_capability(candidate(existing_capability_sufficient=True)).lifecycle == "REJECT"


def test_missing_project_isolation_stays_research_only():
    result = assess_capability(candidate(project_isolation_proven=False))
    assert result.lifecycle == "RESEARCH"
    assert any("cross-project" in gate for gate in result.gates)


def test_missing_provenance_stays_research_only():
    assert assess_capability(candidate(provenance_supported=False)).lifecycle == "RESEARCH"


def test_missing_rollback_stays_research_only():
    assert assess_capability(candidate(rollback_defined=False)).lifecycle == "RESEARCH"


def test_live_credentials_force_experiment_even_with_controls():
    result = assess_capability(candidate(live_credentials_required=True))
    assert result.lifecycle == "EXPERIMENT"
    assert any("credentials" in gate for gate in result.gates)


def test_production_mutation_never_self_authorizes():
    result = assess_capability(candidate(production_mutation_required=True))
    assert result.lifecycle == "EXPERIMENT"
    assert any("production" in gate for gate in result.gates)


def test_clean_candidate_still_requires_measured_adoption_gate():
    result = assess_capability(candidate())
    assert result.lifecycle == "ADOPT_CANDIDATE"
    assert any("Adoption Gate" in reason for reason in result.reasons)
