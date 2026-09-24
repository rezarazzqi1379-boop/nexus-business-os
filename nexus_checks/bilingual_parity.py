"""Bilingual (EN/ZH) structural parity.

Origin (FM-006; audit F18, round-3 review point 2): the Chinese RFQ had
five technical asks the English one lacked, because corrections were applied
to one language only. A human spotted it; nothing mechanical did.

Rule: paired files must have the same number of sections (## headings),
numbered items, bullet items and table rows. Equal structure does not prove
equal meaning (F18) - it catches the one-sided edit, which is the common case.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import Finding

SECTION = re.compile(r"^##\s")
NUMBERED = re.compile(r"^\s*\d+\.\s")
BULLET = re.compile(r"^\s*[-*]\s")
TABLE_ROW = re.compile(r"^\|(?!\s*-{3})")  # table lines except the |---| separator


def profile(path: Path) -> dict[str, int]:
    counts = {"sections": 0, "numbered": 0, "bullets": 0, "table_rows": 0}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if SECTION.match(line):
            counts["sections"] += 1
        elif NUMBERED.match(line):
            counts["numbered"] += 1
        elif BULLET.match(line):
            counts["bullets"] += 1
        elif TABLE_ROW.match(line):
            counts["table_rows"] += 1
    return counts


def pair_files(paths: list[Path]) -> list[tuple[Path, Path]]:
    """Pair X_EN_*.md with X_ZH_*.md by replacing the language tag."""
    by_name = {p.name: p for p in paths}
    pairs = []
    for p in paths:
        if "_EN" in p.name:
            zh = p.name.replace("_EN", "_ZH", 1)
            if zh in by_name:
                pairs.append((p, by_name[zh]))
    return pairs


def check_pair(en: Path, zh: Path) -> list[Finding]:
    a, b = profile(en), profile(zh)
    out = []
    for k in a:
        if a[k] != b[k]:
            out.append(Finding("bilingual_parity", "ERROR", f"{en.name} <> {zh.name}", 0, "F18-parity",
                               f"{k}: EN={a[k]} ZH={b[k]}"))
    return out


def check_paths(paths: list[Path]) -> list[Finding]:
    res: list[Finding] = []
    pairs = pair_files(paths)
    for en, zh in pairs:
        res.extend(check_pair(en, zh))
    unpaired = [p for p in paths if ("_EN" in p.name or "_ZH" in p.name)
                and not any(p in pr for pr in pairs)]
    for p in unpaired:
        res.append(Finding("bilingual_parity", "WARN", str(p), 0, "F18-unpaired",
                           "no counterpart in the other language"))
    return res
