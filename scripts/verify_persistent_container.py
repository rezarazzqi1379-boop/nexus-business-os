"""Disposable Docker acceptance; never attaches an existing production volume.

Only fixed, non-sensitive checks leave the container. Queue fixtures are frozen,
not live research; the existing free-runtime workflow supplies live evidence.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid


ROOT = Path(__file__).resolve().parents[1]


def require(condition):
    if not condition:
        raise RuntimeError("acceptance_check_failed")


SEED = '''
import os,json
from pathlib import Path
from state import EventStore,EventRecord
from nexus_public_research_agent import PublicResearchRuntime,REPO,URLS
def require(value):
    if not value: raise RuntimeError('fixture_failed')
server_uids=[]
for path in Path('/proc').glob('[0-9]*/cmdline'):
    try:
        args=path.read_bytes().rstrip(b'\\0').split(b'\\0')
        if args[-1:]==[b'start.py']:
            line=next(x for x in path.with_name('status').read_text().splitlines() if x.startswith('Uid:'))
            server_uids.append(int(line.split()[2]))
    except (OSError,StopIteration): pass
require(server_uids and set(server_uids)=={10001})
store=EventStore(Path('/data/state.db'))
require(store.begin(EventRecord('persistence-proof','PRJ-NEXUS-SANDBOX','fixture',{'synthetic':True}))=='new')
bodies=[json.dumps({'full_name':REPO,'archived':False,'pushed_at':'2026-01-01T00:00:00Z','license':{'spdx_id':'MIT'}}).encode(),json.dumps({'html_url':f'https://github.com/{REPO}/releases/tag/v1','tag_name':'v1','published_at':'2026-01-01T00:00:00Z'}).encode()]
runtime=PublicResearchRuntime(Path('/data/router.db'),transport=lambda url:bodies[URLS.index(url)])
require(runtime.submit('persistence-proof',budget_units=3))
require(runtime.drain()==1 and runtime.review('persistence-proof')=='accepted')
Path('/data/nexus_vault/persistence-proof.txt').write_text('frozen-fixture')
print('SEED_OK_NON_ROOT_AND_ATOMIC_CHECKPOINT')
'''

RECOVER = '''
from pathlib import Path
from state import EventStore
from nexus_public_research_agent import PublicResearchRuntime
from unified_data_environment import UnifiedDataHub,DataAsset,BackupManager
from ops import backup,verify_backup,restore_backup
def require(value):
    if not value: raise RuntimeError('fixture_failed')
def no_network(url): raise RuntimeError('replay_must_not_read')
def check(root):
    require(EventStore(root/'state.db').get_status('persistence-proof')=='processing')
    require((root/'nexus_vault/persistence-proof.txt').read_text()=='frozen-fixture')
    runtime=PublicResearchRuntime(root/'router.db',transport=no_network)
    require(not runtime.submit('persistence-proof',budget_units=3))
    require(runtime.drain()==0 and runtime.review('persistence-proof')=='accepted')
check(Path('/data'))
hub=UnifiedDataHub(Path('/data/nexus_system/nexus.db'),Path('/data'))
for name in ('state.db','canonical.db','router.db'):
    hub.register_asset(DataAsset(name,'PRJ-NEXUS-SANDBOX','sqlite',name,'frozen-fixture'))
hub.register_asset(DataAsset('vault','PRJ-NEXUS-SANDBOX','directory','nexus_vault','frozen-fixture'))
manager=BackupManager(hub,Path('/tmp/hub-backups'))
require(manager.verify_snapshot(manager.create_snapshot('container-proof')))
copy=Path(backup(Path('/data'),Path('/tmp/ops-backups'))['backup'])
require(verify_backup(copy)['valid'])
restore_backup(copy,Path('/tmp/restore-proof'))
check(Path('/tmp/restore-proof'))
try: restore_backup(copy,Path('/tmp/restore-proof'))
except ValueError: pass
else: raise RuntimeError('restore_overwrite_not_blocked')
print('RECOVERY_OK_REPLAY_ZERO_READS_BACKUP_VERIFIED_RESTORE_VERIFIED')
'''


def run(image: str) -> dict:
    summary = {"status": "BLOCKED", "scope": "DISPOSABLE_CONTAINER_ACCEPTANCE",
               "queue_source_mode": "FROZEN_TEST_FIXTURE", "production_deployed": False,
               "authority_promoted": False, "external_writes": 0}
    if shutil.which("docker") is None:
        return {**summary, "reason": "DOCKER_UNAVAILABLE"}
    project = "nexus-proof-" + uuid.uuid4().hex[:16]
    env = dict(os.environ)
    env.update(NEXUS_IMAGE=image, NEXUS_ACCESS_TOKEN=secrets.token_urlsafe(48))
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        env["NEXUS_HTTP_PORT"] = str(sock.getsockname()[1])
    base = "http://127.0.0.1:" + env["NEXUS_HTTP_PORT"]
    stage = "COMPOSE_CONFIG"
    started = False
    with tempfile.NamedTemporaryFile() as empty_env:
        command = ["docker", "compose", "--env-file", empty_env.name, "-f",
                   str(ROOT / "deploy/compose.persistent.yml"), "-p", project]

        def compose(*args, timeout=90, check=True, environment=None):
            result = subprocess.run([*command, *args], env=env if environment is None else environment,
                cwd=ROOT, capture_output=True, text=True, timeout=timeout)
            if check:
                if result.returncode != 0:
                    # Export only fixed categories, never raw stderr/config/env.
                    markers = ("permission denied", "read-only file system", "invalid mount",
                               "port is already allocated", "no such image", "no such file",
                               "invalid argument", "unknown flag", "operation not permitted",
                               "mount", "cpus", "memory", "daemon", "address already in use",
                               "operationalerror", "modulenotfounderror", "runtimeerror")
                    summary["command_failure"] = {
                        "operation": args[0], "exit_code": result.returncode,
                        "categories": [m for m in markers if m in result.stderr.lower()]}
                    raise RuntimeError("container_command_failed")
            return result

        def probe():
            for _ in range(60):
                try:
                    with urllib.request.urlopen(base + "/ready", timeout=2) as response:
                        require(response.status == 200)
                        return
                except (urllib.error.URLError, RuntimeError):
                    time.sleep(.5)
            raise RuntimeError("readiness_failed")

        try:
            no_token = {k: v for k, v in env.items() if k != "NEXUS_ACCESS_TOKEN"}
            require(compose("config", "--quiet", check=False, environment=no_token).returncode != 0)
            compose("config", "--quiet")  # Never print resolved secret values.
            stage = "CREATE_CONTAINER"
            started = True
            compose("up", "-d", "--no-build")
            stage = "READINESS"
            probe()
            stage = "PUBLIC_HEALTH"
            with urllib.request.urlopen(base + "/health", timeout=3) as response:
                require(response.status == 200)
            stage = "UNAUTHENTICATED_DIAGNOSTICS"
            try:
                urllib.request.urlopen(base + "/v1/system/diagnostics", timeout=3)
            except urllib.error.HTTPError as error:
                require(error.code == 401)
            else:
                raise RuntimeError("authentication_missing")
            request = urllib.request.Request(base + "/v1/system/diagnostics",
                headers={"Authorization": "Bearer " + env["NEXUS_ACCESS_TOKEN"]})
            stage = "AUTHENTICATED_DIAGNOSTICS"
            with urllib.request.urlopen(request, timeout=3) as response:
                require(response.status == 200 and all(json.load(response)["checks"].values()))
            stage = "SEED_CHECKPOINT"
            result = compose("exec", "-T", "--user", "10001:65534", "nexus", "python", "-c", SEED)
            require("SEED_OK" in result.stdout)
            stage = "RESTART"
            compose("restart", "nexus")
            probe()
            stage = "RECOVER_BACKUP_RESTORE"
            result = compose("exec", "-T", "--user", "10001:65534", "nexus", "python", "-c", RECOVER)
            require("RECOVERY_OK" in result.stdout)
            summary.update(status="VERIFIED", auth=True, readiness=True, server_non_root=True,
                volume_restart_persistence=True, queue_replay_zero_reads=True,
                checkpoint_and_supervisor=True, backup_manifest_verified=True,
                restore_into_empty_target=True, restore_overwrite_blocked=True)
        except Exception:
            summary.update(status="BLOCKED", reason=stage + "_FAILED")
        finally:
            if started:
                try:
                    compose("down", "--volumes", "--remove-orphans", timeout=60)
                    summary["disposable_resources_cleaned"] = True
                except Exception:
                    summary.update(status="BLOCKED", reason="DISPOSABLE_CLEANUP_FAILED")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    summary = run(args.image)
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0 if summary["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
