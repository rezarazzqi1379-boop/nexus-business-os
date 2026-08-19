import pytest

from nexus_core.causal_claims import CausalEvidence, causal_confidence, may_use_causal_language


def test_observational_only_never_becomes_causal_from_volume_alone():
    item = CausalEvidence(
        claim_id="claim-1",
        design="observational_only",
        evidence_refs=("trace:1",),
        counterfactual_defined=False,
        assumptions_documented=True,
        confounding_addressed=False,
        sample_size=10000,
    )
    assert causal_confidence(item) == "attribution_only"
    assert may_use_causal_language(item) is False


def test_quasi_experiment_requires_counterfactual_and_confounding_controls():
    item = CausalEvidence(
        claim_id="claim-2",
        design="quasi_experimental",
        evidence_refs=("experiment:1",),
        counterfactual_defined=True,
        assumptions_documented=True,
        confounding_addressed=False,
        sample_size=200,
    )
    assert causal_confidence(item) == "weak"


def test_replicated_randomized_evidence_can_reach_strong():
    item = CausalEvidence(
        claim_id="claim-3",
        design="randomized",
        evidence_refs=("exp:a", "exp:b"),
        counterfactual_defined=True,
        assumptions_documented=True,
        confounding_addressed=True,
        sample_size=100,
        replicated=True,
    )
    assert causal_confidence(item) == "strong"
    assert may_use_causal_language(item) is True


def test_adjusted_observational_stays_limited():
    item = CausalEvidence(
        claim_id="claim-4",
        design="observational_adjusted",
        evidence_refs=("analysis:1",),
        counterfactual_defined=True,
        assumptions_documented=True,
        confounding_addressed=True,
        sample_size=500,
    )
    assert causal_confidence(item) == "limited"
    assert may_use_causal_language(item) is False


def test_invalid_sample_fails_closed():
    item = CausalEvidence(
        claim_id="claim-5",
        design="randomized",
        evidence_refs=("exp:1",),
        counterfactual_defined=True,
        assumptions_documented=True,
        confounding_addressed=True,
        sample_size=0,
    )
    with pytest.raises(ValueError, match="invalid_sample_size"):
        causal_confidence(item)
