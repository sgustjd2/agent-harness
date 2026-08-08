# M1 host experiments

Record of host verification. **Recording an outcome is the requirement; a positive
outcome is not.** Nothing is reported as passing without execution.

Last updated: 2026-08-08 (M1.4A).

---

## Environment

| | |
| :--- | :--- |
| OS | Windows 10 (AMD64), **native Windows outside WSL** |
| WSL | Ubuntu installed but the WSL service is unavailable (`HCS_E_SERVICE_NOT_AVAILABLE`). Not started or repaired — out of scope |
| Python | 3.11.9 (venv) |
| Git | 2.40.1.windows.1 |
| Shell | Git Bash |
| Claude Code | **2.1.195** |
| Codex CLI | **codex-cli 0.146.0-alpha.9.2** — bundled with ChatGPT Desktop, not on PATH |
| ChatGPT Desktop | installed (Codex runtime present); GUI not automated |
| Symlink creation | not permitted without elevation |
| Disposable profile | available (isolated `CODEX_HOME` outside TEMP) |

**M1.1 recorded Codex CLI as "Not Available" because `command -v codex` failed. That was
incomplete.** The CLI ships inside ChatGPT Desktop and is fully functional when invoked
by absolute path. This correction unblocked the Codex experiments below.

---

## Evidence-label discipline

These are tracked as distinct facts and never merged:

| Concept | Status this pass |
| :--- | :--- |
| schema validation | Passed (local schemas) |
| vendor validator validation | Claude: **Passed**. Codex: no validator exists |
| marketplace registration | Codex: **Passed** (isolated) |
| plugin installation | Codex: **Passed** (isolated). Claude: Not Run |
| plugin loading | Claude: **Passed (M1.4A, session-scoped)**. Codex: indirect only |
| Skill discovery | Claude: **Passed (M1.4A, component inventory)**. Codex: **Not Run** |
| Skill invocation | **Not Run** on both hosts |
| helper-script execution | **Not Run** on both hosts |

---

## Documented path asymmetry (Step 3)

**Claude Code — documented capability:**

- `CLAUDE_PLUGIN_ROOT` is documented for substitution in plugin Skill content
- `CLAUDE_PLUGIN_ROOT` is documented for substitution in plugin agent content
- `CLAUDE_PLUGIN_ROOT` is documented for hook and monitor commands
- plugin `bin/` executables can be added to the Bash tool PATH
- **this is documented capability, not fixture runtime evidence**

**Codex — documented capability:**

- `PLUGIN_ROOT` and `PLUGIN_DATA` are documented for plugin hook commands
- `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` are supplied to Codex plugin hooks for compatibility
- these are **not** documented as universally available to commands initiated from arbitrary Skill bodies
- **hook-root evidence must not be reused as Skill-script evidence**

| Question | Status |
| :--- | :--- |
| Claude plugin Skill path | **Documented capability — runtime test pending** |
| Codex plugin hook path | **Documented capability — runtime test pending** |
| Codex plugin Skill path | **Open — runtime test required** |

---

## Claude results

| Experiment | Result | Evidence |
| :--- | :--- | :--- |
| `claude --version` | 2.1.195 | — |
| `claude plugin validate . --strict` | **Passed** | exit 0, `Validation passed`. Target was the Candidate C **generated** catalog |
| `claude plugin validate ./plugins/agent-harness --strict` | **Passed** | exit 0, `Validation passed`, with `.codex-plugin/` present in the root |
| Plugin runtime load (`claude --plugin-dir … plugin list --json`) | **Passed (M1.4A)** | `agent-harness@inline`, `scope: session`, enabled, loaded from the root containing `.codex-plugin/`. No installed record created |
| Skill discovery (`plugin details`) | **Passed (M1.4A)** | component inventory: Skills (1) `m1-discovery-fixture`; Agents/Hooks/MCP/LSP all 0 |
| Load + discovery from a path with spaces | **Passed (M1.4A)** | byte-identical disposable copy; no quoting error; deleted afterwards |
| Fixture invocation `/agent-harness:m1-discovery-fixture` | **Not Run** | would invoke a paid model; manual runbook prepared |
| `${CLAUDE_PLUGIN_ROOT}` runtime experiment | **Documented, Runtime Not Run** | static string inspection is not runtime success |

Claude strict validation proves **validator tolerance** of a dual-manifest root. It does
not prove loading, discovery, or invocation. M1.4A added the first two of those three
directly; **invocation remains Not Run.**

---

## Codex CLI results

All state landed in an isolated `CODEX_HOME`. Isolation of material state was proven
before any write.

