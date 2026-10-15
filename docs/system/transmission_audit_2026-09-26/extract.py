"""Extract numbers (incl. Persian digits, ٫ decimal, ٬ thousands) from audited docs; EN/ZH parity."""
import re, sys, collections, pathlib
R = pathlib.Path(__file__).resolve().parents[3] / "docs"
FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫٬", "01234567890123456789.,")
NUM = re.compile(r"(?<![A-Za-z0-9.])\d+(?:,\d{3})*(?:\.\d+)?")
def nums(line):
    s = line.translate(FA)
    return [float(x.replace(",", "")) for x in NUM.findall(s)]
docs = {
 "A": "expert_foundry/ENGINEERING_PACKAGE_A_TECHNICAL_2026-09-21.md",
 "SLAB": "expert_foundry/SLAB_LINE_PRELIMINARY_DESIGN_2026-09-21.md",
 "B": "expert_foundry/ENGINEERING_PACKAGE_B_ENGINEER_2026-09-21.md",
 "EXEC": "expert_foundry/ENGINEERING_PACKAGE_EXEC_SUMMARY_2026-09-21.md",
 "CTRL": "expert_foundry/PROJECT_CONTROL_PRJ-STEEL-ROLLING-LINE-01.md",
 "ENGSPEC": "procurement/ENGINEER_SPEC_AND_STOCK_SEARCH_2026-09-23.md",
 "DISPATCH": "procurement/RFI_DISPATCH_SHEET_INTERNAL_v5_2026-09-23.md",
}
for it in ("DC-MOTOR-DRIVE","MAIN-GEARBOX","REVERSING-STAND","FURNACE"):
    for lang in ("EN","ZH"):
        docs[f"{it}_{lang}"] = f"procurement/RFQ-{it}_{lang}_v5_2026-09-23.md"
mode = sys.argv[1] if len(sys.argv) > 1 else "find"
if mode == "find":
    targets = [float(x) for x in sys.argv[2:]]
    for k, p in docs.items():
        for i, line in enumerate((R/p).read_text(encoding="utf-8").splitlines(), 1):
            ns = nums(line)
            hit = [t for t in targets if any(abs(n - t) < 1e-9 for n in ns)]
            if hit:
                print(f"{k}:{i}: {hit} :: {line.strip()[:170]}")
elif mode == "parity":
    for it in ("DC-MOTOR-DRIVE","MAIN-GEARBOX","REVERSING-STAND","FURNACE"):
        en = [ (i,nums(l)) for i,l in enumerate((R/docs[f'{it}_EN']).read_text(encoding='utf-8').splitlines(),1)]
        zh = [ (i,nums(l)) for i,l in enumerate((R/docs[f'{it}_ZH']).read_text(encoding='utf-8').splitlines(),1)]
        ce = collections.Counter(n for _,ns in en for n in ns); cz = collections.Counter(n for _,ns in zh for n in ns)
        print(it, "EN-only:", dict(ce - cz), " ZH-only:", dict(cz - ce))
elif mode == "count":
    tot = 0
    for k, p in docs.items():
        c = sum(len(nums(l)) for l in (R/p).read_text(encoding="utf-8").splitlines())
        tot += c; print(k, c)
    print("TOTAL numeric tokens", tot)
