# M1.1 remediation report

Evidence-based record of the M1.1 audit and correction pass. Not a planning document.

| | |
| :--- | :--- |
| Phase | M1.1 — deterministic scaffold correction and scope audit |
| Date | 2026-08-08 |
| Outcome | **M1 scaffold complete, host verification pending** |
| M2 | Not begun |

---

## 1. PRD integrity

`docs/PRD.md` was not modified. It was read only.

| | SHA-256 | Bytes |
| :--- | :--- | ---: |
| Before | `c6575532ebaa37a03cca32decd3007560cbc53714cbcea13abd209928186f3ef` | 349584 |
| After | `c6575532ebaa37a03cca32decd3007560cbc53714cbcea13abd209928186f3ef` | 349584 |

**Hashes match. PRD integrity verified.**

---

## 2. Reported concerns — verified against the files

Each concern was checked against the repository, not accepted from the report.

| # | Concern | Verdict | Evidence |
| :--- | :--- | :--- | :--- |
| 1 | Git not initialized | **Confirmed** | `git rev-parse` → *fatal: not a git repository* |
| 2 | Hand-written YAML parser | **Confirmed** | `scripts/_common.py:84 def parse_yaml_subset` |
| 3 | Hand-written JSON Schema validator | **Confirmed** | `scripts/_common.py:259 def validate_instance` |
| 4 | Five schemas are state, not packaging | **Confirmed, and worse than reported** | `core/schemas/` held config, plan, evidence, result, proposal. **Zero** packaging schemas existed. E3/E4 had been claimed Passed on field checks plus state schemas — neither validates a Codex manifest or catalog |
| 5 | "12 of 17" but 11 listed | **Confirmed** | The prior list contained E3, E4, E7, E8, E9, E10, E11, E14, E15, E16, E17 = 11. The total was written by hand |
| 6 | Only 16 negative fixtures | **Confirmed** | 16 cases existed against 27 required scenarios |
| 7 | Skill placeholders violate the plugin boundary | **Confirmed** | 9 Skill directories in the installable root: 7 production names + 2 fixtures |
| 8 | `release.yml` out of scope | **Confirmed** | Present. The PRD lists `release.yml` as an **M8** deliverable and omits it from the M1 CI deliverable (`validate.yml`, `test.yml`) |
| 9 | 167 files needs audit | **Partly** — actual count was **160**; the 167 figure included `__pycache__` | Audit performed, §4 |
| 10 | No pytest result | **Confirmed** | pytest was not installed; the default `py` was Python 3.9 |

Three documents the prompt named did not exist and were created in this pass:
`docs/m1-decisions.md`, `docs/m1-experiments.md`, `docs/m1-traceability.md`.

---

## 3. Conflicts between the PRD and the M1.1 directive

Recorded rather than silently resolved.

| Topic | PRD says | M1.1 directive says | Resolution |
| :--- | :--- | :--- | :--- |
| Production Skill placeholders | E15 permits `skills/*/SKILL.md` as placeholders | No production Skill directory may exist in the installable root | **Followed M1.1.** A shipped `SKILL.md` is host-discoverable regardless of body text, so a placeholder in the installable root is a product surface. All seven removed |
| Fixture Skill name | Example name `_fixture-noop`, "1~2 fixture Skills" | Exactly one, named `m1-discovery-fixture` | **Followed M1.1.** The PRD introduces the name with "예" (e.g.), so it is illustrative, not mandated. ATS-018-3's example identifier changes accordingly |
| State schemas | M1 deliverable #4 explicitly requires the five state schemas | Keep only if the PRD places them in M1 | **Kept**, moved to `core/schemas/state/` with a README stating they are never packaging evidence |
| `release.yml` | Appears in the §18 tree; is an M8 deliverable | Remove during M1 | **Removed.** The PRD's M1 CI deliverable lists only `validate.yml` and `test.yml` |
| Script names | Names `check_packaging.py`, and no `run_all`/`validate_all` | Names `check_path_containment.py`, `check_version_sync.py`, `validate_all.py` | **Followed M1.1** for these three; renames are recorded in §6 |
| `check_invocation_policy.py` | Named in M1 deliverable #5 | — | **Removed.** Its Gate A check is now in `validate_skills.py`; keeping both would inflate the check count, which Step 9 forbids. Its Gate B half targeted `apply-refinement/reference/`, which is no longer in the installable root |

