# Codex adapter

Host-specific integration for Codex and the OpenAI surfaces.

## What belongs here

- `AGENTS.md` marker-block template (<= 2 KiB)
- registration vs installation procedure -- see `install-surface.md`
- experiment records -- `hook-root-findings.md` (A), `path-resolution.md` (B)
- optional agent TOML templates, never installed without explicit approval

## What must never appear here

Workflow prose copied from `skills/` (PRIN-01, enforced by `check_adapter_drift.py`).

## M1 status

Placeholder. The Codex adapter is built in M4. There is no `agent-templates/` directory:
M1.1 removed the empty placeholder because an empty directory carries no M1 purpose.
The templates arrive in M4, and even then they are copied only after the user explicitly
approves, into project scope by default.
