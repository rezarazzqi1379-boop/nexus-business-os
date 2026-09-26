"""ENGINEER_SPEC check: 1:25, DC 1250 kW, slower mill. Model re-run with a lower speed ceiling
by substituting the module's speed-ramp function (analysis only; no file changed)."""
import sys, math
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import slab_line_design as m
orig = m.pass_speed_m_s
mb = m.mass_balance()
print("Surface speed v = pi*D*n/(60*i):")
for D in (600, 620):
    print(" D", D, [(n, round(math.pi*D/1000*n/60/25, 3)) for n in (400, 500, 700, 1000, 1200)])
print("Linear scaling claims: 2040*1.5/2.86 =", round(2040*1.5/2.86), " 2040*1.8/2.86 =", round(2040*1.8/2.86), " v at 1250 kW =", round(1250/2040*2.86, 2))
for base in (400, 500):
    tb = 1250e3/(2*math.pi*base/60)
    print(f" 1250 kW base {base}: base torque {tb/1e3:.2f} kN.m; x25 = {tb*25/1e3:.0f}; x25x0.941 = {tb*25*0.9409/1e3:.0f}; x25x0.899 = {tb*25*0.8992/1e3:.0f} kN.m; roll speed at base {math.pi*0.6*base/60/25:.3f} m/s")
for vmax in (3.0, 1.75, 1.5, 1.25, 1.0):
    m.pass_speed_m_s = (lambda i, n, v_max=vmax, v_first=min(0.8, vmax): orig(i, n, v_max=v_max, v_first=v_first))
    print(f"\n=== v_max {vmax} m/s (S355JR balanced, first pass {min(0.8,vmax)} m/s)")
    for t in (30.0, 20.0, 15.0, 12.0, 10.0, 6.0):
        s = m.build_schedule(t, "balanced", grade="S355JR")
        cs = m.cycle_summary(s)
        wp = m.worst_cases(s)["max_power"]; wt = m.worst_cases(s)["max_torque"]
        rolling = cs["rolling_s"]
        rev = sum(m.reverse_time_s(p.speed_m_s, 3.0, max_line_speed=vmax) for p in s[:-1])
        # motor check 1250 kW, i=25, base 400/500 rpm, eta .899
        chk = []
        for base in (400, 500):
            r = m.motor_at_operating_point(wp, 1250, base, 25.0)
            chk.append(f"b{base}: n{r['motor_rpm']:.0f} shaftP{r['motor_shaft_power_kw']:.0f} {r['fraction_of_continuous']*100:.0f}%cont {r['fraction_of_envelope']*100:.0f}%env")
        print(f" {t:4.0f}mm n{len(s):2d} rolling {rolling:5.1f}s cyc(model,8s) {cs['cycle_s']:5.0f}s cycA(roll+rev3s+30) {rolling+rev+30:5.0f}s  finish {s[-1].exit_temp_c:5.0f}C  "
              f"maxP roll {wp.power_kw:5.0f}kW (pass {wp.index}, v{wp.speed_m_s:.2f}) shaft {wp.power_kw/0.8992:5.0f}kW maxT {wt.torque_roll_nm/1e3:5.1f} | " + " ; ".join(chk))
m.pass_speed_m_s = orig