| Experiment | Result | Evidence |
| :--- | :--- | :--- |
| CLI availability | **Available** | `codex-cli 0.146.0-alpha.9.2` |
| Official validate subcommand | **Not Available** | `codex plugin --help` lists `add`, `list`, `marketplace`, `remove` only. None invented |
| Marketplace registration | **Passed** | `codex plugin marketplace add <disposable>` → `Added marketplace` |
| Marketplace listing | **Passed** | `codex plugin marketplace list` → root resolved to the disposable copy |
| Catalog → plugin recognition | **Passed** | `codex plugin list` → `agent-harness@agent-harness`, status **not installed** |
| **Registration ≠ installation** | **Empirically confirmed** | status was `not installed` immediately after registration |
| Plugin installation (CLI only) | **Passed on codex-cli 0.146.0-alpha.9.2 — PROTOCOL-DEVIATING (PROC-001)** | install-class subcommand → `installed, enabled`, v0.0.1, isolated. M1.2 forbade automatic installation; evidence retained but not a universal guarantee and NOT the M1.3 revalidation |
| Dual-manifest tolerance | **Passed** | installed from a root containing `.claude-plugin/` **and** `.codex-plugin/`; no error |
| Install cache preservation | **Passed** | cache retained both manifests, `skills/`, and `skills/m1-discovery-fixture/agents/openai.yaml` |
| Skill discovery | **Not Run** | no `skill` subcommand; `codex exec` would invoke a paid model |
| Fixture invocation `$m1-discovery-fixture` | **Not Run** | manual runbook prepared |
| Implicit-invocation blocking | **Not Run** | cannot be inferred from the YAML alone |

### Q-IMPL-011 — normalized in M1.3

**Host-verified on codex-cli 0.146.0-alpha.9.2; cross-version and stable-documentation
status remains Open.**

| Claim | Status |
| :--- | :--- |
| the install-class subcommand appeared in actual help output | **Host-Observed**, version 0.146.0-alpha.9.2 |
| CLI installation succeeded on that alpha version | **Host-Observed**, isolated — **PROC-001 protocol deviation** |
| current public documentation defines it as the stable general installation path | **No** |

The published packaging documentation covers `marketplace add / list / upgrade / remove`
and ChatGPT Desktop installation. It does not establish the install-class subcommand as a
stable cross-version contract, so this repository does not describe it as universally
supported. The M1.2 evidence is retained, not discarded.

**M1.3 did not run any install-class command.**

---

## DEF-001 — host-exposed defect

`codex plugin marketplace add` **rejected** the generated OpenAI catalog:
`unknown variant 'none', expected 'ON_INSTALL' or 'ON_USE'` at `policy.authentication`.

Full analysis, controlled diagnosis and remediation: [`m1-defects.md`](m1-defects.md).

Per the M1.2 rule the defect was recorded, the affected experiment stopped, nothing was
patched, and E4 was marked Failed.

**M1.3 closed it.** The invented `policy.install` was removed with no alias, the invalid
`authentication: "none"` was replaced with the documented contract, and the corrected
catalog was re-registered successfully on the same host — registration only, no install.
**E4 is Passed again, now on host-revalidated evidence rather than on a schema that
validated our own invention.**

---

## Isolation report

| | |
| :--- | :--- |
| Mechanism | `CODEX_HOME` redirected to a disposable directory outside TEMP |
| Proof | the CLI's own warning named the isolated path; `marketplace list` showed only our disposable marketplace |
| **Isolated** | marketplace registration, plugin installation, plugin cache, `config.toml` |
| **NOT isolated** | `~/.codex/logs_2.sqlite-wal`, `~/.codex/models_cache.json`, and 3 `~/.codex/tmp/arg0/...` helper files, written on **every** invocation regardless of `CODEX_HOME` |
| Real config verified clean | `~/.codex/config.toml` contains only pre-existing `openai-bundled` and `openai-primary-runtime`. **No agent-harness entry** |
| Real plugin cache verified clean | contains only `openai-*` entries |
| Cleanup | isolated home and disposable copy deleted |

**Disclosure:** complete isolation was not achievable. Logs, model cache, and temp helper
files are written to the real `~/.codex` on any invocation, including the first
`--version` probe. No configuration, marketplace, or plugin state leaked.

---

## Hook-root experiment (ATS-028)

| Part | Result |
| :--- | :--- |
| Static fixture validation | **Passed** (M1.1) |
| Runtime | **Manual Required** — firing a hook needs a session that invokes a paid model |

Fixture: `tests/fixtures/host-tests/codex-hook-root/`. Not copied into the plugin.
`PLUGIN_ROOT` / `PLUGIN_DATA` were **not** simulated — simulation is not host verification.

