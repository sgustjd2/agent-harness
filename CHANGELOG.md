# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### M2 — shared Skill implementation (in progress)

#### Added — `init-project` (slice 2)

- **`init-project`, the second production Skill, and the first that writes files.**
  Creates `.agent-harness/` — `config.yaml`, `memory/{facts,decisions,patterns}.md`,
  `runs/`, `proposals/`, and a self-contained `.agent-harness/.gitignore` — and appends a
  marker block to `CLAUDE.md` and `AGENTS.md`. Instruction-only and dependency-free.
- **Two-phase approval.** Phase A inspects and proposes, touching nothing. Phase B
  applies only after approval tied to that specific proposal, re-checks targets
  immediately before writing, and stops on drift. Explicit invocation is not mutation
  approval, and stale approval is rejected rather than reused.
- Idempotent: a second run against an initialized repository produces no diff, reports
  existing files as unchanged, never duplicates a marker block, and never deletes.
- Verification gates are **proposed, never enabled and never executed**. Commands are
  argv arrays, never shell strings.
- `skills/init-project/references/config-template.yaml` — host-neutral configuration
  with no gate enabled; validated in tests against the project's own config schema.
- `skills/init-project/references/initialization-checklist.md` — the pre-write and
  post-write check.
- `skills/init-project/agents/openai.yaml` — implicit invocation **disabled**, because a
  Skill that changes a repository should start only when someone names it.
- `tests/test_init_project_skill.py` — 45 contract tests.

#### Changed — shared validator (slice 2)

- Skill safety contracts are now checked against **profiles** rather than one table:
  `read-only` for `plan-work`, `approval-gated-mutation` for `init-project`. A single
  shared table would have let a file-writing Skill declare itself read-only. Invariants
  common to both — never execute a command, never reach the network — live in
  `UNIVERSAL_SKILL_POLICY` and are inherited.
- Mutation-capable Skills must declare `allowed_path_roots`, their entire write surface.
  The validator rejects user-scope roots (`~`), absolutes, traversal, and anything under
  `.git/`, `plugins/`, `marketplace/` or `scripts/`.
- Required references are per-Skill, because the documents differ.
- New diagnostic codes: `SKILL_PROFILE_UNDECLARED`, `SKILL_WRITE_ROOTS_MISSING`,
  `SKILL_WRITE_ROOTS_UNEXPECTED`, `SKILL_WRITE_ROOT_FORBIDDEN`.
- The allowlist and forbidden-Skill tests now derive from `_common` instead of
  hard-coding a milestone's membership, so a future slice edits one list rather than
  restating it in every test file.

#### Added

- **`plan-work`, the first production Skill.** Turns a goal into a structured plan:
  tasks with stable IDs and completion conditions, dependency order, parallelization
  opportunities, acceptance criteria, and a verification plan whose every gate starts
  at `Not Run`. Instruction-only and dependency-free.
- `skills/plan-work/references/plan-template.md` — the output structure, field
  meanings, and ID conventions (`T-01`, `AC-01`, `V-01`, `R-01`).
- `skills/plan-work/references/quality-checklist.md` — the pre-return check, including
  the rule that no plan may claim a task, criterion, or gate passed.
- `skills/plan-work/agents/openai.yaml` — invocation policy only. Implicit invocation
  is enabled because the Skill is read-only; it grants no tools or permissions.
- A machine-checkable safety contract: implemented production Skills declare an
  `agent-harness:policy` marker that `validate_skills.py` parses as YAML, rather than
  the validator guessing intent from prose.
- Diagnostic codes `SKILL_POLICY_MARKER_MISSING`, `SKILL_POLICY_MARKER_MALFORMED`,
  `SKILL_MUTATION_NOT_PERMITTED`, `SKILL_COMMAND_BLOCK_PRESENT`,
  `SKILL_VERIFICATION_DEFAULT_INVALID`, `SKILL_REFERENCE_MISSING`,
  `SKILL_EXECUTABLE_DIR_PRESENT`, `SKILL_RUNTIME_DEPENDENCY`,
  `POLICY_INVOCATION_UNDECLARED`, `POLICY_GRANT_NOT_PERMITTED`.
- `tests/test_plan_work_skill.py` — 60 contract tests covering the frontmatter policy,
  name parity, references, path containment, the read-only marker, command-block
  prohibition, the `Not Run` default, the milestone allowlist, and OpenAI metadata.

#### Changed

- The installable-root Skill allowlist is now derived from
  `IMPLEMENTED_PRODUCTION_SKILLS` rather than a hard-coded single fixture name, so it
  widens one Skill at a time as each is built. The six unimplemented production Skills
  are still rejected.
- The shared `plugin_tree` test fixture copies the real `skills/` tree instead of
  hand-writing a stand-in, so the baseline cannot drift from what ships.

`plan-work` is **experimental**. Remaining M1 host verification is still a release
blocker.

### M1.1 — scaffold correction and scope audit

Corrective pass over the M1 scaffold. **M2 has not begun.**

#### Changed

- **Development validation now uses established libraries.** The hand-written YAML
  subset parser and hand-written JSON Schema subset validator were removed in favour of
  PyYAML (`yaml.safe_load`) and jsonschema. The plugin runtime remains dependency-free.
- **pytest is the authoritative test runner.** `run_all.py` became `validate_all.py`,
  which orchestrates the 12 deterministic validators and then invokes pytest.
- Catalogs are now **generated** from `marketplace/marketplace.source.json` rather than
  hand-maintained (Candidate C, provisional implementation strategy only).
- Renamed `check_packaging.py` to `check_path_containment.py` and
  `check_release_version.py` to `check_version_sync.py`.

#### Added

- Five packaging schemas: claude-plugin, codex-plugin, claude-marketplace,
  openai-marketplace, canonical-marketplace. None existed before.
- Stable diagnostic codes (`scripts/_diagnostics.py`); tests assert codes, not prose.
- 27 negative scenarios, up from 16.
- `scripts/m1_status.py`, which computes exit-criteria counts from a structured table.
- `requirements-dev.txt`, `pyproject.toml` with pytest markers, `.gitattributes`.
- `docs/m1-remediation.md`, `docs/m1-decisions.md`, `docs/m1-experiments.md`,
  `docs/m1-traceability.md`.

#### Removed

- All seven production Skill placeholders from the installable plugin root.
- `.github/workflows/release.yml` — release automation is an M8 deliverable.
- `agents/`, `scripts/`, `core/roles/`, `core/workflows/`, `adapters/codex/agent-templates/`
  from the installable plugin root.
- Empty M2/M5/M6 stub trees under `tests/`.

#### Fixed

Three defects the hand-written tooling had hidden:

- a path-traversal hole: `./../skills/` matched the schema path pattern
- UNC paths reported as absolute rather than UNC
- catalog generation emitted CRLF on Windows, so output was not byte-deterministic

#### Corrected

- Exit-criteria arithmetic. The prior report claimed 12 of 17 while listing 11.
  The count is now computed programmatically: **13 of 17**.

## [0.0.1] - 2026-08-08

M1 — repository and validation scaffold. No production Skill behaviour.

[Unreleased]: https://github.com/OWNER/agent-harness/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/OWNER/agent-harness/releases/tag/v0.0.1
