# ADR 0001 — One canonical Skill layer, thin host adapters

**Status:** Accepted
**Date:** 2026-08-08

## Context

Claude Code and Codex both read Skills from `skills/<name>/SKILL.md`, but differ in
manifest path, marketplace path, native agent format, and project instruction file. A team
using both ends up maintaining two divergent copies of the same workflow — the problem
this product exists to solve. Solving it by copying into both would reproduce it.

## Decision

Keep **one canonical Skill layer** under `plugins/agent-harness/skills/`, shared verbatim
by both hosts. Confine host differences to `adapters/claude/` and `adapters/codex/`, which
hold integration details and **never workflow prose**.

Two consequences follow, and both are load-bearing:

1. **Canonical Skill frontmatter is restricted to `name` + `description`.** That is the
   intersection both hosts certainly accept. Codex's handling of unknown keys is
   unverified, so widening the set would be a guess.

2. **The canonical layer resolves no host-specific paths.** No `CLAUDE_SKILL_DIR`, no
   installation cache path, no `PLUGIN_ROOT`, no working-directory assumption.

## Consequences

**Good.** Workflow prose exists once. Skill content cannot drift between hosts, because
there is only one copy. Adding a third host later means adding an adapter, not forking.

**Costly.** Claude-specific frontmatter such as `disable-model-invocation` is unavailable
in the canonical layer — which is precisely why `apply-refinement` needs a host-independent
approval gate in its body rather than relying on host invocation control. Bundled helper
scripts cannot be located by any host-specific mechanism, so deterministic helper execution
is deferred until a portable method is verified.

**Enforced by.** `check_adapter_drift.py` (no copied prose), `validate_skills.py`
(frontmatter minimum set), `check_path_portability.py` (no host path assumptions).

## Alternatives considered

**Per-host Skill copies.** Rejected: reproduces the exact drift the product targets.

**Generate host variants from a template.** Deferred, not rejected. Viable once a concrete
need exists, and the drift protection would be golden-file tests. Introducing it before
that need is complexity without payment.

**Depend on the richer Claude frontmatter and let Codex ignore extra keys.** Rejected:
"ignore" is an assumption, not a verified behaviour. If it is confirmed later, this ADR
can be revisited.
