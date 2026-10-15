from copy import deepcopy
from datetime import datetime, timezone, timedelta
import json

import pytest

from nexus_public_research_agent import PublicResearchRuntime, REPO, URLS, extract, public_get
from nexus_router_runtime import SyntheticRuntime


def fixture():
    return [json.dumps({"full_name": REPO, "archived": False, "pushed_at": "2026-10-01T00:00:00Z",
                        "license": {"spdx_id": "MIT"}}).encode(),
            json.dumps({"html_url": f"https://github.com/{REPO}/releases/tag/v1", "tag_name": "v1",
                        "published_at": "2026-10-01T00:00:00Z"}).encode()]


def test_real_contract_frozen_checkpoint_and_replay(tmp_path):
    calls = []
    def transport(url):
        calls.append(url)
        return fixture()[URLS.index(url)]
    runtime = PublicResearchRuntime(tmp_path / "queue.db", transport=transport)
    runtime.submit("real")
    assert runtime.drain() == 1
    assert calls == list(URLS)
    assert runtime.review("real") == "accepted"
    assert runtime.drain() == 0
    assert len(calls) == 2
    assert len(runtime.snapshot()["tasks"]) == 1
    assert SyntheticRuntime(tmp_path / "queue.db").drain() == 0


@pytest.mark.parametrize("mutation", ["project", "hash", "url", "value", "evidence", "stale"])
def test_evidence_fail_closed(tmp_path, mutation):
    runtime = PublicResearchRuntime(tmp_path / "queue.db", transport=lambda url: fixture()[URLS.index(url)])
    runtime.submit("real")
    item = runtime.claim("owner")
    output = runtime.execute(item.payload)
    if mutation == "project": output["project_id"] = "OTHER"
    if mutation == "hash": output["documents"][0]["sha256"] = "0"*64
    if mutation == "url": output["documents"][0]["url"] = "http://127.0.0.1"
    if mutation == "value": output["values"]["release_tag"] = "invented"
    if mutation == "evidence": output["evidence"] = []
    if mutation == "stale": output["observed_at"] = (datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
    with pytest.raises(ValueError): runtime.finish(item, "owner", output)
    assert runtime.review("real") == "rejected"


@pytest.mark.parametrize("url", ["http://localhost", "https://api.github.com.evil.invalid", URLS[0]+"?token=secret"])
def test_no_arbitrary_network(url):
    with pytest.raises(PermissionError): public_get(url)


def test_bounds_entity_and_future_rejection():
    now = datetime.now(timezone.utc).isoformat()
    with pytest.raises(ValueError): extract([b'x'*65537, b'{}'], now)
    wrong = fixture()
    repo = json.loads(wrong[0]); repo['full_name'] = 'imposter/other'
    wrong[0] = json.dumps(repo).encode()
    with pytest.raises(ValueError): extract(wrong, now)
    with pytest.raises(ValueError): extract(fixture(), '2020-01-01T00:00:00+00:00')


def test_crash_before_checkpoint_reclaims(tmp_path):
    runtime = PublicResearchRuntime(tmp_path/'queue.db', transport=lambda url: fixture()[URLS.index(url)])
    runtime.submit('real')
    now = datetime.now(timezone.utc)+timedelta(seconds=1)
    first = runtime.claim('first', now=now, lease_seconds=1)
    replacement = runtime.claim('second', now=now+timedelta(seconds=2))
    assert replacement.attempt == 2
    with pytest.raises(PermissionError): runtime.finish(first,'first',runtime.execute(first.payload),now=now+timedelta(seconds=2))
    runtime.finish(replacement,'second',runtime.execute(replacement.payload),now=now+timedelta(seconds=2))
    assert runtime.review('real') == 'accepted'


@pytest.mark.parametrize('status', [301,403,429,500])
def test_redirect_auth_rate_and_server_errors_are_denied(monkeypatch,status):
    import nexus_public_research_agent as module
    class Response:
        def __init__(self): self.status = status
        def getheader(self,*args): return 'application/json'
    class Connection:
        def __init__(self,*args,**kwargs): pass
        def request(self,method,path,headers):
            assert method == 'GET' and 'Authorization' not in headers
        def getresponse(self): return Response()
        def close(self): pass
    monkeypatch.setattr(module.http.client,'HTTPSConnection',Connection)
    with pytest.raises(module.AcquisitionError,match='source_unavailable'):
        public_get(URLS[0])


def test_provider_exception_is_redacted(tmp_path):
    from nexus_public_research_agent import AcquisitionError
    def transport(url): raise RuntimeError('DO_NOT_RELAY_PRIVATE_RESPONSE')
    runtime=PublicResearchRuntime(tmp_path/'queue.db',transport=transport)
    runtime.submit('real')
    item=runtime.claim('owner')
    with pytest.raises(AcquisitionError) as error: runtime.execute(item.payload)
    assert 'DO_NOT_RELAY' not in str(error.value)
    assert runtime.review('real') == 'rejected'
