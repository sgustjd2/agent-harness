# Claude Code adapter

Host-specific integration for Claude Code. **This layer exists so the canonical Skill
layer does not have to know about any host.**

## What belongs here

- `CLAUDE.md` marker-block template
- host path resolution, including `${CLAUDE_SKILL_DIR}` -- forbidden in the canonical layer
- host capability notes (Agent Teams, subagent behaviour)
- if adopted later: a Gate A strategy for Claude Code

## What must never appear here

Workflow prose copied from `skills/`. `check_adapter_drift.py` fails the build if 20+
consecutive words from a canonical Skill body reappear in an adapter file (PRIN-01).

## M1 status

Placeholder. The Claude adapter is built in M3.
