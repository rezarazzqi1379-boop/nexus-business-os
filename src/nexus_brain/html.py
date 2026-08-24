from __future__ import annotations

from html import escape
from typing import Any


STATUS_LABELS = {
    "fact": "FACT",
    "claim": "CLAIM",
    "estimate": "ESTIMATE",
    "inference": "INFERENCE",
    "hypothesis": "HYPOTHESIS",
    "assumption": "ASSUMPTION",
    "unknown": "UNKNOWN",
    "contradicted": "CONTRADICTED",
    "stale": "STALE",
    "superseded": "SUPERSEDED",
}


def _pill(text: str, css: str = "") -> str:
    return f'<span class="pill {escape(css)}">{escape(text)}</span>'


def _node_card(node: dict[str, Any]) -> str:
    status = node["epistemic_status"]
    tier = node["authority_tier"].replace("_", " ").upper()
    provenance = node.get("provenance") or []
    prov = escape(provenance[0]) if provenance else "NO PROVENANCE"
    value = node.get("attributes", {}).get("value")
    value_html = f'<div class="value">{escape(str(value))}</div>' if value is not None else ""
    return (
        '<article class="node-card">'
        f'<div class="node-meta">{_pill(STATUS_LABELS.get(status, status.upper()), status)}{_pill(tier, "tier")}</div>'
        f'<h4>{escape(node["label"])}</h4>'
        f'{value_html}'
        f'<div class="source">{prov}</div>'
        '</article>'
    )


def render_portfolio_html(portfolio: dict[str, Any]) -> str:
    """Render a dependency-free, read-only NEXUS Brain command surface."""
    project_sections: list[str] = []
    for project in portfolio["projects"]:
        blocked = not project["consequential_use_allowed"]
        state = "BLOCKED" if blocked else "DECISION-READY"
        blocker_pills = "".join(_pill(item.replace("_", " ").upper(), "blocker") for item in project["blockers"])
        cards = "".join(_node_card(item) for item in project["requirements"] + project["claims"] + project["unknowns"])
        contradictions = "".join(
            f'<li><strong>{escape(item["predicate"])}</strong> — {escape(item["reason"])}</li>'
            for item in project["contradictions"]
        ) or '<li>None detected</li>'
        project_sections.append(
            f'''<section class="project {'blocked' if blocked else 'ready'}">
              <header><div><span class="eyebrow">PROJECT</span><h2>{escape(project['project_id'])}</h2></div><span class="state">{state}</span></header>
              <div class="stats"><span>{project['counts']['facts']} facts</span><span>{project['counts']['claims']} claims</span><span>{project['counts']['unknowns']} unknowns</span><span>{project['counts']['contradictions']} contradictions</span></div>
              <div class="blockers">{blocker_pills or _pill('NO BLOCKERS', 'ok')}</div>
              <div class="nodes">{cards}</div>
              <details><summary>Contradiction radar</summary><ul>{contradictions}</ul></details>
            </section>'''
        )

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEXUS Brain</title>
<style>
:root{{--bg:#080a0d;--panel:#101318;--line:#262b33;--text:#f4f6f8;--muted:#8f99a8;--hot:#ff5a52;--ok:#6be49b;--warn:#ffcc66}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at 50% 0,#171b22 0,var(--bg) 40%);color:var(--text);font:14px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}}
main{{max-width:1440px;margin:auto;padding:32px}} .hero{{display:flex;justify-content:space-between;align-items:end;border-bottom:1px solid var(--line);padding:24px 0;margin-bottom:28px}}
h1{{font:700 clamp(32px,6vw,76px)/.9 system-ui;margin:8px 0}} .eyebrow{{letter-spacing:.28em;color:var(--muted);font-size:11px}}
.summary{{text-align:right;color:var(--muted)}} .project{{border:1px solid var(--line);background:rgba(16,19,24,.88);border-radius:20px;padding:22px;margin:18px 0}}
.project.blocked{{box-shadow:inset 3px 0 0 var(--hot)}} .project.ready{{box-shadow:inset 3px 0 0 var(--ok)}} .project header{{display:flex;justify-content:space-between;align-items:center}}
h2{{margin:4px 0 8px;font:700 24px system-ui}} .state{{letter-spacing:.12em;font-size:11px;border:1px solid var(--line);padding:8px 11px;border-radius:999px}}
.stats{{display:flex;gap:18px;flex-wrap:wrap;color:var(--muted);margin:8px 0 14px}} .pill{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:4px 8px;font-size:10px;letter-spacing:.08em;margin:2px 4px 2px 0}}
.pill.fact,.pill.ok{{border-color:#275c40;color:var(--ok)}} .pill.claim,.pill.inference{{border-color:#6b5827;color:var(--warn)}} .pill.unknown,.pill.blocker{{border-color:#72312e;color:#ff8a84}} .pill.tier{{color:#9eb3cf}}
.nodes{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px;margin-top:14px}} .node-card{{border:1px solid var(--line);border-radius:14px;padding:14px;background:#0c0f13;min-height:120px}}
.node-card h4{{font:600 14px system-ui;margin:10px 0 6px}} .value{{font-size:18px;color:white;margin:6px 0}} .source{{font-size:10px;color:var(--muted);overflow-wrap:anywhere;margin-top:12px}} details{{margin-top:16px;border-top:1px solid var(--line);padding-top:12px;color:var(--muted)}}
@media(max-width:600px){{main{{padding:16px}} .hero{{align-items:start;flex-direction:column}} .summary{{text-align:left;margin-top:12px}}}}
</style></head><body><main>
<div class="hero"><div><span class="eyebrow">NEXUS BUSINESS OS · BRAIN · READ ONLY</span><h1>Evidence → Decision</h1></div><div class="summary">{portfolio['project_count']} projects<br>{portfolio['blocked_project_count']} blocked by evidence/governance</div></div>
{''.join(project_sections)}
</main></body></html>'''
