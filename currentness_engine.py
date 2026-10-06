"""Currentness classification must use the underlying observation date, not page/profile update time."""
from datetime import date,datetime

def classify_currentness(observed_at:str, as_of:str, *, current_days=90,recent_days=365,stale_days=1095)->str:
 try:
  o=datetime.fromisoformat(observed_at).date(); a=datetime.fromisoformat(as_of).date()
 except Exception as e: raise ValueError("invalid_date") from e
 age=(a-o).days
 if age<0: raise ValueError("future_observation")
 if age<=current_days:return "CURRENT"
 if age<=recent_days:return "RECENT"
 if age<=stale_days:return "HISTORICAL"
 return "STALE"

def profile_update_can_refresh_observation(*args,**kwargs)->bool:
 return False
