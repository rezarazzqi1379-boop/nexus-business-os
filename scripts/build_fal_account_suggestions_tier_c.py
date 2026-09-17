"""Prepare (never execute) account-onboarding suggestions for the (C)-tier paid commercial
trade-intelligence platforms (Volza, ImportGenius, Panjiva, Tendata). Same boundary as the
(B)-tier script: this only builds and prints/saves plan objects. It never submits a signup
form, never enters payment/identity details, and never calls authorize_commit(). Every plan's
approval_required_actions explicitly lists create_account/accept_terms/link_payment as Reza's
own steps -- and every one of these carries a real risk_flag (financial_commitment and/or
identity_verification_required) plus the compliance note already logged in
docs/research/FAL_DATA_SOURCE_CATALOG.md about US ToS/sanctions exposure for Iran-linked
ferroalloys research. Reza should read that note before acting on any of these.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from external_account_orchestrator import AccountTarget, build_onboarding_plan

# expected_cost left at 0.0 (unknown/variable -- these are quote-on-request or tiered
# subscriptions, not a fixed public price) rather than guessing a number; requires_payment=True
# still forces the financial_commitment risk flag regardless of the placeholder cost value.
CANDIDATES = [
    AccountTarget(
        target_id="volza_trial",
        service_name="Volza (global shipment-level trade data, free-trial tier)",
        signup_url="https://www.volza.com/",
        purpose="Shipment-level import/export records for ferromanganese/ferrosilicon "
                "counterparties across ~200 countries, for FAL-A/FAL-B research.",
        jurisdiction="India (Volza's stated HQ)",
        account_owner="Reza",
        expected_cost=0.0,
        requires_kyc=False,
        requires_payment=True,
    ),
    AccountTarget(
        target_id="importgenius_paid",
        service_name="ImportGenius (customs/shipment trade intelligence)",
        signup_url="https://www.importgenius.com/",
        purpose="Customs/shipment-level trade intelligence searchable by company/product, "
                "for FAL-A/FAL-B counterparty discovery.",
        jurisdiction="United States",
        account_owner="Reza",
        expected_cost=0.0,
        requires_kyc=False,
        requires_payment=True,
    ),
    AccountTarget(
        target_id="panjiva_paid",
        service_name="Panjiva (S&P Global) enterprise trade/supply-chain intelligence",
        signup_url="https://panjiva.com/",
        purpose="Enterprise-grade shipment/supply-chain mapping for ferroalloys "
                "counterparties -- highest compliance-caution item in this catalog given "
                "S&P Global's own regulatory posture as a US financial-data company.",
        jurisdiction="United States (S&P Global)",
        account_owner="Reza",
        expected_cost=0.0,
        requires_kyc=True,
        requires_payment=True,
    ),
    AccountTarget(
        target_id="tendata_paid",
        service_name="Tendata (trade data platform)",
        signup_url="https://www.tendata.com/",
        purpose="Comparable shipment/trade-data platform to Volza/ImportGenius, for "
                "cross-checking FAL-A/FAL-B counterparty candidates against a second provider.",
        jurisdiction="China (Tendata's stated HQ)",
        account_owner="Reza",
        expected_cost=0.0,
        requires_kyc=False,
        requires_payment=True,
    ),
]

plans = []
for target in CANDIDATES:
    plan = build_onboarding_plan(
        target,
        public_fields={"account_owner_name": "Reza", "purpose": target.purpose},
        missing_owner_inputs=(),
    )
    plans.append(plan)
    print(f"\n=== {target.service_name} ===")
    print(f"stage: {plan.stage}")
    print(f"signup_url: {target.signup_url}")
    print(f"risk_flags: {plan.risk_flags}")
    print(f"missing_owner_inputs (Reza must supply, never Claude): {plan.missing_owner_inputs}")
    print(f"approval_required_actions (Reza's own steps): {plan.approval_required_actions}")
    print(f"commit_digest: {plan.commit_digest}")

out_path = Path(__file__).resolve().parent.parent / "data" / "research" / "fal_account_onboarding_plans_tier_c_2026-09-17.json"
out_path.write_text(
    json.dumps([{**asdict(p), "target": asdict(p.target)} for p in plans], indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(f"\nSaved plans to: {out_path}")
