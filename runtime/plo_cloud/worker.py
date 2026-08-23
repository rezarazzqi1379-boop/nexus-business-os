import argparse,json,os
from plo_core import PLOStore

def run_once(db):
    s=PLOStore(db); recovered=s.recover_orphans()
    return {"mode":"PLO_CLOUD_READ_ONLY","db":db,"gmail_write_enabled":False,"recovered":recovered,"metrics":s.metrics()}
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--db',default=os.getenv('NEXUS_PLO_DB','/data/nexus_plo.db')); a=p.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.db)),exist_ok=True); print(json.dumps(run_once(a.db),indent=2))
