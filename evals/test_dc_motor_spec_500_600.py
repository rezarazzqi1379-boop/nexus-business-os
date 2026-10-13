"""Pins the 2026-09-30 check of the owner's DC motor spec (1-2.5 MW, 500-600 rpm)
against slab_line_design (FM-010: compare new work with the engineering basis).

A 500-600 rpm base motor at 2:1 field weakening needs a 10:1 or 12.5:1 gearbox,
not Package A's 7.1:1. If a motor with this spec is bought, the gearbox ratio in
any gearbox RFI must change with it.
"""
import slab_line_design as m


def _opt(kw, base, fw, t=30.0, sc="balanced"):
    return m.build_dc_option("t", m.build_schedule(t, sc), kw, base, fw, "")


def test_500_rpm_base_needs_10_to_1_and_600_needs_12_5():
    assert _opt(1600, 500, 2.0).gear_ratio == 10.0
    assert _opt(1600, 600, 2.0).gear_ratio == 12.5
    assert _opt(1600, 350, 2.0).gear_ratio == 7.1       # Package A reference, unchanged


def test_1_6_mw_at_500_rpm_covers_every_target_in_the_balanced_case():
    for t in m.THICKNESS_TARGETS_MM:
        assert _opt(1600, 500, 2.0, t).feasible


def test_1_mw_fails_the_heavy_passes_in_the_aggressive_case():
    assert not _opt(1000, 600, 2.0, 30.0, "aggressive").feasible
    assert _opt(2000, 500, 2.0, 30.0, "aggressive").feasible
