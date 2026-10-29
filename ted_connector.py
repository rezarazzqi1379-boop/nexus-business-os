"""Fixed, read-only TED public Search API request. No credentials or publication."""
from contextlib import closing
import http.client
import json
import re
from time import monotonic

ENDPOINT = "https://api.ted.europa.eu/v3/notices/search"
QUERY = "FT~steel"
REQUEST = {"query": QUERY, "fields": ["publication-number"], "page": 1,
           "limit": 3, "scope": "ALL", "checkQuerySyntax": False, "paginationMode": "PAGE_NUMBER"}
MAX_BYTES = 65536


def public_search(url):
    if url != ENDPOINT:
        raise PermissionError("ted_endpoint_not_allowlisted")
    started = monotonic()
    try:
        with closing(http.client.HTTPSConnection("api.ted.europa.eu", timeout=5)) as connection:
            connection.request("POST", "/v3/notices/search", body=json.dumps(REQUEST).encode(), headers={
                "Content-Type": "application/json", "Accept": "application/json",
                "Accept-Encoding": "identity", "User-Agent": "NEXUS-bounded-read-only-trial"})
            response = connection.getresponse()
            if response.status != 200 or "application/json" not in response.getheader("Content-Type", ""):
                raise ValueError("ted_unavailable")
            body = bytearray()
            while True:
                remaining = 8 - (monotonic() - started)
                if remaining <= 0:
                    raise ValueError("ted_timeout")
                if connection.sock is not None:
                    connection.sock.settimeout(min(5, remaining))
                chunk = response.read1(min(8192, MAX_BYTES + 1 - len(body)))
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise ValueError("ted_response_too_large")
                if not chunk:
                    return bytes(body)
    except Exception:
        raise RuntimeError("bounded_ted_read_failed") from None


def parse_notices(body):
    if type(body) is not bytes or len(body) > MAX_BYTES:
        raise ValueError("ted_response_bounds")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_ted_key")
            result[key] = value
        return result
    data = json.loads(body, object_pairs_hook=unique)
    if not isinstance(data, dict) or not isinstance(data.get("notices"), list) or len(data["notices"]) > 3:
        raise ValueError("ted_notice_schema")
    results = []
    for row in data["notices"]:
        if not isinstance(row, dict):
            raise ValueError("ted_notice_schema")
        identity = row.get("publication-number")
        if not isinstance(identity, str) or not re.fullmatch(r"[0-9]{1,8}-20[0-9]{2}", identity):
            raise ValueError("ted_notice_identity")
        # Only requested public notice identity is retained; no source-supplied links.
        results.append({"identity": identity, "url": f"https://ted.europa.eu/en/notice/{identity}/html"})
    return tuple(results)
