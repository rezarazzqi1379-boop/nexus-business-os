import sys
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import slab_line_design as m
for ip in (12.0, 8.0, 5.0, 3.0):
    s = m.build_schedule(10.0, "balanced", grade="S355JR", interpass_seconds=ip)
    cs = m.cycle_summary(s, interpass_seconds=ip)
    print(f"10mm interpass {ip:4.1f}s: finish {s[-1].exit_temp_c:.0f} C  cycle {cs['cycle_s']:.0f} s  {cs['tph']:.1f} t/h")
for T0 in (1250.0, 1280.0):
    s = m.build_schedule(8.0, "balanced", grade="S355JR", entry_temp_c=T0)
    print(f"8mm furnace {T0}: finish {s[-1].exit_temp_c:.0f}")
for e in (0.75, 0.80, 0.85):
    s = m.build_schedule(10.0, "balanced", grade="S355JR", emissivity=e)
    print(f"10mm emissivity {e}: finish {s[-1].exit_temp_c:.0f}")
# friction-only sensitivity at 12 mm, S235 (SLAB §6.5 'fixed reduction rule')
for mu in (0.25, 0.30, 0.35):
    m.SCENARIOS["_t"] = dict(mu=mu, max_reduction=0.25, bite_utilisation=0.90, basis="audit")
    s = m.build_schedule(12.0, "_t", grade="S235JR"); w = m.worst_cases(s); cs = m.cycle_summary(s)
    print(f"mu {mu}: passes {len(s)} maxF {w['max_force'].force_n/1e6:.2f} maxT {w['max_torque'].torque_roll_nm/1e3:.1f} cycle {cs['cycle_s']:.0f}")
del m.SCENARIOS["_t"]
