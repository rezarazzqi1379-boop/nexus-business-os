#!/usr/bin/env node
/**
 * branch-integrity-guard.cjs â€” PreToolUse nudge before a git commit/push, running
 * scripts/audit_branch_import_gaps.py and warning if any tracked file imports a module
 * whose only copy is untracked on this branch.
 *
 * Added 2026-09-17, directly following the discovery (this session) of two real instances
 * of this bug class: fal_vertical.py (commit e34c62b) and the nexus_system_bootstrap.py ->
 * system_capability_registry.py gap (commit 0f1cf63). Both were found by running
 * scripts/audit_branch_import_gaps.py manually; this hook makes that check automatic
 * instead of relying on someone remembering to run it before every commit/push.
 *
 * Same philosophy as compliance-guard.cjs: deliberately non-blocking. A false positive or
 * a broken Python environment on the runner must never stop a real commit -- this is a
 * visible nudge, not a gate. It never exits non-zero.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch (e) {
    return '';
  }
}

function main() {
  let raw = readStdin();
  let input = {};
  if (raw && raw.trim()) {
    try { input = JSON.parse(raw); } catch (e) { /* ignore malformed input */ }
  }
  const toolInput = input.tool_input || input.toolInput || {};
  const command = toolInput.command || '';

  // Only act on commands that look like they're about to record or publish history.
  if (!/\bgit\s+(commit|push)\b/.test(command)) {
    process.exit(0);
  }

  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const auditScript = path.join(projectDir, 'scripts', 'audit_branch_import_gaps.py');
  if (!fs.existsSync(auditScript)) {
    process.exit(0); // script not present in this checkout -- nothing to run, stay silent
  }

  let result;
  try {
    result = spawnSync('python', [auditScript], { cwd: projectDir, timeout: 15000, encoding: 'utf8' });
  } catch (e) {
    process.exit(0); // never block on a runner problem (missing python, timeout, etc.)
  }

  const out = (result && result.stdout) || '';
  const gapsHeader = '=== REAL GAPS: tracked file imports a module whose ONLY copy is untracked ===';
  const idx = out.indexOf(gapsHeader);
  if (idx === -1) {
    process.exit(0); // audit didn't run cleanly -- stay silent rather than guess
  }
  const gapsSection = out.slice(idx + gapsHeader.length);
  if (gapsSection.includes('None found')) {
    process.exit(0); // clean -- no nudge needed
  }

  process.stderr.write(
    `[branch-integrity-guard] scripts/audit_branch_import_gaps.py found tracked file(s) ` +
    `importing a module whose only copy is untracked on this branch -- a clean clone of ` +
    `this branch would fail to import it (this is exactly the fal_vertical.py bug from ` +
    `commit e34c62b). Details:\n${gapsSection.trim()}\n` +
    `[branch-integrity-guard] Review before ${/push/.test(command) ? 'pushing' : 'committing'} ` +
    `-- either commit the missing file(s) too, or confirm the import is dead code.\n`
  );
  process.exit(0);
}

main();