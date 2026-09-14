"""Manual market-price evidence recording for the FAL-A/FAL-B ferroalloys vertical.

This does NOT fetch prices automatically -- Fastmarkets, Mysteel, Asian Metal, and CRU
Group (the industry's known ferroalloys price sources) require paid subscriptions or
have no public API this environment can reach. Rather than scrape or guess a price,
this module gives you a disciplined, evidence-graded place to record a price YOU
observed (from a subscription, a broker quote, a public news snippet) so
fal_trade_economics.py and need_radar.py's evidence discipline can use it honestly.

Every snapshot becomes a NeedEvidence-shaped record: classification is FACT only when
the source_type is a named, checkable source (matching need_radar.py's own rule);
otherwise it's a CLAIM or ESTIMATE. Nothing here is invented -- if you don't have a
real number, don't call this with one.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from need_radar import EVIDENCE_CLASSES, SOURCE_TYPES

KNOWN_PRICE_SOURCES = (
    "fastmarkets", "mysteel", "asian_metal", "cru_group", "broker_quote", "other",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class PriceSnapshot:
    snapshot_id: str
    product: str  # e.g. "ferromanganese", "ferrosilicon" -- validated against fal_vertical products elsewhere
    price_per_ton: float
    currency: str
    price_source: str
    classification: str
    source_ref: str
    observed_at: str
    recorded_at: str
    notes: str = ""

    def validate(self) -> None:
        if not self.snapshot_id.strip():
            raise ValueError("invalid_snapshot_id")
        if not self.product.strip():
            raise ValueError("invalid_product")
        if isinstance(self.price_per_ton, bool) or not isinstance(self.price_per_ton, (int, float)) or self.price_per_ton <= 0:
            raise ValueError("invalid_price_per_ton")
        if not self.currency.strip() or len(self.currency) > 6:
            raise ValueError("invalid_currency")
        if self.price_source not in KNOWN_PRICE_SOURCES:
            raise ValueError("invalid_price_source")
        if self.classification not in EVIDENCE_CLASSES:
            raise ValueError("invalid_classification")
        if not self.source_ref.strip():
            raise ValueError("invalid_source_ref")
        if self.classification == "FACT" and self.price_source == "other":
            raise ValueError("fact_requires_a_named_checkable_source")


class PriceSnapshotStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db:
            with db:
                db.execute("""
                CREATE TABLE IF NOT EXISTS price_snapshots (
                    snapshot_id TEXT PRIMARY KEY, product TEXT NOT NULL, price_per_ton REAL NOT NULL,
                    currency TEXT NOT NULL, price_source TEXT NOT NULL, classification TEXT NOT NULL,
                    source_ref TEXT NOT NULL, observed_at TEXT NOT NULL, recorded_at TEXT NOT NULL,
                    notes TEXT
                )
            """)

    def record(self, snapshot: PriceSnapshot) -> None:
        snapshot.validate()
        with closing(sqlite3.connect(self.path)) as db:
            with db:
                db.execute(
                    "INSERT INTO price_snapshots VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (snapshot.snapshot_id, snapshot.product, snapshot.price_per_ton, snapshot.currency,
                     snapshot.price_source, snapshot.classification, snapshot.source_ref,
                     snapshot.observed_at, snapshot.recorded_at, snapshot.notes),
                )

    def latest_for_product(self, product: str, *, source_type_filter: str | None = None) -> dict | None:
        with closing(sqlite3.connect(self.path)) as db:
            db.row_factory = sqlite3.Row
            if source_type_filter:
                row = db.execute(
                    "SELECT * FROM price_snapshots WHERE product=? AND price_source=? "
                    "ORDER BY observed_at DESC LIMIT 1",
                    (product, source_type_filter),
                ).fetchone()
            else:
                row = db.execute(
                    "SELECT * FROM price_snapshots WHERE product=? ORDER BY observed_at DESC LIMIT 1",
                    (product,),
                ).fetchone()
            return dict(row) if row else None

    def history_for_product(self, product: str) -> list[dict]:
        with closing(sqlite3.connect(self.path)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT * FROM price_snapshots WHERE product=? ORDER BY observed_at", (product,)
            ).fetchall()
            return [dict(r) for r in rows]
