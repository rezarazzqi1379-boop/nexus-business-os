import importlib

from fastapi.testclient import TestClient

from nexus_router_runtime import SyntheticRuntime


def test_console_authentication_and_read_only_state(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_STATE_DB", str(tmp_path / "state.db"))
    monkeypatch.setenv("NEXUS_CANONICAL_DB", str(tmp_path / "canonical.db"))
    monkeypatch.setenv("NEXUS_VAULT_ROOT", str(tmp_path / "vault"))
    monkeypatch.setenv("NEXUS_ACCESS_TOKEN", "synthetic-local-test-credential-" + "x" * 32)
    monkeypatch.setenv("NEXUS_AUTH_REQUIRED", "1")
    runtime = SyntheticRuntime(tmp_path / "queue.db")
    runtime.submit("consoleproof")
    runtime.drain()
    monkeypatch.setenv("NEXUS_ROUTER_SANDBOX_DB", str(runtime.store.path))
    import api
    importlib.reload(api)
    client = TestClient(api.app)
    try:
        assert client.get("/v1/console/router").status_code == 401
        assert client.get("/console/router", follow_redirects=False).status_code == 401
        headers = {"Authorization": "Bearer " + "synthetic-local-test-credential-" + "x" * 32}
        before = runtime.snapshot()
        response = client.get("/v1/console/router", headers=headers)
        assert response.status_code == 200
        assert len(response.json()["tasks"]) == 3
        page = client.get("/console/router", headers=headers)
        assert page.status_code == 200
        assert '/assets/router-status.js' in page.text
        assert "script-src 'self'" in page.headers["Content-Security-Policy"]
        assert client.post("/v1/console/router", headers=headers).status_code == 405
        assert before == runtime.snapshot()
    finally:
        client.close()
