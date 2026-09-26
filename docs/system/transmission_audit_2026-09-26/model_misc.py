import sys, math
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import slab_line_design as m
mb = m.mass_balance()
print("Scenario sensitivity (max force MN / max torque kN.m / max neck MPa / passes):")
for g in ("S355JR","S235JR"):
  for sc in ("conservative","balanced","aggressive"):
    r=[]
    for t in (30.0,12.0,6.0):
        s=m.build_schedule(t,sc,grade=g); w=m.worst_cases(s)
        r.append(f"{t:.0f}mm F{w['max_force'].force_n/1e6:.2f} T{w['max_torque'].torque_roll_nm/1e3:.0f} P{w['max_power'].power_kw:.0f} neck{w['max_neck_stress'].neck_stress_mpa:.0f} defl{w['max_deflection'].deflection_mm:.3f} n{len(s)} bexit{s[-1].exit_b:.1f}")
    print(g, sc, " | ".join(r))
F=5.12e6
print("neck stress 5.12MN:", round(m.neck_bending_stress_mpa(F),1), " barrel defl:", round(m.barrel_deflection_mm(F),3), " stretch 3/8 MN/mm:", round(m.stand_stretch_mm(F,8),2), round(m.stand_stretch_mm(F,3),2))
print("lateral margin:", m.lateral_margin_mm())
# pinion centre
for t in (12.0, 6.0):
    s=m.build_schedule(t,"balanced",grade="S355JR")
    print(t, "new only", m.optimal_pinion_centre_mm(s), "\n    worn560", m.optimal_pinion_centre_mm(s, diameter_worn_mm=560.0))
    o=m.optimal_pinion_centre_mm(s, diameter_worn_mm=560.0)
    for c in (618, 646, 648.5, 645.5):
        print(f"    centre {c}: worst angle 1500 {max(m.spindle_angle_deg(c,x,1500) for x in (o['range_low_mm'],o['range_high_mm'])):.2f} deg; 1800 {max(m.spindle_angle_deg(c,x,1800) for x in (o['range_low_mm'],o['range_high_mm'])):.2f}")
s12=m.build_schedule(12.0,"balanced",grade="S355JR")
print("pass exit gaps 12mm:", [round(p.exit_h,1) for p in s12])
print("ENGINEER centre 600, spindle 1500:")
for D in (600,620):
    for lab,gap in (("entry 125",125.0),("pass1 exit",s12[0].exit_h),("30mm",30.0),("6mm",6.0)):
        print(f"   D{D} {lab}: {m.spindle_angle_deg(600, D+gap, 1500):.2f} deg")
# Engineer config commutation / reversal check at 1:25, 1250 kW
orig=m.pass_speed_m_s
for vmax,nmax in ((1.5,1200),(1.0,1000)):
    m.pass_speed_m_s=(lambda i,n,v_max=vmax: orig(i,n,v_max=v_max,v_first=0.8))
    for base in (400,500):
        for t in (30.0,12.0):
            s=m.build_schedule(t,"balanced",grade="S355JR"); c=m.cycle_summary(s)["cycle_s"]
            out=[]
            for jr in (250,450,750):
                for a in (2.0,3.0,4.0):
                    d=m.motor_duty(s,1250,base,25.0,c,mb.slabs_per_hour,accel_time_s=a,max_rpm=nmax,motor_rotor_j=jr)
                    cc=m.commutation_check(s,1250,base,25.0,d.accel_torque_nm)
                    out.append(f"J{jr}/{a:.0f}:rev{cc['reversal_utilisation']*100:.0f}%")
            ntop=max(p.roll_rpm for p in s)*25
            print(f"1250kW base{base} vmax{vmax} {t:.0f}mm n_top {ntop:.0f} env {m.commutation_overload_limit(ntop,base):.2f} rolling util {cc['worst_rolling_utilisation']*100:.0f}% th {d.thermal_utilisation*100:.0f}% | "+" ".join(out))
m.pass_speed_m_s=orig
# comparison: Package A 1600/350/7.1 reversal util at same grid is in model_duty.py output
# Gearbox motor-side torque capacity vs gearbox spec
for kw in (1600,2000):
    tb=kw*1e3/(2*math.pi*350/60)
    print(f"{kw} kW base torque {tb/1e3:.2f}; at gearbox output (x7.1x0.9409): cont {tb*7.1*0.9409/1e3:.0f}, 1.5x {1.5*tb*7.1*0.9409/1e3:.0f}, 2.0x {2*tb*7.1*0.9409/1e3:.0f} kN.m")
print("gearbox rated power implied by 330/405 kN.m at 49.3 rpm:", round(330e3*2*math.pi*(350/7.1)/60/1e3), round(405e3*2*math.pi*(350/7.1)/60/1e3), " 1600/0.899", round(1600/0.8992), " 2000/0.899", round(2000/0.8992))
print("reversal count annual:", [round(r*2400) for r in (84.93, 169.85)])
