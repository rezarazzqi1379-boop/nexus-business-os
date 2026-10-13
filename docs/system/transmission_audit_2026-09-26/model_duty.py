import sys, math
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import slab_line_design as m
mb = m.mass_balance()
S = {t: m.build_schedule(t, "balanced", grade="S355JR") for t in m.THICKNESS_TARGETS_MM}
print("motor_duty default model (drivetrain_j=50) max_rpm=700, ratio 7.1, base 350")
for kw in (1600, 2000):
  for t in (30.0, 20.0, 12.0, 6.0):
    s = S[t]; c = m.cycle_summary(s)["cycle_s"]
    row = []
    for jr in (250, 450, 750):
        for a in (2.0, 3.0, 4.0):
            d = m.motor_duty(s, kw, 350, 7.1, c, mb.slabs_per_hour, accel_time_s=a, max_rpm=700, motor_rotor_j=jr)
            cc = m.commutation_check(s, kw, 350, 7.1, d.accel_torque_nm)
            row.append(f"J{jr}/{a:.0f}s acc{d.accel_torque_nm/1e3:.1f} rms{d.thermal_rms_nm/1e3:.1f} th{d.thermal_utilisation*100:.0f}% roll{cc['worst_rolling_utilisation']*100:.0f}% rev{cc['reversal_utilisation']*100:.0f}% ev/h{d.reversals_per_hour:.0f}")
    print(kw, t, "\n   " + "\n   ".join(row))
