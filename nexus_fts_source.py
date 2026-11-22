"""Bounded official UK source adapter on the existing sandbox queue; no scheduler."""
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import http.client
import json
import re
from time import monotonic

from nexus_commercial_pilot import CommercialRuntime, VERIFICATION_REQUIREMENTS
from nexus_public_research_agent import AcquisitionError
from nexus_router_runtime import PROJECT
from nexus_http_attempt_budget import AttemptBudget

SOURCE = 'https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages?limit=3&stages=tender'
MAX_BYTES = 262144


def fetch(url):
    if url != SOURCE:
        raise PermissionError('source_not_allowlisted')
    started = monotonic()
    try:
        with closing(http.client.HTTPSConnection('www.find-tender.service.gov.uk', timeout=5)) as conn:
            conn.request('GET', SOURCE.removeprefix('https://www.find-tender.service.gov.uk'),
                         headers={'Accept': 'application/json', 'Accept-Encoding': 'identity',
                                  'User-Agent': 'NEXUS-bounded-read-only-research'})
            response = conn.getresponse()
            if response.status != 200 or 'application/json' not in response.getheader('Content-Type', ''):
                raise AcquisitionError('source_unavailable')
            body = bytearray()
            while True:
                remaining = 8 - (monotonic() - started)
                if remaining <= 0:
                    raise AcquisitionError('timeout')
                if conn.sock is not None:
                    conn.sock.settimeout(min(5, remaining))
                chunk = response.read1(min(8192, MAX_BYTES + 1 - len(body)))
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise AcquisitionError('response_too_large')
                if not chunk:
                    return bytes(body)
    except Exception:
        raise AcquisitionError('bounded_source_read_failed') from None


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timezone_required')
    return parsed


def text(value):
    if value is None:
        return 'UNKNOWN'
    if type(value) is not str or not value or len(value) > 2000 or re.search(
        r'[<>\x00-\x1f\x7f]|[\w.+-]+@[\w.-]+|(?i:bearer\s|password|secret|api[_-]?key|token[=:])', value):
        raise ValueError('unsafe_source_text')
    return value


def assess(body, observed_at):
    if type(body) is not bytes or len(body) > MAX_BYTES:
        raise ValueError('invalid_response_bounds')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result
    data = json.loads(body, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('invalid_json_number')))
    rows = data['releases']
    if type(rows) is not list or len(rows) > 3:
        raise ValueError('invalid_result_limit')
    now = timestamp(observed_at)
    versions = {}
    for row in rows:
        identity, ocid = row['id'], row['ocid']
        if not re.fullmatch(r'[0-9]{6}-[0-9]{4}', identity) or not re.fullmatch(r'ocds-h6vhtk-[a-z0-9]+', ocid):
            raise ValueError('invalid_notice_identity')
        versions.setdefault((ocid, identity), []).append(row)
    items = []
    for (ocid, identity), copies in sorted(versions.items()):
        # Preserve disagreement; do not arbitrarily choose a qualified version.
        conflict = len({json.dumps(row, sort_keys=True) for row in copies}) > 1
        row = sorted(copies, key=lambda x: json.dumps(x, sort_keys=True))[0]
        tender = row.get('tender') or {}
        age = (now - timestamp(row['date'])).total_seconds()
        deadline = (tender.get('tenderPeriod') or {}).get('endDate')
        reasons = ['independent_verification_missing', 'authority_hold']
        if conflict:
            reasons.append('conflicting_source_records')
        if not 0 <= age <= 30 * 86400:
            reasons.append('stale_or_future_source')
        if not deadline or timestamp(deadline) <= now:
            reasons.append('deadline_missing_or_expired')
        if tender.get('status') != 'active' or 'tender' not in row.get('tag', []):
            reasons.append('not_active_tender')
        title, buyer = text(tender.get('title')), text((row.get('buyer') or {}).get('name'))
        relevance = bool(re.search(r'\b(steel|octg|hydrostatic|industrial|machinery)\b', title, re.I))
        if not relevance:
            reasons.append('keyword_relevance_not_supported')
        items.append({'notice_id': identity, 'ocid': ocid, 'title': title, 'buyer_claim': buyer,
            'source_url': 'https://www.find-tender.service.gov.uk/Notice/' + identity,
            'keyword_relevance': relevance, 'technical_specification_match': 'UNKNOWN',
            'independent_technical_compatibility': 'UNKNOWN',
            'verification_requirements': {key: 'UNKNOWN' for key in VERIFICATION_REQUIREMENTS},
            'decision': 'INVESTIGATE' if len(reasons) == 2 else 'REJECT', 'reasons': reasons,
            'evidence_class': 'CLAIM', 'authority': 'HOLD', 'actionable': False})
    return {'project_id': PROJECT, 'lane_id': 'official-uk-tender-sandbox',
        'records_received': len(rows), 'unique_records': len(items), 'duplicates_removed': len(rows)-len(items),
        'decisions': {key: sum(x['decision'] == key for x in items) for key in ('REJECT', 'INVESTIGATE', 'PROCEED')},
        'commercially_verified': 0, 'commercially_actionable': 0, 'insufficient_evidence': len(items),
        'assessments': items, 'authority': 'HOLD', 'canonical_project_assignment': 'BLOCKED',
        'result_scope': 'BOUNDED_SAMPLE_NOT_MARKET_ABSENCE'}


