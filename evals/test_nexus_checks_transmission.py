"""Tests for nexus_checks/transmission.py (docs/system/TRANSMISSION_AUDIT_STEEL_2026-09-26.md
turned into an executable check).

Numbers that were checked against the audit and did NOT make the CLAIMS
registry, because slab_line_design has no function that produces them (left
out rather than faked, per the task): the gearbox "rated power >=1800/>=2200
kW" (audit M12, UNSUPPORTED), the "(A) 25:1" comparison reference (an
explicitly unverified vendor number), and the stand's "nominal capacity
>=6 MN" (audit M24, sourced to EXEC/SLAB, not Package A or the model). All
three are recorded in transmission.CLAIMS_INPUT with source="input" instead.
"""
from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path

import pytest

from nexus_checks import transmission as t

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs" / "procurement"


@pytest.fixture(scope="module")
def model():
    return t._load_model(REPO)


# ---- (a) the real RFIs pass ------------------------------------------------
def test_a_real_rfis_pass(model):
    findings = t.check(model, DOCS)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == [], "\n".join(f.fmt() for f in errors)


def test_a_all_model_claims_are_exercised(model):
    # Every "model" claim's glob must actually find its file(s) in the real
    # tree - a claim that only ever hits its own "file not found" WARN branch
    # would silently never be checked.
    findings = t.check(model, DOCS)
    warns = {(f.rule, f.path) for f in findings if f.severity == "WARN"}
    assert warns == set(), warns


# ---- (b) a wrong number fails, with the right claim id ---------------------
def test_b_wrong_number_fails_with_right_claim_id(tmp_path, model):
    src = DOCS / "RFQ-MAIN-GEARBOX_EN_v5_2026-09-23.md"
    text = src.read_text(encoding="utf-8")
    assert "≥685 kN·m" in text
    (tmp_path / src.name).write_text(text.replace("≥685 kN·m", "≥655 kN·m"), encoding="utf-8")

    findings = t.check(model, tmp_path)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert len(errors) == 1, [f.fmt() for f in errors]
    assert errors[0].rule == "gearbox-guaranteed-peak-685"
    assert "655" in errors[0].message and "681.8" in errors[0].message


# ---- (c) a model-constant change (not a document edit) also fails it ------
def test_c_monkeypatched_model_constant_breaks_the_claim(model, monkeypatch):
    """Proves the check tracks the MODEL, not a frozen number: the documents
    are untouched here, only slab_line_design.mass_balance is monkeypatched
    to double the mill's throughput."""
    real = model.mass_balance()
    doubled = dataclasses.replace(real, slabs_per_hour=real.slabs_per_hour * 2)
    monkeypatch.setattr(model, "mass_balance", lambda rate_tph=20.0: doubled)

    findings = t.check(model, DOCS)
    errors = {f.rule for f in findings if f.severity == "ERROR"}
    # accel+brake and reversals events/h both scale with slabs_per_hour;
    # doubling it must break both, against the unmodified real documents.
    assert "accel-brake-204-374" in errors
    assert "reversals-85-170" in errors
    # a claim that never touches slabs_per_hour must be untouched
    assert "gearbox-guaranteed-peak-685" not in errors


# ---- (d) EN and ZH are both checked ----------------------------------------
def test_d_zh_only_error_is_caught_independently_of_en(tmp_path, model):
    en_src = DOCS / "RFQ-REVERSING-STAND_EN_v5_2026-09-23.md"
    zh_src = DOCS / "RFQ-REVERSING-STAND_ZH_v5_2026-09-23.md"
    shutil.copy(en_src, tmp_path / en_src.name)  # EN twin: untouched
    zh_text = zh_src.read_text(encoding="utf-8")
    assert "中心距约646毫米" in zh_text
    (tmp_path / zh_src.name).write_text(
        zh_text.replace("中心距约646毫米", "中心距约900毫米"), encoding="utf-8")

    findings = t.check(model, tmp_path)
    errors = [f for f in findings if f.severity == "ERROR"]
    zh_errors = [f for f in errors if zh_src.name in f.path]
    en_errors = [f for f in errors if en_src.name in f.path]
    assert any(f.rule == "pinion-centre-646mm" for f in zh_errors), [f.fmt() for f in errors]
    assert en_errors == [], [f.fmt() for f in en_errors]  # EN passes on its own


def test_d_en_only_error_is_caught_independently_of_zh(tmp_path, model):
    en_src = DOCS / "RFQ-REVERSING-STAND_EN_v5_2026-09-23.md"
    zh_src = DOCS / "RFQ-REVERSING-STAND_ZH_v5_2026-09-23.md"
    en_text = en_src.read_text(encoding="utf-8")
    assert "centre distance ≈646 mm" in en_text
    (tmp_path / en_src.name).write_text(
        en_text.replace("centre distance ≈646 mm", "centre distance ≈900 mm"), encoding="utf-8")
    shutil.copy(zh_src, tmp_path / zh_src.name)  # ZH twin: untouched

    findings = t.check(model, tmp_path)
    errors = [f for f in findings if f.severity == "ERROR"]
    en_errors = [f for f in errors if en_src.name in f.path]
    zh_errors = [f for f in errors if zh_src.name in f.path]
    assert any(f.rule == "pinion-centre-646mm" for f in en_errors), [f.fmt() for f in errors]
    assert zh_errors == [], [f.fmt() for f in zh_errors]  # ZH passes on its own


# ---- deliberately-stale (source="input") claims are listed, never checked -
def test_input_claims_are_never_evaluated():
    for claim in t.CLAIMS_INPUT:
        assert claim.source == "input"
        assert claim.compute is None
    # check() only iterates CLAIMS (model claims); CLAIMS_INPUT is a separate
    # list precisely so these never gate CI.
    assert set(t.CLAIMS_INPUT).isdisjoint(t.CLAIMS)


# ---- CLI wiring -------------------------------------------------------------
def test_cli_transmission_flag_passes_on_real_repo(capsys):
    from nexus_checks.__main__ import main
    rc = main(["--transmission", "--repo", str(REPO)])
    out = capsys.readouterr().out
    assert "ERROR] transmission/" not in out
    assert rc == 0


def test_cli_transmission_defaults_repo_to_cwd(monkeypatch):
    # Contract changed at integration: --transmission (like --state) uses --repo or ".",
    # so CI can run it without --repo (which would also trigger git_health on a
    # detached, shallow checkout).
    from pathlib import Path
    from nexus_checks.__main__ import main
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    assert main(["--transmission"]) == 0
