"""Bounded read-only NEXUS maintenance inventory; never installs or authorizes.

Skill text is inert metadata. Installed files do not establish loaded/active
capabilities, connector health or approval. No raw skill content is exported.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

from conversation_control import allocate_tokens, TokenPolicy
from project_control_plane import WorkRequest, build_coordination_plan


def inventory_skills(roots, *, limit=200):
    if type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError('invalid_inventory_limit')
    rows, missing, seen, truncated = [], [], set(), False
    for root in roots:
        root=Path(root).resolve()
        if not root.is_dir():
            missing.append(str(root)); continue
        for path in root.rglob('SKILL.md'):
            resolved=path.resolve()
            if not resolved.is_relative_to(root) or resolved in seen:
                continue
            if len(rows)>=limit:
                truncated=True; break
            seen.add(resolved)
            if path.stat().st_size>131072:
                rows.append({'path':str(resolved),'status':'NOT_READ_SIZE_LIMIT'}); continue
            body=path.read_bytes()
            match=re.search(r'^name:\s*(.+)$',body.decode('utf-8-sig',errors='replace'),re.MULTILINE)
            rows.append({'path':str(resolved),'name':match.group(1).strip() if match else path.parent.name,
                         'sha256':hashlib.sha256(body).hexdigest(),'status':'FILE_PRESENT',
                         'loaded':'UNKNOWN','active':'UNKNOWN'})
    groups=defaultdict(list)
    for row in rows:
        if 'name' in row: groups[row['name']].append(row)
    collisions=[{'name':name,'copies':len(group),'content_drift':len({r['sha256'] for r in group})>1,
                 'paths':[r['path'] for r in group]} for name,group in sorted(groups.items()) if len(group)>1]
    return {'skills':rows,'collisions':collisions,'missing_roots':missing,'coverage_truncated':truncated,
            'automatic_changes':False}


def check_pending_manifest(repo):
    repo=Path(repo)
    path=repo/'data/research/v35-local-llm-manifest.json'
    approval=repo/'data/research/v35-approval-request.json'
    if not path.is_file() or not approval.is_file():
        return {'status':'UNKNOWN_MISSING_FILES','authorized':False}
    expected=json.loads(approval.read_text(encoding='utf-8-sig'))
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=expected.get('manifest_sha256'):
        return {'status':'BLOCK_MANIFEST_DRIFT','authorized':False}
    # Caller-declared metadata, including authorization_received=true, is never
    # interpreted as authenticated owner approval by this inventory tool.
    return {'status':'REVIEW_ONLY_EXACT_APPROVAL_REQUIRED','authorized':False,
            'manifest_sha256':digest,'approval_record_status':expected.get('status','UNKNOWN')}


def build_report(repo, roots):
    repo=Path(repo).resolve()
    request=WorkRequest('maintenance-preflight','PRJ-NEXUS-SANDBOX','Read-only skills/tool/approval inventory',
                        ('agent-runtime',),('agents',),lane='engineering',risk='read')
    plan=build_coordination_plan((request,),(),concurrency=1)
    allocation=allocate_tokens(TokenPolicy(12000,1500),estimated_history=1000,estimated_evidence=2500)
    return {'schema':'nexus.maintenance-preflight.v1','observed_at':datetime.now(timezone.utc).isoformat(),
            'project_id':'PRJ-NEXUS-SANDBOX','repository':str(repo),
            'skill_inventory':inventory_skills(roots),'tools':{name:{'path':shutil.which(name),'health':'NOT_PROBED'}
                for name in ('pwsh','powershell','git','rg')},'llm_manifest':check_pending_manifest(repo),
            'coordination':{'version':plan.version,'blocked':plan.blocked,
                            'assignments':[r.agent_id for r in plan.assignments],'executor':'READ_ONLY_LOCAL_INVENTORY'},
            'token_allocation':allocation.__dict__,'session_tokens':None,
            'changes_applied':False,'permissions_changed':False,'authority':'HOLD'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--skill-root',type=Path,action='append',required=True)
    args=parser.parse_args()
    print(json.dumps(build_report(args.repo,args.skill_root),ensure_ascii=False,indent=2))
