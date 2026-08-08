# Experiment A — plugin hook root variables (ATS-028)

**Question.** Can a plugin hook command resolve the installed plugin root and a writable
data directory deterministically?

**Scope limit — read this first.** This experiment answers the **hook** question only.
Its result must **not** be used as evidence for Skill-context path resolution. That is
experiment B (ATS-020), recorded in `path-resolution.md`. Conflating the two is exactly
the mistake FR-027 was split to prevent (RISK-026).

## What the documentation states

| Variable | Meaning | Provided to |
| :--- | :--- | :--- |
| `PLUGIN_ROOT` | installed plugin root | plugin hook commands |
| `PLUGIN_DATA` | plugin's writable data directory | plugin hook commands |
| `CLAUDE_PLUGIN_ROOT` | compatibility alias | plugin hook commands |
| `CLAUDE_PLUGIN_DATA` | compatibility alias | plugin hook commands |

Status: **Verified** for the hook execution context.

Not stated anywhere we found: whether these are inherited by arbitrary commands started
from a Skill body. We do not assume it.

## Why this is recorded but not used

The MVP ships **no hooks** (FR-022, DEC-C16). This finding is future justification for
an opt-in hook capability, not a licence to depend on hook variables now. The fixture
under `tests/fixtures/host-tests/codex-hook-root/` is a test artifact and is not part of the
installable plugin.

## Method

`tests/fixtures/host-tests/codex-hook-root/probe_hook_root.py`, invoked from a minimal hook definition.
It needs no model, so it can run in CI.

**Recording constraints (SEC-22).** The probe reports booleans only:

- presence of each variable — `true` / `false`, never the value
- whether each path is a directory
- whether `PLUGIN_DATA` resolves inside `PLUGIN_ROOT`
- whether the compatibility aliases match their primaries

No variable values, no secrets, no full environment dump. No real user repository is
modified and nothing is written outside a temporary directory.

## Results

**Status: NOT RUN.**

M1 requires that this experiment be *defined and its outcome recorded*. It has not been
executed against a host yet. A negative result would be a valid outcome; an unrecorded
result is not.

| Field | Value |
| :--- | :--- |
| Host | _not recorded_ |
| Host version | _not recorded_ |
| Command | _not recorded_ |
| Exit code | _not recorded_ |
| `PLUGIN_ROOT` present | _not recorded_ |
| `PLUGIN_DATA` present | _not recorded_ |
| Compatibility aliases present | _not recorded_ |
| `PLUGIN_DATA` inside `PLUGIN_ROOT` | _not recorded_ |
| Output summary | _not recorded_ |
| Result | `not-run` |

## Consequence for M1 exit E13

E13 requires hook-root behaviour to be tested **separately** from Skill-script behaviour.
The separation exists in the design — two experiments, two fixtures, two records, and a
CI check that the canonical layer never references `PLUGIN_ROOT`. **E13 is not yet
satisfied**, because neither experiment has been executed. See `docs/compatibility.md`.
