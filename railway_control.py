"""Governed Railway Public API client for NEXUS Business OS.

The client deliberately starts read-only. Railway mutations are not exposed until
live schema discovery and an exact production approval bind the action, target,
payload and rollback plan.

Authentication is read from the environment only; tokens are never accepted on
the command line or written to disk.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

RAILWAY_GRAPHQL_ENDPOINT = "https://backboard.railway.com/graphql/v2"


class RailwayControlError(RuntimeError):
    """Raised when a Railway API request cannot be safely completed."""


@dataclass(frozen=True)
class RailwayAuth:
    token: str
    token_type: str = "project"

    @classmethod
    def from_environment(cls) -> "RailwayAuth":
        project_token = os.getenv("RAILWAY_PROJECT_TOKEN")
        bearer_token = os.getenv("RAILWAY_TOKEN")
        if project_token and bearer_token:
            raise RailwayControlError(
                "Ambiguous Railway authentication: set only one of "
                "RAILWAY_PROJECT_TOKEN or RAILWAY_TOKEN."
            )
        if project_token:
            return cls(project_token, "project")
        if bearer_token:
            return cls(bearer_token, "bearer")
        raise RailwayControlError(
            "Missing Railway authentication. Set RAILWAY_PROJECT_TOKEN "
            "(preferred for NEXUS production) or RAILWAY_TOKEN."
        )

    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token_type == "project":
            headers["Project-Access-Token"] = self.token
        elif self.token_type == "bearer":
            headers["Authorization"] = f"Bearer {self.token}"
        else:
            raise RailwayControlError(f"Unsupported token type: {self.token_type}")
        return headers


class RailwayClient:
    def __init__(
        self,
        auth: RailwayAuth,
        endpoint: str = RAILWAY_GRAPHQL_ENDPOINT,
        timeout: float = 20.0,
    ) -> None:
        self.auth = auth
        self.endpoint = endpoint
        self.timeout = timeout

    def execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers=self.auth.headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RailwayControlError(f"Railway HTTP {exc.code}: {body[:500]}") from exc
        except urllib.error.URLError as exc:
            raise RailwayControlError(f"Railway network error: {exc.reason}") from exc

        try:
            decoded = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RailwayControlError("Railway returned non-JSON content") from exc

        # GraphQL authorization and validation failures may arrive with HTTP 200.
        if decoded.get("errors"):
            sanitized = []
            for error in decoded["errors"]:
                sanitized.append(
                    {
                        "message": error.get("message"),
                        "code": (error.get("extensions") or {}).get("code"),
                        "traceId": (error.get("extensions") or {}).get("traceId"),
                    }
                )
            raise RailwayControlError(f"Railway GraphQL errors: {json.dumps(sanitized)}")
        return decoded.get("data") or {}

    def project_token_scope(self) -> dict[str, Any]:
        if self.auth.token_type != "project":
            raise RailwayControlError("project_token_scope requires RAILWAY_PROJECT_TOKEN")
        return self.execute("query { projectToken { projectId environmentId } }")

    def query_type_fields(self, type_name: str) -> dict[str, Any]:
        """Read live GraphQL schema fields before implementing a mutation."""
        return self.execute(
            """
            query SchemaType($name: String!) {
              __type(name: $name) {
                name
                fields(includeDeprecated: true) {
                  name
                  isDeprecated
                  deprecationReason
                }
              }
            }
            """,
            {"name": type_name},
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NEXUS governed Railway API client")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scope", help="Verify project-token scope without mutating Railway")
    schema = sub.add_parser("schema", help="Inspect one live GraphQL type read-only")
    schema.add_argument("type_name")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = RailwayClient(RailwayAuth.from_environment())
        if args.command == "scope":
            result = client.project_token_scope()
        elif args.command == "schema":
            result = client.query_type_fields(args.type_name)
        else:
            raise RailwayControlError(f"Unsupported command: {args.command}")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except RailwayControlError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
