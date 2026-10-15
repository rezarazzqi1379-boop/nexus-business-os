"""Cell-by-cell check of Package A T-B* (S355) and SLAB §5 (S235) pass tables against the model."""
import pathlib as _pl
ROOT = _pl.Path(__file__).resolve().parents[3]
import sys, re, pathlib
import os; sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import slab_line_design as m
FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹٫٬", "0123456789.,")
def rows(path, start, end):
    L = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    out = []
    for i in range(start-1, end):
        s = L[i].translate(FA)
        if re.match(r"\|\s*\d+\s*\|", s):
            cells = [c.strip() for c in s.strip().strip("|").split("|")]
            out.append((i+1, cells))
    return out
def num(c):
    x = re.findall(r"-?\d+(?:\.\d+)?", c.replace("°",""))
    return float(x[0]) if x else None
A = str(ROOT / "docs" / "expert_foundry" / "ENGINEERING_PACKAGE_A_TECHNICAL_2026-09-21.md")
S = str(ROOT / "docs" / "expert_foundry" / "SLAB_LINE_PRELIMINARY_DESIGN_2026-09-21.md")
tot = bad = 0; issues = []
def cmp(line, name, doc, model, tol):
    global tot, bad
    tot += 1
    if doc is None or abs(doc - model) > tol:
        bad += 1; issues.append(f"line {line} {name}: doc {doc} model {model:.3f}")
# Package A T-B tables: (thickness, first line, last line)
for t, a, b in ((30,101,106),(20,115,121),(12,130,138),(10,147,156),(8,165,174),(6,183,193)):
    s = m.build_schedule(float(t), "balanced", grade="S355JR")
    for (ln, c), p in zip(rows(A, a, b), s):
        # pass|dir|h0|h1|dh|%|Tin|Tout|v|n|len|F|T|Troll|P|time|rev
        cmp(ln,"h0",num(c[2]),p.entry_h,0.051); cmp(ln,"h1",num(c[3]),p.exit_h,0.051); cmp(ln,"dh",num(c[4]),p.draft,0.051)
        cmp(ln,"Tin",num(c[6]),p.entry_temp_c,0.51); cmp(ln,"Tout",num(c[7]),p.exit_temp_c,0.51)
        cmp(ln,"v",num(c[8]),p.speed_m_s,0.0051); cmp(ln,"n",num(c[9]),p.roll_rpm,0.051); cmp(ln,"len",num(c[10]),p.piece_length_m,0.051)
        cmp(ln,"F",num(c[11]),p.force_n/1e6,0.0051); cmp(ln,"T",num(c[12]),p.torque_roll_nm/1e3,0.051); cmp(ln,"Troll",num(c[13]),p.torque_roll_nm/2e3,0.051)
        cmp(ln,"P",num(c[14]),p.power_kw,0.51); cmp(ln,"time",num(c[15]),p.rolling_time_s,0.051); cmp(ln,"rev",num(c[16]),m.reverse_time_s(p.speed_m_s,3.0),0.051)
print(f"Package A T-B30..T-B6: {tot} cells, {bad} mismatches"); [print("  ",x) for x in issues]
tot = bad = 0; issues.clear()
for t, a, b in ((30,183,188),(12,206,214),(6,232,242)):
    s = m.build_schedule(float(t), "balanced", grade="S235JR")
    for (ln, c), p in zip(rows(S, a, b), s):
        # pass|dir|h0|h1|dh|%|b|Tin|Tout|v|n|Lc|alpha|ok|eps|edot|sigma|Q|F|T|P|len|time|conf
        cmp(ln,"b",num(c[6]),p.exit_b,0.051); cmp(ln,"Tin",num(c[7]),p.entry_temp_c,0.51); cmp(ln,"Tout",num(c[8]),p.exit_temp_c,0.51)
        cmp(ln,"v",num(c[9]),p.speed_m_s,0.0051); cmp(ln,"Lc",num(c[11]),p.contact_len,0.051); cmp(ln,"alpha",num(c[12]),p.bite_angle,0.051)
        cmp(ln,"eps",num(c[14]),p.strain,0.00051); cmp(ln,"edot",num(c[15]),p.strain_rate,0.051); cmp(ln,"sigma",num(c[16]),p.flow_stress,0.051)
        cmp(ln,"Q",num(c[17]),p.geometry_q,0.00051); cmp(ln,"F",num(c[18]),p.force_n/1e6,0.0051); cmp(ln,"T",num(c[19]),p.torque_roll_nm/1e3,0.051)
        cmp(ln,"P",num(c[20]),p.power_kw,0.51); cmp(ln,"len",num(c[21]),p.piece_length_m,0.051); cmp(ln,"time",num(c[22]),p.rolling_time_s,0.051)
print(f"SLAB §5 S235 tables: {tot} cells, {bad} mismatches"); [print("  ",x) for x in issues[:20]]
# bearing torque share
worst = 0
for g in ("S235JR","S355JR"):
    for t in m.THICKNESS_TARGETS_MM:
        for p in m.build_schedule(t, "balanced", grade=g):
            tb = m.MU_BEARING*p.force_n*(m.NECK_DIAMETER_RATIO*m.ROLL_DIAMETER_MM/2)*2/1000
            worst = max(worst, tb/p.torque_roll_nm)
print(f"max bearing-torque share of total roll torque (balanced, all t): {worst*100:.1f}%")
