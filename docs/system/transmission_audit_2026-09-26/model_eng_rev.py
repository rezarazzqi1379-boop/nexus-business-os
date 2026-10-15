import sys
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import slab_line_design as m
mb = m.mass_balance(); orig = m.pass_speed_m_s
for vmax in (1.0, 1.5):
    m.pass_speed_m_s = (lambda i, n, v_max=vmax: orig(i, n, v_max=v_max, v_first=0.8))
    s = m.build_schedule(30.0, "balanced", grade="S355JR"); c = m.cycle_summary(s)["cycle_s"]
    ntop = max(p.roll_rpm for p in s) * 25
    for base in (400, 500):
        row = []
        for jr in (250, 450, 750):
            for a in (2.0, 3.0, 4.0):
                d = m.motor_duty(s, 1250, base, 25.0, c, mb.slabs_per_hour, accel_time_s=a, max_rpm=ntop, motor_rotor_j=jr)
                cc = m.commutation_check(s, 1250, base, 25.0, d.accel_torque_nm)
                row.append(f"{jr}/{a:.0f}s:{cc['reversal_utilisation']*100:.0f}%")
        print(f"v_max {vmax} n_top {ntop:.0f} rpm base {base}: " + " ".join(row))
m.pass_speed_m_s = orig
# Package A comparison: 1600/350/7.1 at 3 m/s (model default J incl. drivetrain), 30 mm
s = m.build_schedule(30.0, "balanced", grade="S355JR"); c = m.cycle_summary(s)["cycle_s"]
row=[]
for jr in (250,450,750):
    for a in (2.0,3.0,4.0):
        d = m.motor_duty(s,1600,350,7.1,c,mb.slabs_per_hour,accel_time_s=a,max_rpm=700,motor_rotor_j=jr)
        row.append(f"{jr}/{a:.0f}s:{m.commutation_check(s,1600,350,7.1,d.accel_torque_nm)['reversal_utilisation']*100:.0f}%")
print("PkgA 1600/350/7.1:", " ".join(row))
