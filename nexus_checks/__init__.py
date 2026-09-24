"""NEXUS failure-mining checks.

Each rule in this package exists because a real error happened in a NEXUS
project and was caught late (see FM-005..FM-008 in
.nexus/expert_foundry/registers/ENGINEERING_FAILURE_MEMORY.md). The point is that the same class of error cannot pass silently a second time.

All checks are read-only, stdlib-only, and return a list of Finding objects.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    check: str        # e.g. "vendor_hygiene"
    severity: str     # "ERROR" blocks release; "WARN" needs a human look
    path: str
    line: int         # 1-based; 0 when the finding is file-level
    rule: str         # rule id, audit finding id (e.g. "F14"), see FM-005..FM-008
    message: str

    def fmt(self) -> str:
        loc = f"{self.path}:{self.line}" if self.line else self.path
        return f"[{self.severity}] {self.check}/{self.rule} {loc} — {self.message}"
