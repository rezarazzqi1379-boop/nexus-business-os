"""Evidence freshness and deterministic lead deduplication for steel intelligence."""
from __future__ import annotations
from datetime import date,datetime
from urllib.parse import urlsplit,urlunsplit

def canonical_domain(url:str)->str:
    h=urlsplit(url.strip()).hostname or ""
    h=h.casefold()
    return h[4:] if h.startswith("www.") else h

def lead_identity(country:str,company:str,domain:str="")->str:
    norm=lambda s:" ".join(s.casefold().split())
    return "|".join((norm(country),canonical_domain(domain) or norm(company)))

def evidence_freshness(observed_at:str,*,max_age_days:int=180,today:date|None=None)->str:
    try:d=datetime.fromisoformat(observed_at.replace("Z","+00:00")).date()
    except (ValueError,AttributeError):return "UNKNOWN"
    age=((today or date.today())-d).days
    if age<0:return "INVALID_FUTURE"
    return "FRESH" if age<=max_age_days else "STALE"
