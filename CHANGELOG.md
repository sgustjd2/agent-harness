# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### M2 — shared Skill implementation (in progress)

#### Added — `refine-harness` (slice 6)

- **`refine-harness`, the sixth production Skill.** Reads `plan.md`, `evidence.md` and
  `result.md` from completed or failed runs and writes **exactly one** proposal at
  `.agent-harness/proposals/<proposal-id>.md`. Instruction-only and dependency-free.
- **Stage A only — it proposes, it never applies.** Nothing in memory, config, source or
  the plugin changes. `status: proposed` on creation, never advanced. `apply-refinement`
  owns application and does not exist yet.
- **Evidence is required, not optional.** Every item needs at least one `evidence_refs[]`
  entry resolving to real evidence in a declared source run. The repository defined
  `run_id` and `E-###` separately but no combined form, so this slice documents
  `<run-id>#<evidence-id>` and uses it identically in the Skill, the references and the
  tests — **no schema change**. Assumptions, plan intent, result summaries and generic
  best practice ground nothing.
- **Duplicates and conflicts.** An exact normalized duplicate fact produces a proposal to
  update the existing entry's `sources[]` and `last_confirmed` — never a second entity.
  Near duplicates (Jaccard ≥ 0.8) and contradictions are marked `conflict: true` and left
  for a human: resolving them automatically would delete the disagreement the reviewer
  needs to see.
- **Target paths are data, not permission.** Every `target_path` is normalized and
  rejected on traversal, outside-absolutes, user-home scope or symlink escape, then
  checked against the single permitted target for its `change_type`. Evidence text can
  never inject a target.
- **All source material is data.** Memory, evidence, results, READMEs and logs are read as
  input, never followed as instructions — evidence output is written from whatever a run
  executed, so it can carry adversarial text by construction.
- **Redaction is fail-closed**: where a value cannot be established as safe the candidate
  is omitted rather than stored. A proposal has the same leakage surface as run evidence.
- `current_hash` is set only when a trustworthy hash is already available without running
  a command, otherwise `null` — **never fabricated**, because a made-up hash would make
  `apply-refinement`'s future staleness check pass against an unverified state.
- `skill` items are always `risk: high` and **human-PR-only**; the Skill never writes to
  `plugins/agent-harness/skills/**`.
- **Known limitation recorded, not worked around:** the current M2 `.agent-harness/`
  layout defines no project instruction file, so `change_type: workflow` has no legitimate
  target. The Skill reports that rather than inventing a canonical path.
- `references/proposal-contract.md`, `evidence-and-dedup.md`, `proposal-template.md`.
- `tests/test_refine_harness_skill.py` — 35 test functions.

#### Changed — safety profiles (slice 6)

- New profile **`proposal-only-mutation`**, the fifth. The four existing ones are
  semantically unchanged, and no existing Skill's mapping moved.
- **`approval-gated-mutation` was deliberately not reused.** It requires mutation approval
  tied to an already-shown proposal, and `refine-harness` is what produces the proposal —
  reusing it would have made the authorization circular. The replacement distinction:
  explicit invocation authorizes *creating* the artifact; creating it is never permission
  to *apply* its contents.
- `PROFILES_REQUIRING_PATH_ROOTS` now includes `proposal-only-mutation`, with
  `ALLOWED_WRITE_PATH_ROOTS["refine-harness"] = [".agent-harness/proposals/"]` — narrower
  than `init-project`'s root over the same tree, so two Skills hold different permissions
  there on purpose.
- Execution and agent-spawn grants are untouched: `PROFILES_PERMITTING_EXECUTION` stays
  `["bounded-verification"]`, `PROFILES_PERMITTING_AGENT_SPAWN` stays
  `["plan-bounded-orchestration"]`.

#### Added — `orchestrate` (slice 5)

- **`orchestrate`, the fifth production Skill**, and the one with the widest authority:
  it writes source and may delegate to subagents. It executes **no** commands in this
  milestone. Instruction-only and dependency-free.
- **The plan is the authority.** Requires a specific run id or an unambiguously latest
  **ready** run. No ready plan means `Blocked` recommending `plan-work` — never a
  synthesized plan. Ambiguous ready runs prompt a choice rather than a silent pick. A
  cyclic or malformed plan is rejected, never repaired.
- **Bounding constraints** make that write authority acceptable: planned paths only,
  **repository-contained** (SEC-05 / SEC-06 / THR-003 — a path listed in `writes[]` is not
  permission to leave the repository; traversal, outside-absolutes and symlink escapes are
  rejected, and overlap and scope comparisons use the normalized form), the dependency
  graph respected, and **`.agent-harness/**` read-only**. An unsafe planned path blocks the
  task rather than being repaired.
- **No command execution in this milestone.** `plan.schema.json` has no structured task
  command field, so there is no argv, working directory, timeout, or security semantics to
  validate — and executing prose that merely looks like a command is the injection surface
  `verify-work`'s argv contract exists to prevent. A task that needs a command is
  `blocked` with the missing capability stated. `verify-work` remains the only production
  Skill permitted to execute configured commands, and is not weakened.