---

## 4. File inventory

| | Count |
| :--- | ---: |
| Before | 160 |
| After | **97** |
| Removed | 78 |
| Added | 15 |

Excludes `.git/`, `.venv/`, `__pycache__/`, `.pytest_cache/`.

The M1 report's "167" counted `__pycache__`; the true starting figure was 160.

### By category, after

| Category | Count |
| :--- | ---: |
| Documentation (incl. adapter records, examples, READMEs) | 32 |
| Validation tooling (`scripts/`) | 17 |
| Required M1 source (manifests, canonical source, 5 packaging schemas, discovery fixture) | 16 |
| Deterministic test | 11 |
| Repository meta (`.gitignore`, `.gitattributes`, LICENSE, CHANGELOG, CI, pyproject, requirements) | 8 |
| Deferred state schema (`core/schemas/state/`) | 6 |
| Manual host-test fixture (`tests/fixtures/host-tests/`) | 5 |
| Generated M1 artifact (both native catalogs) | 2 |
| **Out-of-scope** | **0** |
| **Duplicate** | **0** |
| **Unexplained** | **0** |

### By top-level directory

| Directory | Count |
| :--- | ---: |
| `plugins/` | 31 |
| `scripts/` | 17 |
| `tests/` | 16 |
| `docs/` | 14 |
| (root) | 8 |
| `examples/` | 6 |
| `.github/` | 2 |
| `.agents/`, `.claude-plugin/`, `marketplace/` | 1 each |

### Removed, with reasons

| Files | Reason |
| :--- | :--- |
| 7 production Skill directories (~21 files) | Production Skill names in the installable root. A shipped `SKILL.md` is discoverable regardless of body text |
| `plugins/agent-harness/agents/` | Claude subagents are an M3 deliverable |
| `plugins/agent-harness/scripts/` | Production helper scripts are forbidden; helper execution is deferred until the path question is answered |
| `plugins/agent-harness/core/roles/`, `core/workflows/` | M2 deliverables; empty placeholders |
| `adapters/codex/agent-templates/` | M4 deliverable; empty placeholder |
| `.github/workflows/release.yml` | Release automation is an M8 deliverable |
| `tests/golden/`, `tests/integration/` | Target M2+ runtime output; nothing exists to compare or smoke |
| `tests/fixtures/corrupted-state/` | M5 concern |
| `tests/fixtures/legacy-schema/` | Exercises the state schema, now separated as non-packaging; migration is M5 |
| `tests/fixtures/stale-approval/` | Gate B semantics are an M6 deliverable; no M1 validator asserts on them |
| 16 old fixture directories (~40 files) | Superseded by parameterized scenarios asserting stable diagnostic codes |
| `scripts/run_all.py`, `check_packaging.py`, `check_release_version.py`, `validate_schemas.py`, `check_invocation_policy.py` | Renamed or superseded — §6 |
| 14 `.gitkeep` files | Directories now either hold real files or were removed |

---

## 5. Dependency and validator changes

**Plugin runtime: still zero third-party dependencies.** CI asserts the plugin root
declares no `requirements.txt`, `pyproject.toml`, `package.json` or lockfile.

**Development tooling now uses established libraries:**

| Concern | Before | After |
| :--- | :--- | :--- |
| YAML | hand-written subset parser (~90 lines) | `yaml.safe_load` — PyYAML 6.0.3 |
| JSON Schema | hand-written subset validator (~110 lines) | `jsonschema` 4.26.0, validator class resolved from each schema's own `$schema` |
| Test runner | custom `run_all.py` | pytest 8.4.2 |

