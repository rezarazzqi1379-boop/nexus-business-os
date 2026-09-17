"""Prepare (never execute) account-onboarding suggestions for the two lowest-risk,
free-registration data sources identified for FAL-A/FAL-B research: UN Comtrade/ComtradePlus
and ITC Trade Map. Uses this project's own external_account_orchestrator.py exactly as
designed -- this script builds a plan object and prints it; it never submits a form, never
enters payment/identity details, and never calls authorize_commit(). Reza reviews the plan and
completes the actual signup himself in his own browser, per this project's account boundary.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from external_account_orchestrator import AccountTarget, build_onboarding_plan

CANDIDATES = [
    AccountTarget(
        target_id="comtradeplus_free",
        service_name="UN Comtrade / ComtradePlus (free API registration)",
        signup_url="https://comtradeplus.un.org/",
        purpose="Programmatic access to official UN bulk trade statistics (ferroalloys HS 7202) "
                "for FAL-A/FAL-B market-level research.",
        jurisdiction="UN (international body, not a single national jurisdiction)",
        account_owner="Reza",
        expected_cost=0.0,
        requires_kyc=False,
        requires_payment=False,
    ),
    AccountTarget(
        target_id="trademap_free",
        service_name="ITC Trade Map (free registration)",
        signup_url="https://www.trademap.org/",
        purpose="Bilateral trade flow and market-access detail for ferroalloys, complementing "
                "Comtrade for FAL-A/FAL-B research.",
        jurisdiction="ITC / UN-WTO joint agency",
        account_owner="Reza",
        expected_cost=0.0,
        requires_kyc=False,
        requires_payment=False,
    ),
]

plans = []
for target in CANDIDATES:
    plan = build_onboarding_plan(
        target,
        public_fields={"account_owner_name": "Reza", "purpose": target.purpose},
    )
    plans.append(plan)
    print(f"\n=== {target.service_name} ===")
    print(f"stage: {plan.stage}")
    print(f"signup_url: {target.signup_url}")
    print(f"allowed_automatic_steps (Claude may do these): {plan.allowed_automatic_steps}")
    print(f"approval_required_actions (Reza must do these himself): {plan.approval_required_actions}")
    print(f"risk_flags: {plan.risk_flags}")
    print(f"missing_owner_inputs: {plan.missing_owner_inputs}")
    print(f"commit_digest: {plan.commit_digest}")

out_path = Path(__file__).resolve().parent.parent / "data" / "research" / "fal_account_onboarding_plans_2026-09-17.json"
out_path.write_text(
    json.dumps([{**asdict(p), "target": asdict(p.target)} for p in plans], indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(f"\nSaved plans to: {out_path}")
