# Experiment B — Skill script path resolution (Codex)

**Question.** Can a canonical, cross-host Skill locate its bundled scripts deterministically
on this host, without assuming the working directory?

**Status: Open (Q-IMPL-003 / FR-027-B). NOT RUN.**

## Why this is separate from experiment A

Experiment A (ATS-028) verified that **plugin hook commands** receive `PLUGIN_ROOT` and
`PLUGIN_DATA`. That says nothing about the Skill execution context. Whether those
variables are inherited by a command a Skill starts is undocumented, so we do not assume
it. **A's result is not evidence for B.**

## Candidates to try, in order

| # | Candidate | Note |
| :--- | :--- | :--- |
| 1 | Skill-directory-relative path, no cwd assumption | preferred if it works |
| 2 | Host-provided path variable | No portable Skill-directory variable is documented for Codex. Do not claim an equivalent to `${CLAUDE_SKILL_DIR}` exists. |
| 3 | Is `PLUGIN_ROOT` inherited into Skill-started commands? | test, do not assume |
| 4 | Project-local launcher | installed only after explicit approval |

## Method constraints

- A minimal non-production fixture Skill only, held OUTSIDE the installable plugin
  root at `tests/fixtures/host-tests/skill-script-path/`. A probe inside the
  installable root would be a product surface.
- **Static inspection is not a result.** Only an actual execution counts as `verified`.
- No destructive commands. Nothing written outside a temporary test directory.
- SEC-22 applies: no environment dumps, no secrets.
- **Excluded from normal CI**: this needs Skill execution, which may require a paid or
  interactive model invocation. It is a documented manual host test (PRD §23.1.1).

## Results

| Candidate | Result | Host | Version | Notes |
| :--- | :--- | :--- | :--- | :--- |
| 1. relative, no cwd | `not-run` | — | — | — |
| 2. host path variable | `not-run` | — | — | — |
| 3. `PLUGIN_ROOT` inherited | `not-run` | — | — | — |
| 4. project-local launcher | `not-run` | — | — | — |

## Consequence if nothing is verified

FR-027-B's deferral condition fires: deterministic helper execution is postponed to the
adapter phase, and the MVP Skills operate through direct model file access instead. That
weakens determinism (NFR-008), and the weakening must be stated in `docs/compatibility.md`
and in each run's `result.md` rather than passed over.

**M1 does not implement production Skill helper execution regardless of the outcome.**