`scripts/_common.py` now holds only infrastructure no library provides: bounded output,
diagnostic codes, home-path redaction, path containment, path-shape codes, atomic
writes, safe subprocess, frontmatter boundary extraction.

`scripts/preflight.py` remains as an explicitly **NON-AUTHORITATIVE** checker. It is
labeled as such in its output, checks only file readability, JSON syntax and path shape,
and cannot disagree with the authoritative validators because it never judges anything
they judge. Its result is not counted as schema validation.

### Defects the replacement immediately exposed

Three real bugs, all invisible to the hand-written tooling:

1. **Path traversal passed the schema.** `./../skills/` matched the path pattern because
   `.` is inside the character class `[A-Za-z0-9._-]`. Fixed with a negative lookahead
   rejecting a `..` segment. Covered by NS-08.
2. **UNC paths were misreported as absolute.** `//server/share` hit the `startswith("/")`
   branch first. UNC is now checked before absolute. Covered by NS-24.
3. **Generation was not byte-deterministic across platforms.** `write_text` emitted CRLF
   on Windows and LF elsewhere, so drift detection would fire on every Windows clone.
   Fixed by pinning `newline="\n"` and adding `.gitattributes`.

---

## 6. Script inventory — one authoritative list

The earlier report gave three different totals (11 validators, 13 plus a runner, 14
checks). There is now one inventory, produced by `scripts/validate_all.py --list`, and
each validator runs **exactly once**.

| # | Script | Authoritative? | Purpose |
| ---: | :--- | :--- | :--- |
| 1 | `preflight.py` | **No** — labeled non-authoritative | readability, JSON syntax, path shape |
| 2 | `generate_marketplaces.py --check` | yes | generation determinism + catalog drift |
| 3 | `validate_manifests.py` | yes (jsonschema) | both plugin manifests |
| 4 | `validate_marketplaces.py` | yes (jsonschema) | all three catalogs |
| 5 | `validate_skills.py` | yes (PyYAML) | Skill frontmatter + installable-root boundary |
| 6 | `check_path_containment.py` | yes | plugin-root containment, symlink escape |
| 7 | `check_path_portability.py` | yes | canonical layer uses no host path assumption |
| 8 | `check_version_sync.py` | yes | version agreement across 5 files |
| 9 | `check_no_install_command.py` | yes | no undocumented host command in user paths |
| 10 | `check_no_network.py` | yes | runtime imports nothing network-capable |
| 11 | `check_adapter_drift.py` | yes | adapters do not copy canonical Skill prose |
| 12 | `check_colocation.py` | yes (static half only) | dual-manifest co-location structure |

Plus `validate_all.py` (orchestrator, runs the 12 then pytest), `m1_status.py` (exit
criteria), and three non-executable modules: `_common.py`, `_authoritative.py`,
`_diagnostics.py`.

**Renames:** `check_packaging.py` → `check_path_containment.py`;
`check_release_version.py` → `check_version_sync.py`; `run_all.py` → `validate_all.py`.

---

## 7. Authoritative schema inventory

All five M1 packaging schemas now exist. Each declares Draft 2020-12, carries a stable
local `$id`, identifies itself as a local compatibility schema in `$comment`, cites the
official documentation URL, and states that host behaviour remains authoritative.

| Schema | Validates | Rejects unknown fields |
| :--- | :--- | :---: |
| `claude-plugin.schema.json` | `plugins/agent-harness/.claude-plugin/plugin.json` | yes |
| `codex-plugin.schema.json` | `plugins/agent-harness/.codex-plugin/plugin.json` | yes |
| `claude-marketplace.schema.json` | `.claude-plugin/marketplace.json` | yes |
| `openai-marketplace.schema.json` | `.agents/plugins/marketplace.json` | yes |
| `canonical-marketplace.schema.json` | `marketplace/marketplace.source.json` | yes |

Path rules are enforced in-schema: relative, forward-slash, no `..` segment, no drive
letter, no UNC, no `~`, no `$`/`%` interpolation.

