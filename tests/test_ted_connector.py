from datetime import datetime, timedelta, timezone
import json
import pytest
from autonomy import AutonomyStore
from nexus_router_runtime import PROJECT
from run_source_trial import run_tick
from ted_connector import parse_notices, public_search, REQUEST


def test_three_tick_frozen_replay_and_dedup(tmp_path):
    start = datetime.now(timezone.utc)
    store = AutonomyStore(tmp_path / "trial.db")
    store.configure_http_trial("trial",PROJECT,sources=("worldbank","ted"),starts_at=start)
    wb = json.dumps(dict(rows="1",os="0",page="1",total="1",procnotices=[{"id":"OP00476469"}])).encode()
    ted = json.dumps({"notices":[{"publication-number":"1234-2026"}]}).encode()
    transports = {"worldbank":lambda _:wb,"ted":lambda _:ted}
    for tick in range(3):
        result = run_tick(store,"trial",tick,transports=transports,now=start+timedelta(seconds=300*tick))
    assert result["reserved_attempts"] == 6 and len(result["evidence"]) == 6
    assert not result["multi_source_live_proven"]
    assert not result["independent_shared_claim_verified"]
    assert {e["independence_group"] for e in result["evidence"]} == {"worldbank-publication","eu-publications-office"}
    again = run_tick(store,"trial",2,transports=transports,now=start+timedelta(seconds=600))
    assert again["reserved_attempts"] == 6
    with pytest.raises(ValueError,match="mode"):
        run_tick(store,"trial",0,now=start)


@pytest.mark.parametrize("body", [b'{}',b'{"notices":[{"publication-number":"https://evil"}]}',
    b'{"notices":[],"notices":[]}',b'x'*65537,
    json.dumps({"notices":[{"publication-number":"1234-2026"}]*4}).encode()],
    ids=["missing","identity","duplicate-key","bytes","rows"])
def test_ted_bounds_and_malformed(body):
    with pytest.raises(ValueError):
        parse_notices(body)


def test_source_links_are_not_followed_or_retained():
    assert REQUEST["checkQuerySyntax"] is False
    assert REQUEST["limit"] == 3 and REQUEST["fields"] == ["publication-number"]
    result = parse_notices(b'{"notices":[{"publication-number":"1234-2026","links":{"xml":"https://evil.invalid"}}]}')
    assert result[0]["url"] == "https://ted.europa.eu/en/notice/1234-2026/html"
    with pytest.raises(PermissionError):
        public_search("https://evil.invalid")


@pytest.mark.parametrize("status,size", [(302,0),(200,65537)])
def test_transport_rejects_redirect_or_oversize_without_retry(monkeypatch,status,size):
    import ted_connector
    calls = []
    class Response:
        def __init__(self):
            self.status = status
            self.remaining = size
        def getheader(self,name,default):
            return "application/json"
        def read1(self,n):
            length = min(n,self.remaining)
            self.remaining -= length
            return b'x'*length
    class Connection:
        sock = None
        def __init__(self,host,timeout):
            assert host == "api.ted.europa.eu" and timeout == 5
        def request(self,method,path,body,headers):
            calls.append((method,path,json.loads(body)))
        def getresponse(self):
            return Response()
        def close(self):
            pass
    monkeypatch.setattr(ted_connector.http.client,"HTTPSConnection",Connection)
    with pytest.raises(RuntimeError,match="^bounded_ted_read_failed$"):
        public_search(ted_connector.ENDPOINT)
    assert len(calls) == 1
    assert calls[0] == ("POST","/v3/notices/search",REQUEST)