---

## Skill-script experiment (ATS-020)

| Host | Result |
| :--- | :--- |
| Claude | **Documented, Runtime Not Run** |
| Codex | **Open — runtime test required** |

Fixture: `tests/fixtures/host-tests/skill-script-path/`, outside the installable root.
**Q-IMPL-003 remains open.** No workaround was invented.

---

## ChatGPT Desktop

Not automated, by instruction. Manual runbook: [`m1-runbook.md`](m1-runbook.md).

| Experiment | Result |
| :--- | :--- |
| Marketplace recognition | **Not Run** |
| Plugin installation | **Not Run** |
| Fixture discovery | **Not Run** |
| Fixture invocation | **Not Run** |

---

## Not performed, deliberately

| Action | Why |
| :--- | :--- |
| Register a marketplace in the real user config | forbidden; isolated copy used instead |
| Install a plugin into the real user cache | forbidden; isolated copy used instead |
| Start an interactive or `exec` Codex/Claude session | would invoke a paid model |
| Install or repair WSL, Codex, or any package | forbidden |
| Patch DEF-001 | forbidden; recorded and scoped to M1.3 |


---

## M1.3 — DEF-001 remediation and revalidation

### What changed

The invented `policy.install` field and the invalid `authentication: "none"` value were
removed. The corrected contract uses only documented values, and the canonical source now
carries named semantic concepts (`installation_availability`, `authentication_timing`)
that the generator maps to host-native fields.

### Codex revalidation — registration only

| Step | Result |
| :--- | :--- |
| Host | codex-cli 0.146.0-alpha.9.2 |
| Isolation | `CODEX_HOME` redirected; disposable repository copy |
| `codex plugin marketplace add <disposable>` | **Passed** — `Added marketplace` |
| `codex plugin marketplace list` | **Passed** — marketplace root resolved |
| `codex plugin list` | plugin source resolved, status **`not installed`** |
| Plugin installation | **NOT performed** — no install-class command executed |
| Real material config after | **no** `agent-harness` marketplace, **no** `agent-harness` plugin |
| Isolated plugin cache | **empty** — confirming no installation occurred |
| Cleanup | isolated home and disposable copy removed |

**Disclosure (ENV-001):** Codex may still update real runtime logs and cache metadata
despite `CODEX_HOME`. That is host bookkeeping, not configuration mutation.

### Claude revalidation

| Command | Result |
| :--- | :--- |
| `claude plugin validate . --strict` | **Passed**, exit 0 |
| `claude plugin validate ./plugins/agent-harness --strict` | **Passed**, exit 0, `.codex-plugin/` present |

**Validator evidence only.** Not plugin runtime loading, not Skill discovery, not Skill
invocation. Those remain Not Run.

### Source shape finding — reclassified in M1.3.1

An isolated probe showed the host accepts **both** the object form and a plain string path
for a local entry, and resolves them identically. M1.3 recorded this as "the documented
object form versus an undocumented string", and adopted the object accordingly.

**That classification was wrong.** The current OpenAI documentation states that for local
entries `source` may also be a plain string path. Both forms are Official-Documented, the
host accepts both, and the plain string artifact M1.2 shipped was never malformed. The
object form is still what Candidate C emits — but as a local architecture choice, not
because the alternative was invalid.

---

## M1.3.1 — contract-evidence correction (no new host runs)

_2026-08-08._ Deterministic revalidation only. **No Codex probe and no Claude session was
run in this pass**; the M1.3 host evidence above is retained unchanged.

| Correction | Before (M1.3) | After (M1.3.1) |
| :--- | :--- | :--- |
| plain string `source` | recorded as undocumented; schema rejected it | Official-Documented; schema accepts both forms |
| object `source` | justified as "the documented shape" | justified as a local generation choice |
| Claude marketplace `name` / `plugins[].name` kebab-case | removed as invented | **restored** — documented by the vendor |
| `category` kebab-case | removed as invented | stays removed — correctly identified |
| `ON_USE` literal | labelled Official-Documented (prose) | **Host-Observed**, version-scoped to 0.146.0-alpha.9.2 |

**Regression window.** Between M1.3 and M1.3.1 the local schemas accepted `"Agent
Harness"` as a marketplace and plugin identifier — a value the Claude validator rejects
with a kebab-case error. No artifact in the repository used such a name, so nothing
shipped wrong; the schemas simply stopped catching it. Verified as load-bearing after
restoration: with the pattern absent that value validates clean, with it present it fails
as `PLUGIN_NAME_NOT_KEBAB`.

