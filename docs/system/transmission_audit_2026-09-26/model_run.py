"""Transmission audit: run slab_line_design.py and dump every consequential output."""
import sys, math, json
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import slab_line_design as m

mb = m.mass_balance()
print(f"MASS slab {mb.slab_mass_kg:.1f} kg  slabs/h {mb.slabs_per_hour:.3f}  furnace cycle {mb.cycle_time_s:.1f} s")
print(f"TOTAL_SF {m.total_service_factor():.4f}")
print(f"bite mu^2R bal {m.max_draft_bite_mm(0.30):.2f}  exact {m.max_draft_bite_exact_mm(0.30):.2f}  roll rpm@3 {m.roll_rpm(3.0):.2f}")
for grade in ("S355JR", "S235JR"):
    print(f"\n==== {grade} balanced, reversing, interpass 8 s")
    print("t  n  maxF_MN  maxT_kNm  perRoll  perSpindle  maxP_kW  lenmax  finishT  cyc_s(model)  tph  rev/slab rev/h accbrk/h  rolling_s  sum_rev_s  cycA=roll+rev+30")
    for t in m.THICKNESS_TARGETS_MM:
        s = m.build_schedule(t, "balanced", grade=grade)
        w = m.worst_cases(s)
        cs = m.cycle_summary(s)
        rev = m.reversals_per_slab(s)
        spl = m.torque_per_roll_nm(w["max_torque"].torque_roll_nm)
        rolling = sum(p.rolling_time_s for p in s)
        revs = sum(m.reverse_time_s(p.speed_m_s, 3.0) for p in s)  # accel 3 s? test below
        print(f"{t:4.0f} {len(s):2d} {w['max_force'].force_n/1e6:6.2f} {w['max_torque'].torque_roll_nm/1e3:8.1f} "
              f"{spl['nominal_per_roll_nm']/1e3:6.1f} {spl['design_per_spindle_nm']/1e3:6.1f} {w['max_power'].power_kw:7.0f} "
              f"{w['max_length'].piece_length_m:6.1f} {s[-1].exit_temp_c:6.0f} {cs['cycle_s']:7.1f} {cs['tph']:5.1f} {rev:3d} "
              f"{rev*mb.slabs_per_hour:6.1f} {2*len(s)*mb.slabs_per_hour:6.1f} {rolling:6.1f}")
