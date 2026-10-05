"""Aggregate evidence-backed historical outcomes for Commercial Genome."""
from collections import Counter
from commercial_genome import comparable
def outcome_summary(target,history,minimum_similarity=.5):
 matches=comparable(target,history,minimum_similarity)
 counts=Counter(); usable=[]
 for score,g in matches:
  if g.outcome=="UNKNOWN" or not g.outcome_evidence_refs:continue
  counts[g.outcome]+=1; usable.append((score,g.opportunity_id))
 return {"comparable_cases":len(usable),"outcomes":dict(sorted(counts.items())),"matches":tuple(usable)}