**State schemas** (`config`, `plan`, `evidence`, `result`, `proposal`) are retained
because PRD M1 deliverable #4 explicitly requires them, but moved to
`core/schemas/state/` with a README stating they are **never** evidence for plugin or
marketplace validation. E3 and E4 rest solely on `codex-plugin.schema.json` and
`openai-marketplace.schema.json`.

---

## 8. Negative-scenario coverage

27 scenarios. Every one asserts one primary **stable diagnostic code**, never prose, so
an upstream rewording cannot silently weaken the suite.

| ID | Scenario | Validator | Expected code | Actual | Test | Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| NS-01 | missing plugin name | claude-plugin schema | `PLUGIN_NAME_MISSING` | same | `test_schema_scenario[NS-01…]` | pass |
| NS-02 | invalid kebab-case name | claude-plugin schema | `PLUGIN_NAME_NOT_KEBAB` | same | `[NS-02…]` | pass |
| NS-03 | malformed semantic version | claude-plugin schema | `VERSION_NOT_SEMVER` | same | `[NS-03…]` | pass |
| NS-04 | version mismatch | `validate_manifests` | `VERSION_MISMATCH` | same | `test_ns04_version_mismatch` | pass |
| NS-05 | missing Codex skills path | codex-plugin schema | `CODEX_SKILLS_MISSING` | same | `[NS-05…]` | pass |
| NS-06 | skills path as array | codex-plugin schema | `CODEX_SKILLS_NOT_STRING` | same | `[NS-06…]` | pass |
| NS-07 | absolute skills path | codex-plugin schema | `PATH_ABSOLUTE` | same | `[NS-07…]` | pass |
| NS-08 | parent-traversal skills path | codex-plugin schema | `PATH_PARENT_TRAVERSAL` | same | `[NS-08…]` | pass |
| NS-09 | empty marketplace plugin list | claude-marketplace schema | `MARKETPLACE_EMPTY` | same | `[NS-09…]` | pass |
| NS-10 | invalid Claude source path | claude-marketplace schema | `CLAUDE_SOURCE_INVALID` | same | `[NS-10…]` | pass |
| NS-11 | invalid OpenAI local source path | openai-marketplace schema | `OPENAI_SOURCE_INVALID` | same | `[NS-11…]` | pass |
| NS-12 | missing OpenAI install policy | openai-marketplace schema | `OPENAI_POLICY_MISSING` | same | `[NS-12…]` | pass |
| NS-12b | policy present, `install` absent | openai-marketplace schema | `OPENAI_POLICY_INSTALL_MISSING` | same | `[NS-12b…]` | pass |
| NS-13 | invalid OpenAI auth policy | openai-marketplace schema | `OPENAI_POLICY_AUTH_INVALID` | same | `[NS-13…]` | pass |
| NS-14 | generated catalog drift | `generate_marketplaces` | `CATALOG_DRIFT` | same | `test_ns14_generated_catalog_drift` | pass |
| NS-15 | canonical missing semantic field | canonical schema | `CANONICAL_FIELD_MISSING` | same | `[NS-15…]` | pass |
| NS-16 | Skill missing description | `validate_skills` | `SKILL_DESCRIPTION_MISSING` | same | `test_ns16_…` | pass |
| NS-17 | unsupported canonical frontmatter | `validate_skills` | `SKILL_FRONTMATTER_UNSUPPORTED` | same | `test_ns17_…` | pass |
| NS-18 | `openai.yaml` enables implicit invocation | `validate_skills` | `POLICY_IMPLICIT_INVOCATION_ENABLED` | same | `test_ns18_…` | pass |
| NS-19 | symbolic-link escape | `check_path_containment` | `SYMLINK_ESCAPE` | — | `test_ns19_symlink_escape` | **skipped on Windows** (symlink creation needs elevation; check is platform-neutral and runs on CI Linux/macOS) |
| NS-20 | production Skill name in installable root | `validate_skills` | `PRODUCTION_SKILL_IN_ROOT` | same | `test_ns20_…` | pass |
| NS-21 | production hook in installable root | `validate_skills` | `PRODUCTION_HOOK_IN_ROOT` | same | `test_ns21_…` | pass |
| NS-22 | affirmative undocumented install example | `check_no_install_command` | `UNDOCUMENTED_INSTALL_COMMAND` | same | `test_ns22_…` | pass |
| NS-22b | negated mention is permitted | `check_no_install_command` | *(none — must pass)* | none | `test_ns22b_…` | pass |
| NS-23 | Windows drive-qualified path | codex-plugin schema | `PATH_DRIVE_QUALIFIED` | same | `[NS-23…]` | pass |
| NS-24 | UNC path | codex-plugin schema | `PATH_UNC` | same | `[NS-24…]` | pass |
| NS-25 | tilde expansion | codex-plugin schema | `PATH_TILDE` | same | `[NS-25…]` | pass |
| NS-26 | environment-variable interpolation | codex-plugin schema | `PATH_ENV_INTERPOLATION` | same | `[NS-26…]` | pass |
| NS-27 | repository path containing spaces | `validate_manifests` | *(none — must pass)* | none | `test_ns27_…` | pass |

