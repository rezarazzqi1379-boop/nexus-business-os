import os,sys,tempfile,sqlite3
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
from plo_core import PLOStore,ApprovalError,OwnershipError,MAX_ORPHAN_RETRIES
from gmail_readonly import GmailReadOnly,ReadOnlyViolation,deterministic_message_id,State
from reconciliation import decide,Decision

def fresh():
    td=tempfile.TemporaryDirectory(); return td,PLOStore(os.path.join(td.name,'p.db'))

def test_approval_before_side_effect():
    td,s=fresh(); r=s.enqueue('send','k1',True); c=s.claim_next('w')
    try: s.authorize_operation(r,'op','send:a',c['_lease_token'],'w'); raise AssertionError()
    except ApprovalError: pass
    a=s.request_approval(r,'send:a'); s.decide_approval(a,'approved'); tok=s.authorize_operation(r,'op','send:a',c['_lease_token'],'w'); s.record_intent(r,'op',tok,c['_lease_token'],'w'); assert s.operation_state('op')=='intended'; td.cleanup()
def test_stale_version():
    td,s=fresh(); r=s.enqueue('x','k2',True); a=s.request_approval(r,'send:a'); c=s.claim_next('w'); s.decide_approval(a,'approved')
    try: s.authorize_operation(r,'op','send:a',c['_lease_token'],'w'); raise AssertionError()
    except ApprovalError: pass
    td.cleanup()
def test_expired_lease_cannot_renew():
    td,s=fresh(); r=s.enqueue('x','k3'); c=s.claim_next('w',-1)
    try: s.renew_lease(r,c['_lease_token'],'w'); raise AssertionError()
    except OwnershipError: pass
    td.cleanup()
def test_expired_lease_cannot_authorize():
    td,s=fresh(); r=s.enqueue('send','k6',True); c=s.claim_next('w',-1); a=s.request_approval(r,'send:a'); s.decide_approval(a,'approved')
    try: s.authorize_operation(r,'op-exp','send:a',c['_lease_token'],'w'); raise AssertionError('expired lease authorized')
    except OwnershipError: pass
    td.cleanup()
def test_expired_lease_cannot_record_intent():
    td,s=fresh(); r=s.enqueue('send','k7',True); c=s.claim_next('w',1); a=s.request_approval(r,'send:a'); s.decide_approval(a,'approved'); tok=s.authorize_operation(r,'op-gap','send:a',c['_lease_token'],'w')
    s.renew_lease(r,c['_lease_token'],'w',-1)
    try: s.record_intent(r,'op-gap',tok,c['_lease_token'],'w'); raise AssertionError('expired lease recorded intent')
    except OwnershipError: pass
    td.cleanup()
def test_mark_executed_requires_intent():
    td,s=fresh(); r=s.enqueue('send','k8',True); c=s.claim_next('w'); a=s.request_approval(r,'send:a'); s.decide_approval(a,'approved'); s.authorize_operation(r,'op-order','send:a',c['_lease_token'],'w')
    try: s.mark_executed('op-order'); raise AssertionError('executed without intent')
    except ApprovalError: pass
    td.cleanup()
def test_read_only_completion():
    td,s=fresh(); r=s.enqueue('research','ro-1'); c=s.claim_next('w'); assert s.complete_read_only(r,c['_lease_token'],'w','RESULT:brain-hydro') is True; m=s.metrics(); assert m['completed']==1 and m['pending']==0; td.cleanup()
def test_read_only_completion_rejects_consequential_task():
    td,s=fresh(); r=s.enqueue('send','ro-2',True); c=s.claim_next('w')
    try: s.complete_read_only(r,c['_lease_token'],'w','RESULT:nope'); raise AssertionError('consequential task completed through read-only path')
    except ApprovalError: pass
    td.cleanup()
def test_read_only_completion_rejects_expired_lease():
    td,s=fresh(); r=s.enqueue('research','ro-3'); c=s.claim_next('w',-1)
    try: s.complete_read_only(r,c['_lease_token'],'w','RESULT:nope'); raise AssertionError('expired lease completed read-only task')
    except OwnershipError: pass
    td.cleanup()
def test_recovery():
    td,s=fresh(); r=s.enqueue('x','k4'); s.claim_next('w',-1); assert r in s.recover_orphans(); assert s.metrics()['pending']==1; td.cleanup()
def test_orphan_retry_budget_exhaustion_holds_task():
    td,s=fresh(); r=s.enqueue('x','retry-budget')
    for i in range(MAX_ORPHAN_RETRIES):
        c=s.claim_next(f'w{i}',-1); assert c and c['run_id']==r
        assert r in s.recover_orphans()
    m=s.metrics(); assert m['pending']==0 and m['reconciliation_required']==1
    assert s.claim_next('after-budget') is None
    db=sqlite3.connect(s.path); row=db.execute("SELECT status,retry_count FROM tasks WHERE run_id=?",(r,)).fetchone(); audit=db.execute("SELECT result FROM audit WHERE run_id=? AND action='orphan_recovered' ORDER BY id DESC LIMIT 1",(r,)).fetchone(); db.close()
    assert row==('WAITING',MAX_ORPHAN_RETRIES); assert audit==('retry_budget_exhausted',); td.cleanup()
def test_orphan_with_intent_requires_reconciliation():
    td,s=fresh(); r=s.enqueue('send','k9',True); c=s.claim_next('w',30); a=s.request_approval(r,'send:a'); s.decide_approval(a,'approved'); tok=s.authorize_operation(r,'op-uncertain','send:a',c['_lease_token'],'w'); s.record_intent(r,'op-uncertain',tok,c['_lease_token'],'w'); s.renew_lease(r,c['_lease_token'],'w',-1)
    assert r in s.recover_orphans(); m=s.metrics(); assert m['reconciliation_required']==1 and m['pending']==0; assert s.claim_next('other') is None; td.cleanup()
def test_mark_executed_is_idempotent():
    td,s=fresh(); r=s.enqueue('send','k5',True); c=s.claim_next('w'); a=s.request_approval(r,'send:a'); s.decide_approval(a,'approved'); tok=s.authorize_operation(r,'op','send:a',c['_lease_token'],'w'); s.record_intent(r,'op',tok,c['_lease_token'],'w'); assert s.mark_executed('op') is True; assert s.mark_executed('op') is False; assert s.metrics()['duplicate_execution_count']==0; td.cleanup()
def test_gmail_read_only():
    g=GmailReadOnly(lambda q,n:['m1']); assert g.find_sent(deterministic_message_id('op')).state is State.FOUND
    try: g.send(); raise AssertionError()
    except ReadOnlyViolation: pass
def test_uncertain_gmail_never_blind_retry(): assert decide(False) is Decision.HOLD and decide(None) is Decision.HOLD
def test_strong_provider_may_retry(): assert decide(False,True,True) is Decision.RETRY

def main():
    ts=[v for k,v in sorted(globals().items()) if k.startswith('test_') and callable(v)]; failed=0
    for t in ts:
        try: t(); print(t.__name__+': PASS')
        except Exception as e: failed+=1; print(t.__name__+f': FAIL {type(e).__name__}: {e}')
    print(f'\n{len(ts)-failed}/{len(ts)} cloud tests passed'); raise SystemExit(1 if failed else 0)
if __name__=='__main__': main()
