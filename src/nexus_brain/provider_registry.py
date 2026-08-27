from __future__ import annotations

import json
from pathlib import Path

from .resource_router import ProviderRecord


def load_provider_registry(path: str | Path) -> tuple[ProviderRecord, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != "nexus-provider-registry-v0.1":
        raise ValueError("unsupported provider registry schema")
    providers = []
    seen: set[str] = set()
    for row in payload.get("providers", []):
        provider_id = row["id"]
        if provider_id in seen:
            raise ValueError(f"duplicate provider id: {provider_id}")
        seen.add(provider_id)
        providers.append(
            ProviderRecord(
                id=provider_id,
                status=row["status"],
                authority=row["authority"],
                capabilities=tuple(row["capabilities"]),
                openai_compatible=bool(row["openai_compatible"]),
                sensitive_data_allowed=bool(row["sensitive_data_allowed"]),
                production_role=row["production_role"],
                free_limit=row["free_limit"],
                data_training=row["data_training"],
                official_source=row.get("official_source"),
                notes=row.get("notes", ""),
            )
        )
    return tuple(providers)
