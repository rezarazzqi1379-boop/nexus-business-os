"""CLI: python -m nexus_checks [--release] [--repo PATH] [--exclude GLOB] FILES_OR_DIRS...

Vendor hygiene applies to files named RFQ-* / RFI-* (vendor-facing drafts).
Superseded values and bilingual parity apply to every .md given.
Exit code 1 if any ERROR.
"""
from __future__ import annotations

import argparse
import fnmatch
import sys
from pathlib import Path

from . import bilingual_parity, git_health, superseded_values, vendor_hygiene


def _collect(items: list[str]) -> list[Path]:
    files: list[Path] = []
    for it in items:
        p = Path(it)
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        elif p.suffix == ".md":
            files.append(p)
    return files


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="nexus_checks")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--release", action="store_true", help="treat draft banners as errors")
    ap.add_argument("--repo", help="also run git health on this repo")
    ap.add_argument("--exclude", action="append", default=[],
                    help="glob on file name to skip (e.g. superseded archives); repeatable")
    a = ap.parse_args(argv)

    files = [f for f in _collect(a.paths)
             if not any(fnmatch.fnmatch(f.name, pat) for pat in a.exclude)]
    vendor = [f for f in files if f.name.startswith(("RFQ-", "RFI-"))]
    findings = []
    findings += vendor_hygiene.check_paths(vendor, release=a.release)
    findings += superseded_values.check_paths(files)
    findings += bilingual_parity.check_paths(vendor)
    if a.repo:
        findings += git_health.check_repo(Path(a.repo))

    for f in findings:
        print(f.fmt())
    errors = sum(f.severity == "ERROR" for f in findings)
    warns = sum(f.severity == "WARN" for f in findings)
    print(f"-- {len(files)} file(s), {len(vendor)} vendor-facing; {errors} error(s), {warns} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
