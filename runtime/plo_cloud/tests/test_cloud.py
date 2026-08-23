import os,sys,tempfile
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,ROOT)
from plo_core import PLOStore,ApprovalError,OwnershipError
from gmail_readonly import GmailReadOnly,ReadOnlyViolation,deterministic_message_id,State
from reconciliation import decide,Decision

def fresh():
    td=tempfile.TemporaryDirectory(); return td,PLOStore(os.path.join(td.name,'p.db'))

def test_approval_before_side_effect():
    td,s=fresh(); r=s.enqueue('send','k1',True); c=s.claim_next('w')
    try: s.authorize_operation(r,'op','send:a',c['_lease_token'],'w'); raise AssertionError()
    except ApprovalError: pass
    a=s.request_approval(r,'send:a'); s.decide_approval(a,'approved'); tok=s.authorize_operation(r,'op','send:a',c['_lease_token'],'w'); s.record_intent(r,'op',tok); assert s.operation_state('op')=='intended'; td.cleanup()
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
def test_recovery():
    td,s=fresh(); r=s.enqueue('x','k4'); s.claim_next('w',-1); assert r in s.recover_orphans(); assert s.metrics()['pending']==1; td.cleanup()
def test_duplicate_metric():
    td,s=fresh(); r=s.enqueue('send','k5',True); c=s.claim_next('w'); a=s.request_approval(r,'send:a'); s.decide_approval(a,'approved'); tok=s.authorize_operation(r,'op','send:a',c['_lease_token'],'w'); s.record_intent(r,'op',tok); s.mark_executed('op'); s.mark_executed('op'); assert s.metrics()['duplicate_execution_count']==1; td.cleanup()
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
