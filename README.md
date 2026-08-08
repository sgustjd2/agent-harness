# agent-harness

A vendor-neutral agent workflow layer for **Claude Code** and **OpenAI Codex**,
distributed from one GitHub repository.

It provides no model and no runtime. It provides a procedure: decompose work into roles,
delegate through the host's own subagents, record plan / evidence / result as files in
your repository, refuse to claim completion until your verification gates pass, and turn
accumulated evidence into reviewable proposals that apply only when you say so.

---

## Status: M2 in progress — five production Skills, host verification still pending

**M2 implementation has begun.** M1 built the repository skeleton and the validation
pipeline, and verified the packaging contract against real hosts. M2 adds the first
production Skill.

**`plan-work` is the first production Skill.** It is **read-only by default**: it
produces plans, and it does not implement them. It writes no source, changes no
configuration, runs no command, and creates a file only when you explicitly ask it to
save a plan.

**`init-project` is the second production Skill.** It initializes portable project state
— `.agent-harness/` with configuration, memory files, and run and proposal directories —
and links it to `CLAUDE.md` or `AGENTS.md`. It is **approval-gated**: it inspects the
repository, shows every path it would write, and applies nothing until you approve that
specific proposal. It **does not execute the verification commands it detects**; it
proposes them and leaves them disabled until you say otherwise.

**`verify-work` is the third production Skill.** It **executes the verification gates
already configured** in `.agent-harness/config.yaml` -- and only those. It **never guesses
a command**, requires **explicit approval of the exact gate set** before running anything,
installs no packages, and edits no source or configuration. Commands are argv arrays with
a required timeout, run sequentially. A command that exists is not a command that passed:
it reports `Passed` only on an observed exit code of 0.

**`doctor` is the fourth production Skill.** It diagnoses **agent-harness itself** --
installation, environment, config and memory integrity -- and reports `ok` / `warn` /
`fail` / `unknown` per check with a suggested fix. **`verify-work` verifies your project
code; `doctor` diagnoses the harness.** In this M2 slice `doctor` is **read-only and
executes no commands at all** -- not even `--version` or a PATH lookup -- and it repairs
nothing.

**`orchestrate` is the fifth production Skill.** It **consumes a ready plan** and
carries it out: walking the dependency graph, delegating independent tasks in parallel
when the host and the plan's write scopes allow it and running sequentially otherwise.
**It delegates only within the plan's boundaries** -- planned commands, planned paths --
and **real source changes may occur**. It never declares the work complete; `verify-work`
owns that. **Automatic run-state persistence remains deferred**: no `evidence.md` or
`result.md` is written in this milestone.

**This is not a stable release.** Remaining M1 host verification is still a release
blocker -- Codex Skill discovery, the ChatGPT Desktop surfaces, and the hook and
helper-script runtime experiments are unfinished. Treat all five Skills as
experimental.

| Milestone | Content | State |
| :--- | :--- | :--- |
| M0 / M0.1 / M0.2 | PRD, corrections, decisions | done — [`docs/PRD.md`](docs/PRD.md) |
| M1 | repository + validation scaffold | done |
| M1.1 | scaffold correction and scope audit | done |
| M1.2 | real-host verification | done |
| M1.3 / M1.3.1 | OpenAI marketplace contract remediation and evidence correction | done |
| M1.4A | Claude non-interactive load and component discovery | done |
| M1.4B | Codex Skill discovery, ChatGPT Desktop, hooks, helper execution | **not started** |
| **M2** | **shared Skill bodies — `plan-work`, `init-project`, `verify-work`, `doctor`, `orchestrate`** | **in progress** |
| M3–M8 | adapters, state, refinement, pilot, release | not started |

**Exit criteria: 14 of 17 met.** The three unmet criteria all need host access that this
phase deliberately did not take — see [`docs/m1-traceability.md`](docs/m1-traceability.md).

The installable plugin root contains the compatibility fixture and five production
Skills: `plan-work`, `init-project`, `verify-work`, `doctor` and `orchestrate`. The other
two -- `refine-harness` and `apply-refinement` -- are **not implemented**, and validation
rejects their names until they are.

---

## Repository layout