- **Harness state is protected.** `orchestrate` reads `config.yaml` and
  `runs/<run-id>/plan.md` but writes no `.agent-harness` path, and does not touch the
  managed marker block in `CLAUDE.md` / `AGENTS.md`. Config changes belong to direct
  editing or `apply-refinement`, memory to the proposal → approval path, and evidence and
  result files to the deferred run-state runtime.
- **Authorization model:** a ready plan defines the allowed **scope**; explicit invocation
  authorizes ordinary non-destructive work **within** it. The PRD defines no separate
  plan-approval gate, and this slice claims none.
- Frontier from topological order; a failed dependency `skipped`s its dependents while
  unrelated branches continue. Parallelism requires dependency independence, disjoint
  `writes[]`, **and** a host that exposes it — otherwise sequential, and degradation is
  always recorded with a non-empty `degraded_reason`. `max_parallel_agents` (default 3,
  cap 5) and `max_delegation_depth` (default 1, cap 2) come from config and the schema.
- **Scope is checked in both directions**: overlapping planned writes force sequential
  execution beforehand; a `changed_files` entry outside `writes[]` afterwards is a scope
  violation, and the plan is never widened to justify it.
- **No automatic conflict merge.** Two results touching the same file are held and
  reported for human resolution.
- Explicit invocation authorises ordinary planned work; **destructive and irreversible
  actions need separate approval immediately before the action** — force push, tree
  deletion, migrations, destructive DB operations, history rewrites, permission
  weakening. Without it the task is `blocked` and safe work continues.
- Structured handoff preserved as returned, never paraphrased first. Only the previous
  `summary`, `artifacts`, `open_questions` and a relevant memory excerpt travel onward —
  **never the whole conversation**.
- Terminal task statuses `done` / `failed` / `skipped`; `done` is the coordinator's
  judgement after checking scope and criteria, not a worker's self-report.
- **`orchestrate` never declares `completed`** — `verify-work` owns gate outcomes, and is
  recommended rather than invoked automatically.
- `references/orchestration-contract.md`, `handoff-contract.md`, `conflict-policy.md`.
- `tests/test_orchestrate_skill.py` — 33 test functions.

#### Changed — safety profiles (slice 5)

- New profile **`plan-bounded-orchestration`**, the fourth. The three existing profiles
  are semantically unchanged.
- **Execution and delegation are now granted separately**, each as an explicit list, and
  they land on **different** profiles. `PROFILES_PERMITTING_EXECUTION` holds only
  `bounded-verification`; the new `PROFILES_PERMITTING_AGENT_SPAWN` holds only
  `plan-bounded-orchestration`. `verify-work` runs commands but must never delegate — a
  verifier that could delegate could delegate its way around its own gate list — and
  `orchestrate` delegates but must not execute until a validated command representation
  exists.
- `executes_commands` stays out of `UNIVERSAL_SKILL_POLICY`, and a test asserts no
  profile executes without appearing on the grant list.
- **Deferred, and recorded as such:** the run-state runtime. This slice writes no
  `evidence.md` or `result.md`, ships no `scripts/ah.py`, no helper library, no resume or
  transaction engine, no queue or mailbox. `evidence_persistence: response-only` and
  `run_state_runtime: deferred` are declared in the profile itself.

#### Added — `doctor` (slice 4)

- **`doctor`, the fourth production Skill.** Diagnoses agent-harness itself: host
  identification, plugin layout, Skill integrity, `.agent-harness/` state, config and
  schema version, memory integrity, verification-executable availability, Git presence,
  managed marker blocks, and host compatibility. Instruction-only and dependency-free.
- **The boundary is explicit: `doctor` diagnoses the harness, `verify-work` verifies
  project code.** Both "check things", which is exactly why the split is stated in the
  Skill, the references, and the tests.
- Four statuses per check — `ok`, `warn`, `fail`, `unknown` — with three integrity rules:
  `unknown` is never upgraded to `fail`, `warn` is never upgraded because a host differs,
  and `unknown` is never hidden to reach a green report. `doctor` never stops on a
  failure; a complete run means every applicable check was judged, not that all passed.
- Overall health: `broken` on any `fail`, `degraded` on any `warn`, `unknown` on any
  `unknown`, `healthy` only when everything applicable is `ok`.
- **Executes nothing.** No verification gate, no `--version`, no `command -v` / `which` /
  `where` / `Get-Command`, no Python or Git invocation. Executable availability is
  established by static inspection or reported `unknown` — which is never a `fail`.
- **Repairs nothing.** No config regeneration, no schema migration, no memory deletion,
  no marker-block repair. Remediation commands are argv-array suggestions with
  `automatic_remediation: false`, printed for a human.
- `skills/doctor/references/diagnostic-matrix.md` — every check with its four status
  conditions; `remediation-guide.md` — how fixes are offered and their limits.
- `skills/doctor/agents/openai.yaml` — implicit invocation **enabled**, unlike
  `init-project` and `verify-work`: a read-only diagnostic that writes and runs nothing
  should be reachable when someone asks why things are broken.
