# Codex adapter

Host-specific integration for Codex and the OpenAI surfaces.

## What belongs here

- `AGENTS.md` marker-block template (<= 2 KiB)
- registration vs installation procedure -- see `install-surface.md`
- experiment records -- `hook-root-findings.md` (A), `path-resolution.md` (B)
- optional agent TOML templates, never installed without explicit approval

## What must never appear here

Workflow prose copied from `skills/` (PRIN-01, enforced by `check_adapter_drift.py`).

## `agent-templates/` (M4)

Six optional TOML files, one per role. **Nothing installs them.** They are the only files
in this repository designed to be copied *out* of it, into a project's `.codex/agents/`,
and that copy is made by a human following `docs/install-codex.md`.

No Skill writes there. `.codex/` and `.claude/` are on the forbidden write-prefix list, so
a Skill cannot even declare the path -- a host agent definition changes the permissions of
every later session, and a Skill able to write one could widen its own authority for the
next run.

The core workflow does not need them. Codex's own subagents carry the role instructions
from the Skill bodies; a template adds sandbox-level reinforcement where the role has a
fixed mode, and nothing else.

`validate_agent_templates.py` checks them at build time -- required fields, no unknown
key, no invented sandbox mode, and no path, command or network reference. FR-021 requires
validation before a copy; running it here means a malformed template never reaches the
point of being copied, and a malicious fork has to defeat a check that lives in the
repository rather than one that only exists in a procedure.
