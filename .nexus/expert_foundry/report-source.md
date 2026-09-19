# Expert Foundry v0.1 Internal Design Record

Audience: NEXUS owner and implementing AI roles

Date: 2026-09-08

Scope: governed infrastructure for persistent scientific research, tacit
experience, hypothesis generation, invention and multi-AI coordination, with
metallurgy as the first proof domain.

Assumptions: existing research and coordination feature branches remain
unmerged; live providers and plant control are excluded; repository files are
the coordination surface.

Direct answer: build an append-only knowledge event layer above the existing
provider-neutral research and repository-backed handoff components. Separate
science, experience, hypotheses, experiments, results and inventions. Require
independent evaluation and human promotion.

Sources inspected: `.nexus/state/CURRENT_STATE.md` on main;
`research_evidence.py` on `feat/research-evidence-provider-v0.1`;
`research_lab.py` and its README on `feat/deep-research-lab-v0.1`;
`task_handoff.py` and `coordination_kit.py` on
`feat/nexus-coordination-kit-v0.2`; and the public mirror contract on
`feat/public-handoff-mirror-contract-v0.1`.

Material limitation: no external metallurgy literature was researched in this
architecture slice. Scientific ontology and claims begin in a separate,
source-cited research run after this storage and governance layer is reviewed.
