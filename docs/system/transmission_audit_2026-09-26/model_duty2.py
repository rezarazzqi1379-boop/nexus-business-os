import sys, math
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import slab_line_design as m
mb = m.mass_balance()
S = {t: m.build_schedule(t, "balanced", grade="S355JR") for t in m.THICKNESS_TARGETS_MM}
# Reproduce T-E on the hypothesis drivetrain_j excluded (rotor passed as jr-50)
for t in m.THICKNESS_TARGETS_MM:
    s = S[t]; c = m.cycle_summary(s)["cycle_s"]
    out=[]
    for jr,a in ((250,2.0),(450,3.0),(750,2.0)):
        d = m.motor_duty(s, 1600, 350, 7.1, c, mb.slabs_per_hour, accel_time_s=a, max_rpm=700, motor_rotor_j=jr-50)
        cc = m.commutation_check(s, 1600, 350, 7.1, d.accel_torque_nm)
        out.append(f"J{jr}/{a:.0f} acc{d.accel_torque_nm/1e3:.2f} rms{d.thermal_rms_nm/1e3:.1f} {d.thermal_utilisation*100:.0f}% rev{cc['reversal_utilisation']*100:.0f}%")
    print(t, " | ".join(out))