class FtsRuntime(CommercialRuntime):
    """Same bounded assessor, leases/checkpoints/Supervisor; distinct source action."""
    action = 'router.fts-read.v1'
    roles = ('official_uk_tender_read',)

    def __init__(self, path, *, transport=fetch, attempt_budget=None):
        self.attempt_budget = attempt_budget
        self.source_mode = 'REAL_PUBLIC_HTTP' if transport is fetch else 'FROZEN_TEST_FIXTURE'
        if transport is fetch and (not isinstance(attempt_budget, AttemptBudget)
            or attempt_budget.path != str(path) + '.http-attempts.sqlite'
            or attempt_budget.scope != 'nexus:fts:bounded-read' or attempt_budget.max_attempts != 1):
            raise ValueError('live_attempt_budget_required')
        super().__init__(path, transport=transport)
        with closing(self.store._connect()) as db:
            db.execute('BEGIN IMMEDIATE')
            binding = {'source_mode': self.source_mode,
                       'budget': attempt_budget.binding() if attempt_budget else None}
            old = db.execute("SELECT body FROM router_events WHERE project=? AND task=? AND kind='source_binding'",
                             (PROJECT, 'fts_source_binding')).fetchall()
            if old and (len(old) != 1 or json.loads(old[0][0]) != binding):
                raise ValueError('source_binding_requires_recovery')
            if not old:
                self._event(db, 'fts_source_binding', 'source_binding', binding, datetime.now(timezone.utc))
            db.commit()

    def execute(self, payload):
        if payload['project_id'] != PROJECT or payload['role'] != self.roles[0]:
            raise PermissionError('scope_mismatch')
        body = (self.attempt_budget.read(payload['task_id'], self.transport, SOURCE)
                if self.attempt_budget else self.transport(SOURCE))
        observed = datetime.now(timezone.utc).isoformat()
        values = assess(body, observed)
        digest = sha256(body).hexdigest()
        return {'project_id': PROJECT, 'task_id': payload['task_id'], 'worker': self.roles[0],
            'status': 'COMPLETE', 'evidence_class': 'CLAIM', 'observed_at': observed,
            'documents': [{'url': SOURCE, 'sha256': digest, 'body': body.decode('utf-8')}],
            'evidence': [SOURCE + '#sha256=' + digest], 'values': values,
            'model_tokens': 0, 'api_cost_usd': 0, 'http_reads': 1}

    def validate_result(self, payload, result):
        if (result.get('project_id'), result.get('task_id'), result.get('worker'), result.get('status'),
            result.get('evidence_class')) != (PROJECT, payload['task_id'], self.roles[0], 'COMPLETE', 'CLAIM'):
            raise ValueError('invalid_evidence_scope')
        docs = result['documents']
        if len(docs) != 1 or docs[0]['url'] != SOURCE:
            raise ValueError('invalid_source_provenance')
        body = docs[0]['body'].encode('utf-8')
        digest = sha256(body).hexdigest()
        if docs[0]['sha256'] != digest or result['evidence'] != [SOURCE + '#sha256=' + digest]:
            raise ValueError('digest_mismatch')
        age = (datetime.now(timezone.utc)-timestamp(result['observed_at'])).total_seconds()
        if not 0 <= age <= 300 or result['values'] != assess(body, result['observed_at']):
            raise ValueError('stale_or_inaccurate_evidence')
        if any(type(result.get(k)) is not int or result[k] != v
               for k,v in (('model_tokens',0),('api_cost_usd',0),('http_reads',1))):
            raise ValueError('invalid_metrics')