**Scenarios: 27. Passed: 26. Skipped: 1 (NS-19, platform). Failed: 0. Missing: 0.**

Plus four tests proving malformed input fails through the authoritative library rather
than a subset guess: malformed YAML raises `yaml.YAMLError`; YAML the old parser
rejected (flow sequences, anchors) now parses correctly; an invalid schema raises
`jsonschema.SchemaError`; a schema without `$id` is rejected.

---

## 9. What remains unresolved

| Item | Status | Why |
| :--- | :--- | :--- |
| E5 dual-host plugin root | **Blocked** | Claude half verified; no Codex CLI on this machine |
| E6 Skill discovery on both hosts | **Manual Required** | `plugin validate` checks manifests, not discovery |
| E12 marketplace candidate selection | **Blocked** | Codex CLI and ChatGPT desktop surfaces untested |
| E13 hook-root vs Skill-script experiments | **Manual Required** | Separation implemented; neither experiment executed |
| DEC-P13 | **Proposed** | One host is not two |
| DEC-P14 | **Proposed** | Candidate C adopted provisionally as implementation strategy only |

---

## 10. Final verification

| Assertion | Result |
| :--- | :--- |
| `docs/PRD.md` hash unchanged | **verified** — identical before and after |
| Git repository exists, branch `main` | verified |
| No commit exists | verified — `git rev-list --all --count` = 0 |
| No remote exists | verified |
| No push occurred | verified — no remote to push to |
| No user-level Claude or Codex setting changed | verified — only read-only `claude plugin validate` was run |
| No plugin installed, no marketplace registered | verified |
| No release workflow remains | verified — only `validate.yml`, `test.yml` |
| No production Skill exists | verified — all seven names absent from the installable root |
| Exactly one fixture Skill in the installable root | verified — `m1-discovery-fixture` |
| Authoritative YAML parser is PyYAML | verified — `parse_yaml_subset` gone |
| Authoritative schema validator is jsonschema | verified — `validate_instance` gone |
| pytest is the authoritative test runner | verified — 46 passed, 1 skipped |
| All five packaging schemas exist | verified |
| Generated catalogs are deterministic | verified — two runs byte-identical |
| Manual tests not reported as Passed without execution | verified — E5, E6, E12, E13 are not Passed |
| Exit-criterion arithmetic correct | verified — computed by `scripts/m1_status.py`, sums to 17 |
| DEC-P13 Proposed | verified — only the Claude half has evidence |
| DEC-P14 Proposed | verified — Candidate C is implementation-provisional only |

**Final counts: 13 Passed, 0 Failed, 2 Blocked, 0 Not Available, 2 Manual Required = 17.**

**Phase: M1 scaffold complete, host verification pending.**