| Criterion | Effect of this pass |
| :--- | :--- |
| E4 | remains **Passed** — on retained M1.3 host evidence, not re-run here |
| E5, E6, E12, E13 | **unchanged** — a schema correction is not host-runtime evidence |

**M2 has not begun.**


---

## M1.4A — Claude non-interactive load and component discovery

_2026-08-08._ No model invoked, no prompt sent, no interactive session, no installation,
no marketplace registration. Claude Code **2.1.195**.

### Command contract verified before use

The documented forms were confirmed against the installed binary's own help, not assumed:

| Form | Supported on 2.1.195 |
| :--- | :--- |
| `--plugin-dir <path>` global option | yes |
| `plugin list --json` | yes |
| `plugin details <name>` | yes |

The documentation is explicit that a session-scoped plugin appears in `claude plugin
list` **only when the flag precedes the subcommand**, and that such plugins have no
installed record. Both halves of that statement were tested.

### Result 1 — session-scoped runtime load (ATS-018-1 runtime half)

`claude --plugin-dir ./plugins/agent-harness plugin list --json` → **exit 0**.

| Field | Value |
| :--- | :--- |
| identifier | `agent-harness@inline` |
| version | `0.0.1` |
| scope | `session` |
| enabled | `true` |
| load path | the repository plugin root, **with `.codex-plugin/` present** |

**Status: Passed.** This is runtime loading by the real host, distinct from the strict
validator result recorded earlier.

### Result 2 — component inventory (ATS-018-3)

`claude --plugin-dir ./plugins/agent-harness plugin details agent-harness@inline` →
**exit 0**.

| Component group | Count | Contents |
| :--- | ---: | :--- |
| Skills | **1** | `m1-discovery-fixture` |
| Agents | 0 | — |
| Hooks | 0 | — |
| MCP servers | 0 | — |
| LSP servers | 0 | — |

None of the seven production Skill names (`init-project`, `plan-work`, `orchestrate`,
`verify-work`, `refine-harness`, `apply-refinement`, `doctor`) appear. The plugin-root
boundary rule is now confirmed by the host's own inventory, not only by our validator.

**Status: Passed — as discovery.** The Skill was **not** invoked. The marker
`AGENT_HARNESS_M1_DISCOVERY_OK` was neither expected nor produced, because this phase
runs no model.

### Result 3 — path containing spaces

A byte-identical disposable copy (tree digest verified equal to the source) was placed
under `<temporary path with spaces>` and both experiments were repeated.

| Check | Result |
| :--- | :--- |
| plugin loads from a spaced path | **Passed** — same identifier, `scope: session` |
| Skill discovery from a spaced path | **Passed** — Skills (1) `m1-discovery-fixture` |
| quoting error | none |
| path escaped the disposable root | no |
| persistent installation | none |
| disposable copy deleted afterwards | yes |

### Non-mutation evidence

| Check | Before | After |
| :--- | :--- | :--- |
| Claude plugin-cache tree (entry count + digest) | 1805 / `70da4cd1…` | 1805 / `70da4cd1…` |
| `~/.claude/settings.json` | 691 B, `ca37a8e6…` | 691 B, `ca37a8e6…` |
| `~/.claude/settings.local.json` | absent | absent |
| project `.claude/` | absent | absent |
| `agent-harness` in plugin cache | no | no |
| bare `claude plugin list` (no flag) | 3 entries, ours absent | 3 entries, ours absent |

Settings **contents** were never read — only size, hash and presence.

### Evidence separation

These are recorded as five different facts and are not merged:

| Fact | Status |
| :--- | :--- |
| Claude strict validator | Passed (earlier phases) |
| Claude session-scoped runtime load | **Passed (M1.4A)** |
| Claude component discovery | **Passed (M1.4A)** |
| Claude Skill invocation | **Not Run** |
| Claude helper-script execution / `CLAUDE_PLUGIN_ROOT` runtime | **Not Run** |

There is no such status as "Claude host Passed".

### ATS-018 scoreboard after M1.4A

| Check | Status |
| :--- | :--- |
| 018-1 Claude accepts a root containing `.codex-plugin` | **Passed** (validator + runtime load) |
| 018-2 Codex accepts a root containing `.claude-plugin` | **Passed** — version-scoped, PROC-001 |
| 018-3 Claude discovers the shared `skills/` | **Passed (M1.4A)** |
| 018-4 Codex discovers the same `skills/` | **Not Run** |
| 018-5 neither host parses the other's manifest | **Not Run** |
| 018-6 cache copy preserves both manifests | Codex half only |
| 018-7 runtime paths stay inside the plugin root | static only; runtime **Not Run** |

**M1.4B not begun. M2 not begun.**
