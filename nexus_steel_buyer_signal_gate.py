"""Buyer signal classification must fail closed on missing evidence."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BuyerSignal:
    project_id: str
    buyer_name: str
    source_url: str
    evidence_type: str
    deadline: str = ""


def classify_signal(signal: BuyerSignal, *, today: date) -> str:
    if not isinstance(signal, BuyerSignal) or not isinstance(today, date):
        raise ValueError("invalid_signal")
    if not all(isinstance(v, str) and v.strip() for v in (
        signal.project_id, signal.buyer_name, signal.source_url, signal.evidence_type
    )):
        raise ValueError("missing_evidence")
    if not signal.source_url.startswith(("https://", "http://")):
        raise ValueError("invalid_source_url")
    if signal.evidence_type not in {"BUY_TENDER", "SALE_TENDER", "RFQ", "AWARD", "UNKNOWN", "MARKET_PRICE_MONITORING"}:
        raise ValueError("invalid_evidence_type")
    if signal.evidence_type != "BUY_TENDER":
        return signal.evidence_type
    if not signal.deadline:
        return "BUY_TENDER_DEADLINE_UNKNOWN"
    try:
        deadline = date.fromisoformat(signal.deadline)
    except (ValueError, TypeError):
        raise ValueError("invalid_deadline") from None
    if deadline < today:
        return "BUY_TENDER_EXPIRED"
    return "BUY_TENDER_OPEN_STATUS_UNVERIFIED"
