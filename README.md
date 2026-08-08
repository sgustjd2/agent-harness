# agent-harness

A vendor-neutral agent workflow layer for **Claude Code** and **OpenAI Codex**,
distributed from one GitHub repository.

It provides no model and no runtime. It provides a procedure: decompose work into roles,
delegate through the host's own subagents, record plan / evidence / result as files in
your repository, refuse to claim completion until your verification gates pass, and turn
accumulated evidence into reviewable proposals that apply only when you say so.

---

## Status: M1.4A — scaffold complete, host verification pending

**This repository does nothing useful yet.** M1 built the repository skeleton and the
validation pipeline; M1.1 corrected it; M1.2–M1.3.1 verified and corrected the packaging
contract against real hosts. M1.4A established that Claude Code actually **loads** the
plugin and **discovers** its Skill.

**M2 has not begun.**

| Milestone | Content | State |
| :--- | :--- | :--- |
| M0 / M0.1 / M0.2 | PRD, corrections, decisions | done — [`docs/PRD.md`](docs/PRD.md) |
| M1 | repository + validation scaffold | done |
| M1.1 | scaffold correction and scope audit | done |
| M1.2 | real-host verification | done |
| M1.3 / M1.3.1 | OpenAI marketplace contract remediation and evidence correction | done |
| **M1.4A** | **Claude non-interactive load and component discovery** | **current** |
| M1.4B | Codex Skill discovery, ChatGPT Desktop, hooks, helper execution | **not started** |
| M2 | shared Skill bodies | **not started** |
| M3–M8 | adapters, state, refinement, pilot, release | not started |

**Exit criteria: 14 of 17 met.** The three unmet criteria all need host access that this
phase deliberately did not take — see [`docs/m1-traceability.md`](docs/m1-traceability.md).

There are **no production Skills**. The installable plugin root contains exactly one
compatibility fixture Skill, which does nothing by design.

---

## Repository layout

```
marketplace/marketplace.source.json   canonical catalog source -- the only hand-edited catalog
.claude-plugin/marketplace.json       GENERATED Claude catalog
.agents/plugins/marketplace.json      GENERATED OpenAI catalog

plugins/agent-harness/                the installable plugin. Self-contained.
  .claude-plugin/plugin.json            Claude manifest
  .codex-plugin/plugin.json             Codex manifest, "skills": "./skills/"
  skills/m1-discovery-fixture/          the ONLY Skill here during M1
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

**M2 has not begun.**

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

Apache-2.0. See [`LICENSE`](LICENSE).
