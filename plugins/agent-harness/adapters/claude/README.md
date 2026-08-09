# Claude Code adapter

Host-specific integration for Claude Code. **This layer exists so the canonical Skill
layer does not have to know about any host.**

## What belongs here

| File | Holds |
| :--- | :--- |
| `capability-notes.md` | what this host can and cannot do, with each claim's evidence |
| `claude-md-block.md` | the literal `CLAUDE.md` block text, as an artifact |
| `path-resolution.md` | the Q-IMPL-003 experiment record — still open |

The six role subagents are **not** here. They live in `../../agents/`, because that is
the path Claude Code discovers them at; a host component has to sit where the host looks.
This directory holds what is true *about* the host rather than what is loaded *by* it.

## What must never appear here

Workflow prose copied from `skills/`. `check_adapter_drift.py` fails the build on any run
of 20+ consecutive words shared with a canonical Skill body (PRIN-01), and separately caps
adapter volume at 20% of Skill volume (NFR-004) — a limit that has been enforced rather
than merely reported since M3.

The split to keep in mind: a Skill states the **rules** for the marker block; this
directory holds the **block**. Two files describing the same rules would be the drift the
check exists to catch.

## Nothing here is read at runtime

A canonical Skill assumes no path variable, no installation cache path, and no working
directory, so it cannot locate a sibling directory — Q-IMPL-003, open since M1 and
recorded in `path-resolution.md`. These files are therefore reference material for people
and for whatever adapter machinery lands after that question is settled.

Do not "fix" a Skill to read one of them. It would be a path that cannot resolve, failing
only on a host, only at runtime.