```
marketplace/marketplace.source.json   canonical catalog source -- the only hand-edited catalog
.claude-plugin/marketplace.json       GENERATED Claude catalog
.agents/plugins/marketplace.json      GENERATED OpenAI catalog

plugins/agent-harness/                the installable plugin. Self-contained.
  .claude-plugin/plugin.json            Claude manifest
  .codex-plugin/plugin.json             Codex manifest, "skills": "./skills/"
  skills/m1-discovery-fixture/          compatibility fixture, inert by design
  skills/plan-work/                     production Skill, read-only
  skills/init-project/                  production Skill, approval-gated
  skills/verify-work/                   production Skill, bounded execution
  skills/doctor/                        production Skill, read-only diagnostics
  skills/orchestrate/                   production Skill, plan-bounded execution
  core/schemas/                         five packaging schemas
  core/schemas/state/                   state schemas -- NOT packaging evidence
  adapters/{claude,codex}/              host integration + experiment records

scripts/                              development and CI only, never installed
tests/                                pytest suite + host-test fixtures
docs/                                 PRD, M1 records, compatibility
```

Nothing under `plugins/agent-harness/` may reference anything outside it, and that is
enforced rather than intended.

---

## Dependencies

**The plugin runtime has no required third-party dependency, and must keep none.** CI
asserts the plugin root declares no manifest or lockfile.

**Development validation uses established libraries**, because an approximation of a
published standard can disagree with the real host while still reporting success:

| Concern | Library |
| :--- | :--- |
| YAML parsing | **PyYAML** (`yaml.safe_load`) |
| JSON Schema validation | **jsonschema** (draft taken from each schema's `$schema`) |
| Test running | **pytest** |

---

## Running the checks

```bash
python -m venv .venv
```

```bash
.venv/bin/pip install -r requirements-dev.txt
```

```bash
python scripts/validate_all.py
```

`validate_all.py` runs the 12 deterministic validators once each, then pytest. It
orchestrates; it does not replace pytest. Manual host tests are never run by it.

```bash
python -m pytest -q
```

```bash
python scripts/m1_status.py
```

---

## Three things worth knowing

**Registering a marketplace is not installing a plugin.** On the OpenAI side the Codex
CLI registers a *source*; installation happens in the ChatGPT desktop app. Whether the
CLI alone can install is unverified, so nothing here depends on it.

**Claude validation and OpenAI validation are different things.** `claude plugin
validate` is a real host validator and it passes. The Codex artifacts are checked
against *local compatibility schemas*, because no official Codex validator was found.
The two are never conflated.

**Claude loads the co-located plugin root and discovers the fixture Skill.** Verified
non-interactively on Claude Code 2.1.195: `claude --plugin-dir ./plugins/agent-harness
plugin list --json` loads it as a session-scoped plugin with no installed record, and
`plugin details` reports `Skills (1) m1-discovery-fixture` with zero agents, hooks, MCP and
LSP servers. Loading and discovery are recorded as **separate** facts, and **Skill
invocation is still Not Run** — that needs a model.

**Two architecture decisions remain Proposed.** Whether both manifests can share one
plugin root, and which marketplace catalog strategy to adopt. Candidate C is
implemented *provisionally* so catalogs are generated rather than hand-maintained —
that is an implementation choice, not a decision. Co-location now has runtime evidence on
both hosts, but promoting that decision needs all seven ATS-018 checks and a PRD revision,
so it stays Proposed.

**The OpenAI marketplace contract is now evidence-backed.** M1.1 invented
`policy.install` and `authentication: "none"`; a real host rejected them. Both were
removed in M1.3 with no compatibility alias, and the corrected catalog
(`installation: AVAILABLE`, `authentication: ON_INSTALL`, `category: Productivity`) was
revalidated on the host. Local schemas remain *local compatibility schemas*, not official
vendor schemas — and host acceptance of an unknown field never makes that field valid.

**Both OpenAI local `source` shapes are officially supported.** A local marketplace entry
may use the object `{"source": "local", "path": "./plugins/agent-harness"}` **or** a plain
string path `"./plugins/agent-harness"`. The generator emits the object form by choice,
not by requirement; a plain string is not a defect. The local schema accepts both — where
it is deliberately narrower than a vendor contract, it says so in a `$comment`.

**Required plugin identifiers are kebab-case; `category` is not.** Marketplace and plugin
`name` fields are documented kebab-case identifiers on both hosts. `category`,
`displayName`, descriptions and owner names are free-form labels. M1.3 removed the
identifier patterns in error; M1.3.1 restored them.

**M2 has five Skills so far.** `plan-work`, `init-project`, `verify-work`, `doctor` and
`orchestrate` are implemented and validated; `refine-harness` and `apply-refinement` are
not, and their names are still rejected in the installable root. A shipped `SKILL.md` is host-discoverable whatever
its body says, so an empty placeholder would be a product surface with nothing behind
it.

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

Apache-2.0. See [`LICENSE`](LICENSE).