---

# M1.2 addendum — real-host verification

_2026-08-08._ Full record: [`m1-experiments.md`](m1-experiments.md).
Defect: [`m1-defects.md`](m1-defects.md). Manual work: [`m1-runbook.md`](m1-runbook.md).

## What M1.2 changed about M1.1's conclusions

| M1.1 said | M1.2 found |
| :--- | :--- |
| Codex CLI Not Available | **Available** — `codex-cli 0.146.0-alpha.9.2`, bundled in ChatGPT Desktop, not on PATH |
| Q-IMPL-011 open (can CLI install?) | **Resolved: yes** — `codex plugin add` |
| E4 Passed (Codex catalog validated) | **Failed** — the real host rejects the generated catalog (DEF-001) |
| E12 Blocked | **Failed** — Candidate C tested on Codex and rejected |
| DEC-P13 Codex half unavailable | Codex half **Passed** — installed from a dual-manifest root |

## The central lesson

M1.1 marked E4 Passed because a schema written in M1.1 accepted a value invented in
M1.1. That is circular, and the circularity was invisible until a real host was asked.
The M1.2 instruction not to reinterpret deterministic schema success as host-runtime
success was not a formality — it named the exact defect present in the repository.

## Exit-criteria movement

| | M1.1 | M1.2 |
| :--- | ---: | ---: |
| Passed | 13 | **12** |
| Failed | 0 | **2** |
| Blocked | 2 | 1 |
| Manual Required | 2 | 2 |

The count went **down**, which is the correct direction when real evidence contradicts
assumed evidence.


---

# M1.3 addendum - OpenAI marketplace contract remediation

_2026-08-08._ Full detail: [`m1-defects.md`](m1-defects.md).

## What was wrong

M1.1 invented an OpenAI marketplace `policy` block: `install: "manual"` and
`authentication: "none"`. Neither value came from documentation or a host probe. The
local schema then validated our own invention, and E4 was recorded Passed on that basis.
M1.2 asked a real host, which rejected it.

## What changed

| Artifact | Change |
| :--- | :--- |
| `marketplace/marketplace.source.json` | host-shaped `policy` block replaced with named semantic concepts `installation_availability`, `authentication_timing`; `category` now `Productivity` |
| `scripts/generate_marketplaces.py` | maps concepts to host-native fields; emits the documented object `source` for OpenAI; emits **no** policy fields into the Claude catalog; reads every concept with `[...]` so a missing one fails loudly instead of defaulting |
| `.agents/plugins/marketplace.json` | regenerated: `installation: AVAILABLE`, `authentication: ON_INSTALL`, `category: Productivity`, object `source` |
| `.claude-plugin/marketplace.json` | regenerated: `category: Productivity`; no policy fields |
| `openai-marketplace.schema.json` | rewritten; every enum carries its evidence level; `additionalProperties: false` on `policy` |
| `canonical-marketplace.schema.json` | host-shaped block replaced with semantic concepts |
| `claude-marketplace.schema.json` | kebab-case patterns removed from `name`, `plugins[].name` and `category` — **partly wrong, corrected in M1.3.1**: only `category` was an invention |
| `scripts/_diagnostics.py` | new codes, incl. `OPENAI_POLICY_UNKNOWN_FIELD` for the invented-field case |
| `scripts/validate_marketplaces.py` | resolves both the Claude string and OpenAI object `source` shapes; an unrecognised shape now fails instead of being silently skipped |

## Three findings beyond the reported defect

1. **`policy.install` was never validated by the host at all** - a deliberately bogus
   value was accepted. Host acceptance of an unknown field is not evidence of validity.
