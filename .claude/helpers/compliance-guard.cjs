#!/usr/bin/env node
/**
 * compliance-guard.cjs — PreToolUse reminder for edits to approval-gated /
 * lane-isolation-critical files.
 *
 * Added 2026-09-16 alongside .claude/agents/security/fal-compliance-reviewer.md
 * and .claude/skills/git-plumbing-merge/SKILL.md, as part of a review of the
 * project's Claude Code automation surface.
 *
 * Deliberately non-blocking: this project's own test suite already enforces
 * the real invariants (no send/outreach/execute-shaped functions, compliance
 * clearance separate from approval, lane isolation) structurally. This hook's
 * only job is to make sure a compliance-sensitive edit is never made without
 * a visible nudge to run the fal-compliance-reviewer subagent before commit —
 * it never exits non-zero, so it can never block or corrupt an edit.
 */
'use strict';

const fs = require('fs');

const GUARDED_SUBSTRINGS = [
  'approvals.py',
  'fal_vertical.py',
  'opportunity_suggestion_engine.py',
  'canonical_sources.py',
  'canonical_authority',
];

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
  const filePath = toolInput.file_path || toolInput.filePath || '';

  const hit = GUARDED_SUBSTRINGS.find((s) => filePath.includes(s));
  if (hit) {
    process.stderr.write(
      `[compliance-guard] "${filePath}" is approval-gated / lane-isolation-critical code.\n` +
      `[compliance-guard] Before committing this change, run the fal-compliance-reviewer subagent ` +
      `(no silent auto-approval, compliance clearance separate from approval, lane isolation holds, ` +
      `no new send/outreach/execute-shaped function).\n`
    );
  }
  process.exit(0);
}

main();
