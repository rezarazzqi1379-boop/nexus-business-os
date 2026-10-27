import http.client

import pytest

from scripts import verify_persistent_container as verifier


class Response:
    def __init__(self, status=200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.mark.parametrize('error', [http.client.RemoteDisconnected('fixture reset'),
                                  ConnectionResetError('fixture reset')])
def test_startup_connection_reset_is_retried_without_accepting_failure(monkeypatch, error):
    calls = []
    def urlopen(url, timeout):
        calls.append(url)
        if len(calls) == 1:
            raise error
        return Response()
    monkeypatch.setattr(verifier.urllib.request, 'urlopen', urlopen)
    monkeypatch.setattr(verifier.time, 'sleep', lambda _: None)
    verifier.wait_for_ready('http://127.0.0.1:8421', attempts=2)
    assert len(calls) == 2


def test_unready_service_exhausts_bound_instead_of_passing(monkeypatch):
    calls = []
    def urlopen(url, timeout):
        calls.append(url)
        return Response(503)
    monkeypatch.setattr(verifier.urllib.request, 'urlopen', urlopen)
    monkeypatch.setattr(verifier.time, 'sleep', lambda _: None)
    with pytest.raises(RuntimeError, match='readiness_failed'):
        verifier.wait_for_ready('http://127.0.0.1:8421', attempts=3)
    assert len(calls) == 3
