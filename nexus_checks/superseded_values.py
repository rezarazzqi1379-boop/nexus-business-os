"""Superseded-value linter.

Origin (FM-007; audit F11, independent review I1/I7): numbers that the project had
already corrected kept reappearing in new documents because the older source
was still readable and carried no warning (ratio 1:12.5, pinion centre 618 mm,
gearbox weight 8-16 t, 238 "reversals"/h that were really accelerations plus
brakings, 1000 kW regenerative power). The author (Claude) nearly quoted one
of them again on the day it was audited.

Rule: a line that uses a superseded value is an ERROR unless the same line
marks it as history (superseded / errata / retracted / was / منسوخ / پس گرفته ...).

Deliberate limitation: numbers collide across meanings. "1250 kW" is both the
SUPERSEDED billet-era AC motor and the engineer's 2026-09-23 DC motor spec, so
the rule matches only the full superseded context (with "999 rpm" or AC /
wound-rotor wording), never the bare number. Add rules the same way: narrow
pattern, cited source, replacement value.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import Finding


@dataclass(frozen=True)
class Rule:
    rid: str
    pattern: re.Pattern
    replacement: str
    source: str
    exempt: re.Pattern | None = None   # line-level context that makes the use legitimate
    current: re.Pattern | None = None  # if the current value is on the same line, the line
                                       # describes the change (old -> new): not an error


def _r(p: str) -> re.Pattern:
    return re.compile(p, re.I)


# Persian digits appear in the project's Persian documents; normalise first.
_FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹٫", "0123456789.")

RULES: list[Rule] = [
    Rule("SV-ratio-12.5", _r(r"1\s*:\s*12\.5\b|\bi\s*=\s*12\.5\b|ratio\s+12\.5\b"),
         "~1:7.1 (RFQ range 6.3-8.0)", "Package A §3.3, §4.1; Exec Summary",
         current=_r(r"7\.1")),
    Rule("SV-pinion-618", _r(r"\b61[58]\s*(?:mm|میلی|to\s*620)|615\s*(?:to|تا|–|-)\s*620"),
         "~646 mm preliminary (engineer 2026-09-23 says 600: keep both)", "Package A §4.4, T-I",
         current=_r(r"\b646\b")),
    Rule("SV-gbx-weight-8-16", _r(r"\b8\s*(?:–|-|to|تا)\s*16\s*(?:t\b|ton|تن)"),
         "no weight declared; vendor scope", "Package A §4.3"),
    Rule("SV-reversals-238", _r(r"\b238\b(?![- ]?(?:line|lines|سطر|行)\b)"),  # "238-line file" is a length, not duty
         "85-170 reversals/h by thickness (238 = accelerations+brakings)", "Package A §8.4, T-3",
         exempt=_r(r"accel|brak|شتاب|ترمز|加速|制动")),
    Rule("SV-regen-1000kW", _r(r"(?:regenerat|بازگشت|回馈)[^\n]{0,40}1000\s*kW|1000\s*kW[^\n]{0,20}(?:regenerat|回馈)"),
         ">=650 kW peak", "Package A §8.1", current=_r(r"\b650\s*kW")),
    Rule("SV-billet-150x150", _r(r"150\s*[x×]\s*150\s*[x×]?\s*3150|\b3150\s*mm"),
         "slab 400x125x3000", "SUPERSEDED_NOTICE_2026-09-21"),
    Rule("SV-ac-1250kW-999", _r(r"1250\s*kW[^\n]{0,30}999\s*rpm|wound[- ]rotor[^\n]{0,40}1250"),
         "DC main drive (1600/2000 kW Package A; 1250 kW DC engineer claim)", "SUPERSEDED_NOTICE_2026-09-21"),
    Rule("SV-ratio-9.8", _r(r"1\s*:\s*9\.8\b"),
         "billet-era existing-line ratio, history only", "SUPERSEDED_NOTICE_2026-09-21"),
]

HISTORY_MARKERS = _r(
    r"supersed|errata|retract|withdrawn|was\b|previous|earlier|old\b|history|"
    r"منسوخ|پس گرفت|قبلی|پیشین|اصلاح|رد شد|رد کرده|جایگزین|←|"
    r"取代|已废止")


def check_file(path: Path) -> list[Finding]:
    out: list[Finding] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.translate(_FA)
        for rule in RULES:
            if not rule.pattern.search(line) or HISTORY_MARKERS.search(raw):
                continue
            if rule.exempt is not None and rule.exempt.search(raw):
                continue
            if rule.current is not None and rule.current.search(line):
                continue
            out.append(Finding("superseded_values", "ERROR", str(path), i, rule.rid,
                               f"superseded value; current: {rule.replacement} [{rule.source}]"))
    return out


def check_paths(paths: list[Path]) -> list[Finding]:
    res: list[Finding] = []
    for p in paths:
        res.extend(check_file(p))
    return res
