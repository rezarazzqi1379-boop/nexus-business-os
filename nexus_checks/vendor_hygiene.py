"""Vendor-facing document hygiene.

Origin (FM-005; audit F14): RFQ drafts v1-v4 carried internal content inside
files meant for vendors: competitor recipient lists, internal QA-log pointers,
supersession notes naming internal files, and one real unrelated company name
used as a "warning". Three review rounds approved them.

Rule: a vendor-facing file may contain NO internal marker. In --release mode
the draft banner line itself is also an error (it must be deleted from the
outgoing copy only).
"""
from __future__ import annotations

import re
from pathlib import Path

from . import Finding

# Case-insensitive plain substrings that must never reach a vendor.
INTERNAL_MARKERS = [
    "internal", "qa_log", "qa log", "suggested recipient", "建议收件人",
    "superseded", "supersedes", "取代", "package a", "broker",
    "dispatch sheet", "audit", "do not send", "not vetted", "red flag",
]

# Names that were rejected, confused, or belong to competitors of the recipient.
# Kept here (not in the RFI) precisely so that a copy-paste slip is caught.
NAME_WATCHLIST = [
    "上海东方电气", "南京年达", "无锡宇顺", "上海臻工", "杭州新恒力", "江苏航天",
    "nianda", "yushun", "isunsteel", "prime metallurgy", "hengli", "fortune electric",
    "china electric (shanghai)", "aerospace power", "净环热", "jinghuanre", "凤谷",
    "力杰", "伟盛", "lixing", "南高齿", "重齿", "东力",
]

DRAFT_BANNER = re.compile(r"(DRAFT v\d|草稿第\d版|NOT APPROVED FOR RELEASE|未批准发送)", re.I)
# The banner line is allowed to contain words like "DRAFT"; other markers are
# checked on every other line.


def check_file(path: Path, release: bool = False) -> list[Finding]:
    out: list[Finding] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for i, raw in enumerate(text.splitlines(), 1):
        low = raw.lower()
        if DRAFT_BANNER.search(raw):
            if release:
                out.append(Finding("vendor_hygiene", "ERROR", str(path), i, "F14-banner",
                                   "draft banner still present in an outgoing copy"))
            continue
        for m in INTERNAL_MARKERS:
            if m in low:
                out.append(Finding("vendor_hygiene", "ERROR", str(path), i, "F14-internal",
                                   f"internal marker '{m}' in vendor-facing text"))
        for n in NAME_WATCHLIST:
            if n.lower() in low:
                out.append(Finding("vendor_hygiene", "ERROR", str(path), i, "F14-name",
                                   f"company name '{n}' in vendor-facing text "
                                   "(competitor, rejected or confusable name)"))
    return out


def check_paths(paths: list[Path], release: bool = False) -> list[Finding]:
    res: list[Finding] = []
    for p in paths:
        res.extend(check_file(p, release=release))
    return res
