import sys, math
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import slab_line_design as m
mb = m.mass_balance()
S = {t: m.build_schedule(t, "balanced", grade="S355JR") for t in m.THICKNESS_TARGETS_MM}
S235 = {t: m.build_schedule(t, "balanced", grade="S235JR") for t in m.THICKNESS_TARGETS_MM}
s30 = S[30.0]
print("30mm S355 passes: i v rpm T_kNm P_kW t_s F_MN Texit revtime(3s)")
for p in s30:
    print(f"  {p.index} {p.speed_m_s:.2f} {p.roll_rpm:.1f} {p.torque_roll_nm/1e3:.1f} {p.power_kw:.0f} {p.rolling_time_s:.1f} {p.force_n/1e6:.2f} {p.exit_temp_c:.0f} {m.reverse_time_s(p.speed_m_s,3.0):.1f}")
for g, sch in (("S355", S), ("S235", S235)):
    for r in (7.1, 12.5):
        tr = m.gearbox_rating_trace(sch[30.0], r, m.cycle_summary(sch[30.0])["cycle_s"])
        print(g, r, {k: (round(v/1e3,1) if isinstance(v,float) and v>1000 else v) for k,v in tr.items()})
lc = m.loss_chain(218.3e3, 7.1, 2)
print("loss_chain 218.3 @7.1 2-stage:", {k: round(v/1e3,2) if k.endswith('nm') else round(v,4) for k,v in lc.items()})
lc1 = m.loss_chain(218.3e3, 7.1, 1)
print("loss_chain 1-stage:", {k: round(v/1e3,2) if k.endswith('nm') else round(v,4) for k,v in lc1.items()})
# output-referred duty spectrum 30 mm
f = m.ETA_SPINDLE*m.ETA_COUPLING*m.ETA_PINION*m.ETA_COUPLING
print("gearbox-output torques 30mm:", [round(p.torque_roll_nm/f/1e3,1) for p in s30], "factor", round(f,4))
pk_out = max(p.torque_roll_nm for p in s30)/f
print(f"bite 2x/3x at gearbox output: {2*pk_out/1e3:.1f} / {3*pk_out/1e3:.1f}; criterion B output-referred {1.5*pk_out/1e3:.1f}; x1.23 {1.5*pk_out*1.23/1e3:.1f}; 3x*1.23 {3*pk_out*1.23/1e3:.1f}")
for kw in (1600, 2000):
    o = m.build_dc_option("x", s30, kw, 350, 2.0, "")
    print(f"DC {kw}/350/FW2: ratio {o.gear_ratio} base torque {o.base_torque_nm/1e3:.2f} roll rpm base {o.roll_rpm_at_base:.1f} max speed {o.max_roll_speed_m_s:.3f} feasible {o.feasible} margin {o.worst_margin_pct:.0f} pass {o.limiting_pass}")
# governing power pass across thicknesses
best = max((w for t in S for w in [m.worst_cases(S[t])["max_power"]]), key=lambda p: p.power_kw)
print("governing power pass:", best.index, best.entry_h, best.exit_h, round(best.speed_m_s,2), round(best.power_kw), round(best.rolling_time_s,1))
for kw in (1600, 2000):
    r = m.motor_at_operating_point(best, kw, 350, 7.1)
    print(kw, {k: round(v,3) if isinstance(v,float) else v for k,v in r.items()})
print("envelope at 350/450/550/650/700:", [round(m.commutation_overload_limit(n,350),2) for n in (350,450,550,650,700)])
# max torque pass at motor
pk = max(s30, key=lambda p: p.torque_roll_nm)
print(f"peak torque pass {pk.index}: motor rpm {pk.roll_rpm*7.1:.0f}; motor torque (eta .899) {pk.torque_roll_nm/7.1/0.8992/1e3:.2f}; cont 1600 at that rpm {1600e3/(2*math.pi*350/60)*min(1,350/(pk.roll_rpm*7.1))/1e3:.2f}")
# Inertia
for jr in (250, 450, 750):
    J = m.inertia_at_motor_kgm2(7.1, motor_rotor_j=jr)
    print(f"J rotor {jr}: J total at motor {J:.1f}; accel torque 700rpm ramps 2/3/4 s: " +
          " ".join(f"{J*(2*math.pi*700/60)/a/1e3:.1f}" for a in (2,3,4)) +
          f" | rotor-only: " + " ".join(f"{jr*(2*math.pi*700/60)/a/1e3:.1f}" for a in (2,3,4)))
    for rj, lab in ((jr, "rotor-only"), (J, "full-train")):
        b = [m.braking_per_stop(rj, 678, d) for d in (2,3,4)]
        b7 = [m.braking_per_stop(rj, 700, d) for d in (2,3,4)]
        print(f"   braking {lab} J={rj:.1f}: E {b[0]['energy_per_stop_mj']:.3f} MJ {b[0]['energy_per_stop_kwh']:.4f} kWh; P@678 2/3/4s " +
              " ".join(f"{x['instantaneous_power_kw']:.0f}" for x in b) + " ; P@700 " + " ".join(f"{x['instantaneous_power_kw']:.0f}" for x in b7))
print("hourly avg regen (J=450, 678rpm):", [round(m.braking_hourly_average_kw(450,678, m.reversals_per_slab(S[t])*mb.slabs_per_hour),1) for t in S])
print("hourly avg regen (full J, rotor 450):", [round(m.braking_hourly_average_kw(m.inertia_at_motor_kgm2(7.1,motor_rotor_j=450),678, m.reversals_per_slab(S[t])*mb.slabs_per_hour),1) for t in S])
print("old 3.7: 238/h x 1.1 MJ =", 238*1.1, "MJ/h ->", 238*1.1e6/3600/1e3, "kW")