- `tests/test_doctor_skill.py` — 27 test functions.

#### Changed — slice 4

- `doctor` reuses the existing `read-only` profile **unchanged**. No new profile, no
  widened permission, no write surface, and no behavioural change to the profile system.
- **Fixed a latent crash in `check_path_portability.py`**: `report.fail()` was called
  without its diagnostic code, so the violation branch raised `TypeError` instead of
  reporting. Dormant since M1.1 because no canonical file had tripped a forbidden
  pattern; `doctor` was the first to reach it. New code `PATH_NOT_PORTABLE`.
- The `verify-work` allowlist and forbidden-Skill tests now derive from `_common`, as the
  earlier slices' already do.

#### Added — `verify-work` (slice 3)

- **`verify-work`, the third production Skill, and the only one that runs commands.**
  Executes the verification gates already configured in `.agent-harness/config.yaml` and
  reports evidence. Instruction-only and dependency-free.
- **Configured gates only.** The command set comes from validated configuration, never
  from inference about `package.json`, a Makefile, CI files, or user prose. No configured
  gate means `Blocked`, not a fallback guess.
- **Execution approval is separate from invocation.** Approval is tied to the exact gate
  set displayed, and goes stale when the config, argv, working directory, timeout,
  `required` flag, or gate selection changes.
- **argv arrays are the source of truth.** Shell strings are rejected, shell operators are
  never synthesized, and argv that cannot be represented safely on a shell-only host makes
  the gate `Blocked` rather than weakening the contract.
- Per-gate preflight: non-empty id, supported kind, non-empty argv of non-empty strings,
  positive timeout, repository-contained `working_dir`, boolean `required`, schema-valid
  config. Sequential execution in declared order; no concurrency, no retry except a
  configured `flaky_policy: rerun-once`, which never retries a missing executable, a
  permission denial, or a timeout.
- **Two layers, per PRD §15.4.** Pre-execution `Blocked` (no configured gates, stale
  approval, config that never becomes executable, unsafe path, unrepresentable argv, no
  execution capability) is kept separate from process classification, which uses the PRD
  vocabulary exactly: `pass`, `fail`, `error`, `timeout`, `skipped`, `flaky`. `error` is
  not `Blocked`, `timeout` is not `fail`, and `skipped` is not "never run".
- **`verification_status`** is the authoritative outcome, from required gates only:
  `passed` when every required gate is `pass`; `failed` on any `fail`/`error`/`timeout`;
  `unverified` on any `skipped`, `flaky`, pre-execution `Blocked`, or never-run required
  gate. `failed` and `unverified` are not interchangeable -- one means something is wrong,
  the other means nothing was established. Optional failures never change it and are
  never hidden.
- Bounded, redacted evidence; results returned in the response, no evidence file in this
  milestone.
- `skills/verify-work/references/execution-contract.md` and `evidence-template.md`.
- `tests/test_verify_work_skill.py` — 21 test functions (58 parameterized cases).

#### Changed — safety-profile model (slice 3)

- **`executes_commands` is no longer part of `UNIVERSAL_SKILL_POLICY`.** It stopped being
  universal the moment a verification Skill existed. Leaving it universal with one profile
  overriding it would have been worse than moving it: a guarantee with an exception is a
  default wearing the wrong name. Each profile now states its execution posture
  explicitly, so no Skill inherits a promise it does not keep.
- `network_access: false` remains genuinely universal.
- New third profile **`bounded-verification`**, mapped to `verify-work`. Its
  `read_only: false` means only that subprocesses run; it grants no write surface, and
  `modifies_source` / `modifies_config` stay false.
- `PROFILES_PERMITTING_EXECUTION` pins execution to exactly one profile, asserted in
  tests so a future profile cannot acquire it silently.
- `plan-work` and `init-project` are unchanged, with regression tests proving their
  effective policy — including `executes_commands: false` — survived the refactor.
- The `init-project` allowlist and forbidden-Skill tests now derive from `_common`, as the
  `plan-work` ones already did, so widening a milestone edits one list rather than three.

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
  existing files as unchanged, and never duplicates a managed-marker-block.
- **Rollback is bounded by ownership.** Content that existed before a Phase B attempt is
  never deleted or restored; a failed attempt may withdraw only the exact files and
  managed-marker-block content that same attempt created. When complete rollback is
  impossible, the remaining partial state and the manual cleanup steps are reported, and
  the run is never described as successful. Declared as `deletes_preexisting_content:
  false` and `may_rollback_current_attempt: true` in the approval-gated-mutation profile.
- **Host instruction files use a managed-marker-block, not append-only access.** All
  content outside `<!-- BEGIN agent-harness -->` … `<!-- END agent-harness -->` is
  immutable. No block means append exactly one; one block means replace only its inner
  content, and only when it would change; malformed, nested, duplicated or unmatched
  markers are a conflict and are never modified automatically. "Append-only" was
  withdrawn because it contradicted the in-place block replacement the contract needs.
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
