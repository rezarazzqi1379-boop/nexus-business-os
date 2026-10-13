"""Governed commercial source registry: role-aware admission and permitted use."""
from dataclasses import dataclass
from enum import Enum

class SourceRole(str,Enum):
 PROCUREMENT_AUTHORITY="PROCUREMENT_AUTHORITY"; AWARD_AUTHORITY="AWARD_AUTHORITY"
 SUPPLIER_ROUTE="SUPPLIER_ROUTE"; OEM_INSTALLED_BASE="OEM_INSTALLED_BASE"
 TRADE_STATISTICS="TRADE_STATISTICS"; DISCOVERY="DISCOVERY"

class SourceAuthority(str,Enum):
 PRIMARY="PRIMARY"; OFFICIAL="OFFICIAL"; SECONDARY="SECONDARY"; DISCOVERY_ONLY="DISCOVERY_ONLY"

@dataclass(frozen=True)
class CommercialSource:
 source_id:str; country:str; host:str; role:SourceRole; authority:SourceAuthority
 searchable:bool=True; attachments:bool=False; awards:bool=False; registration:bool=False
 live_refresh_required:bool=True; notes:str=""

def valid_source(s:CommercialSource)->bool:
 return bool(s.source_id and s.country and s.host and "." in s.host)

def may_support_current_procurement(s:CommercialSource)->bool:
 return valid_source(s) and s.role==SourceRole.PROCUREMENT_AUTHORITY and s.authority in {SourceAuthority.PRIMARY,SourceAuthority.OFFICIAL} and s.live_refresh_required

def may_support_verified_winner(s:CommercialSource)->bool:
 return valid_source(s) and s.awards and s.role in {SourceRole.AWARD_AUTHORITY,SourceRole.PROCUREMENT_AUTHORITY} and s.authority in {SourceAuthority.PRIMARY,SourceAuthority.OFFICIAL}

def discovery_only(s:CommercialSource)->bool:
 return s.authority==SourceAuthority.DISCOVERY_ONLY or s.role==SourceRole.DISCOVERY

def seed_sources()->tuple[CommercialSource,...]:
 return (
  CommercialSource("KZ-UNIFIED-PROC","KZ","zakup.gov.kz",SourceRole.PROCUREMENT_AUTHORITY,SourceAuthority.PRIMARY,attachments=True,awards=True,registration=True),
  CommercialSource("KZ-SAMRUK","KZ","zakup.sk.kz",SourceRole.PROCUREMENT_AUTHORITY,SourceAuthority.PRIMARY,attachments=True,awards=True,registration=True),
  CommercialSource("KZ-MITWORK","KZ","eep.mitwork.kz",SourceRole.PROCUREMENT_AUTHORITY,SourceAuthority.PRIMARY,attachments=True,awards=True,registration=True),
  CommercialSource("AM-ARMEPS","AM","armeps.am",SourceRole.PROCUREMENT_AUTHORITY,SourceAuthority.PRIMARY,attachments=True,awards=True,registration=True),
  CommercialSource("AM-EAUCTION","AM","eauction.armeps.am",SourceRole.PROCUREMENT_AUTHORITY,SourceAuthority.PRIMARY,attachments=True,awards=True),
  CommercialSource("TJ-EPROC","TJ","eprocurement.gov.tj",SourceRole.AWARD_AUTHORITY,SourceAuthority.PRIMARY,attachments=True,awards=True,registration=True),
  CommercialSource("OM-JSRS","OM","businessgateways.com",SourceRole.SUPPLIER_ROUTE,SourceAuthority.OFFICIAL,registration=True,notes="registration/opportunity route; not proof of buyer demand"),
  CommercialSource("GLOBAL-COMTRADE","GLOBAL","comtradeplus.un.org",SourceRole.TRADE_STATISTICS,SourceAuthority.PRIMARY,notes="country/product trade evidence; not company buyer proof"),
 )

def source_by_id(source_id:str)->CommercialSource|None:
 return next((s for s in seed_sources() if s.source_id==source_id),None)