2. **`source` accepts an object**, and M1.2 shipped a bare string. Both work on the tested
   host. The object form was adopted. *(Recorded in M1.3 as "the string form is
   undocumented" — **that was wrong**, see the M1.3.1 addendum below.)*
3. **Two more constraints were removed** while auditing: kebab-case patterns on `name` and
   `category` in the marketplace schemas. *(Only `category` was an invention. Removing it
   from `name` was a **regression**, corrected in M1.3.1.)*

## Exit-criteria movement

| | M1.1 | M1.2 | M1.3 |
| :--- | ---: | ---: | ---: |
| Passed | 13 | 12 | **13** |
| Failed | 0 | 2 | **0** |
| Blocked | 2 | 1 | 2 |
| Manual Required | 2 | 2 | 2 |

E4 returned to Passed - but on host-revalidated evidence this time, not on a schema
validating its own invention. E12 moved from Failed to Blocked: Candidate C now passes
two host surfaces, and what remains missing is Desktop coverage rather than a defect.

---

# M1.3.1 addendum - contract-evidence correction

_2026-08-08._ Deterministic work only. **No host command was run in this pass.** The M1.3
host evidence is retained, not re-collected.

M1.3 recorded two claims the current vendor documentation does not support. Both were
re-checked against the published pages and corrected.

## Correction 1 - the plain string `source` is documented

OpenAI documents two local-entry representations: the object
`{"source": "local", "path": "./plugins/my-plugin"}` and a plain string path
`"./plugins/my-plugin"`. M1.3 called the string form undocumented, modelled `source` as
object-only, and shipped NS-42 asserting that a string is invalid.

| Consequence | Correction |
| :--- | :--- |
| schema rejected a documented form | `oneOf` over both forms, path hygiene enforced identically on each |
| NS-42 asserted the wrong contract | withdrawn; replaced by NS-46…NS-54, which reject shapes matching **neither** documented form |
| object form justified as "the documented one" | justified as a local architecture choice (Local-M1-Policy) |
| string form associated with DEF-001 | association removed - it was never part of the defect |

Candidate C still emits the object form. That was **not** reverted: the decision is sound,
only its stated reason was wrong.

## Correction 2 - kebab-case on identifiers is documented

While auditing invented constraints, M1.3 also deleted real ones.

| Field | M1.3 action | Truth | M1.3.1 |
| :--- | :--- | :--- | :--- |
| Claude marketplace `name` | removed as invented | Official-Documented: "kebab-case, no spaces" | **restored** |
| Claude marketplace `plugins[].name` | removed as invented | Official-Documented: "kebab-case, no spaces" | **restored** |
| OpenAI marketplace `plugins[].name` | absent | Official-Documented stable identifier | **added** |
| Claude / Codex plugin manifest `name` | retained | Official-Documented | annotated |
| `category` | removed as invented | correct - a free-form label | stays removed |

For one milestone the schemas accepted `"Agent Harness"` as an identifier, a value the
Claude validator rejects outright. No shipped artifact used such a name, so nothing was
published wrong - the schemas simply stopped catching the error class.

## Correction 3 - `ON_USE` evidence normalized

| Claim | Label |
| :--- | :--- |
| `ON_INSTALL` literal | Official-Documented |
| authentication on install vs. first use (behaviour) | Official-Documented semantics |
| `ON_USE` literal spelling | **Host-Observed**, codex-cli 0.146.0-alpha.9.2 only |

`ON_USE` remains valid in the compatibility schema so a host-observed variant validates,
annotated as version-scoped. The generator never selects it; a test asserts Candidate C
emits `ON_INSTALL`.

## Changed artifacts

| Artifact | Change |
| :--- | :--- |
| `openai-marketplace.schema.json` | `source` accepts both documented forms; kebab restored on `plugins[].name`; `ON_USE` re-annotated |
| `claude-marketplace.schema.json` | kebab **restored** on `name` and `plugins[].name`; `category` stays free-form |
| `claude-plugin.schema.json`, `codex-plugin.schema.json` | kebab confirmed, evidence annotated |
| `canonical-marketplace.schema.json` | identifier patterns aligned; `category` free-form |
| `scripts/_diagnostics.py` | 4 new codes so each source-shape mistake keeps a distinct diagnosis under `oneOf` |
| `scripts/validate_marketplaces.py` | comment corrected: both OpenAI forms resolve |
| `scripts/generate_marketplaces.py` | comment corrected: object form is a local choice |
| `tests/` | NS-42 withdrawn; NS-46…NS-64 added; 5 positive contract tests added |
| `scripts/m1_status.py` | E4 evidence text corrected |

**No catalog regeneration was required** - the generator's output is unchanged, and both
catalogs remain byte-identical to a fresh render.

## Exit-criteria movement

| | M1.1 | M1.2 | M1.3 | M1.3.1 |
| :--- | ---: | ---: | ---: | ---: |
| Passed | 13 | 12 | 13 | **13** |
| Failed | 0 | 2 | 0 | **0** |
| Blocked | 2 | 1 | 2 | **2** |
| Manual Required | 2 | 2 | 2 | **2** |

Unchanged, deliberately. A schema correction is not host-runtime evidence, so E5, E6, E12
and E13 do not move. **M2 has not begun.**


---

# M1.4A addendum - Claude non-interactive host verification

_2026-08-08._ Claude Code **2.1.195**. No model invoked, no prompt, no interactive
session, no installation, no marketplace registration, no settings written.

## Evidence-label correction

One overstatement remained after M1.3.1.

| | Before (M1.3.1) | After (M1.4A) |
| :--- | :--- | :--- |
| Codex plugin manifest `name` | Official-Documented kebab-case identifier | unchanged - still **Official-Documented** |
| OpenAI marketplace `plugins[].name` | Official-Documented kebab-case **marketplace-field** rule | **Local-M1-Policy derived** from the manifest-identity contract |
| rule actually enforced | "must be kebab-case" | "must equal the plugin manifest identity" - kebab-case follows |

The marketplace page's examples reuse the same plugin identity; they do not independently
publish a case rule for a catalog entry name. The distinction matters because it changes
what a future contributor may rely on, not what the validator does.

**Nothing was weakened.** The kebab pattern stays, the parity rule stays, and a non-kebab
plugin identity is still not treated as vendor-valid. A gap was closed instead: identity
parity held in fact but no test asserted it, so the derivation the corrected label depends
on was unenforced. `test_plugin_identity_is_the_same_string_everywhere` now checks all
five files. Generated catalogs are byte-identical; only `$comment` text changed.

## Host results

| Experiment | Result |
| :--- | :--- |
| `--plugin-dir … plugin list --json` | **Passed** - `agent-harness@inline`, `scope: session`, enabled, v0.0.1, loaded from the root containing `.codex-plugin/` |
| `--plugin-dir … plugin details agent-harness@inline` | **Passed** - Skills (1) `m1-discovery-fixture`; Agents/Hooks/MCP/LSP all 0; no production Skill present |
| both experiments from a path containing spaces | **Passed** - no quoting error, no escape, disposable copy deleted |
| bare `claude plugin list` (control) | our plugin **absent** - confirming no installed record |
| plugin-cache tree and `~/.claude/settings.json` | **byte-identical** before and after |

## Exit-criteria movement

| | M1.3 | M1.3.1 | M1.4A |
| :--- | ---: | ---: | ---: |
| Passed | 13 | 13 | **14** |
| Failed | 0 | 0 | **0** |
| Blocked | 2 | 2 | **1** |
| Manual Required | 2 | 2 | **2** |

**E5 Blocked -> Passed.** Both hosts now load the same co-located root at runtime, for the
tested host versions.

**E6 stays Manual Required.** The Claude half passed; the Codex half has no evidence, and
cache-file presence is not discovery. Half of a two-host criterion is not the criterion.

**E12 and E13 unchanged** - this phase ran no ChatGPT Desktop, hook-root, or helper-script
experiment.

**DEC-P13 stays Proposed.** See [`m1-decisions.md`](m1-decisions.md): the PRD conditions
promotion on all seven ATS-018 checks *and* a PRD revision, and this phase may do neither.

**M1.4B not begun. M2 not begun.**
