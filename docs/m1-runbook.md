# M1.2 manual host runbook

Experiments that require a human. Every step here is **agent-forbidden**: each one either
invokes a paid model or mutates real host state.

**Most of this runbook is still unexecuted.** Exception: the *non-interactive* half of RB-01 was completed in M1.4A without a session or a model — see the RB-01 note below. Everything else remains `Not Run`.

Do not paste tokens, credentials, whole config files, or full logs into any record.
Capture only the fields each experiment names.

---

## RB-01 — Claude plugin load and Skill discovery

Covers E5 (Claude half) and E6 (Claude half).

> **Partly superseded by M1.4A.** Plugin *loading* and Skill *discovery* no longer need a
> human, a session, or a model. Both were established non-interactively:
>
> ```bash
> claude --plugin-dir ./plugins/agent-harness plugin list --json
> claude --plugin-dir ./plugins/agent-harness plugin details agent-harness@inline
> ```
>
> The first returned `agent-harness@inline` with `scope: session`; the second listed
> `Skills (1) m1-discovery-fixture`. Neither created an installed record. What remains
> manual below is **invocation only** — the marker check — which does require a model.

**Working directory:** the repository root.

**Command:**

```bash
claude --plugin-dir ./plugins/agent-harness
```

**Then, inside the session, invoke explicitly:**

```
/agent-harness:m1-discovery-fixture
```

| Expectation | Value |
| :--- | :--- |
| Plugin namespace | `agent-harness` |
| Fixture Skill | `m1-discovery-fixture` |
| Expected marker | `AGENT_HARNESS_M1_DISCOVERY_OK` |

**Record each of these separately — they are not the same fact:**

| Field | Result |
| :--- | :--- |
| process started | Not Run |
| plugin loaded | Not Run |
| fixture Skill appeared in the Skill list | Not Run |
| fixture Skill explicitly invoked | Not Run |
| marker returned | Not Run |
| no repository file changed | Not Run |
| no user setting changed | Not Run |
| Claude Code version | — |

A debug log showing Skill registration supports *loading* and *discovery*. It does not by
itself prove *invocation*. Record only the relevant sanitized registration lines, never
the full log.

**If the plugin loads but the fixture does not appear:** mark Claude Skill discovery
**Failed**, record the host version, and do not edit the Skill.

**Cleanup:** end the session. `--plugin-dir` is session-scoped and installs nothing.

> **Note on the marker.** The current fixture `SKILL.md` instructs the model to state that
> it is an M1 compatibility fixture with no behaviour; it does not yet emit the literal
> string `AGENT_HARNESS_M1_DISCOVERY_OK`. Adding that string is a production-artifact
> change and was **not** made in M1.2. Either accept a descriptive response as the
> discovery signal, or schedule the marker addition into M1.3.

---

## RB-02 — Claude `${CLAUDE_PLUGIN_ROOT}` runtime experiment

Covers the Claude half of E13.

Use **only** `tests/fixtures/host-tests/skill-script-path/`. Do not modify the production
fixture Skill.

**Requirements:**

- invoke only the harmless bundled fixture helper
- write only to a temporary directory
- report a fixed marker
- no network access
- no repository mutation
- no user-setting mutation
- exercise a repository path containing spaces
- record the resolved path in redacted form only
- verify the helper stayed inside the plugin fixture root

**Classification — choose exactly one:**

- `Documented and Runtime Passed`
- `Documented but Runtime Failed`
- `Documented, Runtime Not Run` ← **current**

Static string inspection is never runtime success.

---

## RB-03 — Codex fixture Skill discovery and invocation

Covers E6 (Codex half) and part of E12.

Requires a Codex or ChatGPT Desktop session, which invokes a paid model.

**Explicit invocation:** `$m1-discovery-fixture`
**Expected marker:** `AGENT_HARNESS_M1_DISCOVERY_OK`

| Field | Result |
| :--- | :--- |
| plugin visible | Not Run |
| plugin installed | Not Run |
| Skill listed or suggested | Not Run |
| **implicit invocation blocked** | Not Run |
| explicit invocation accepted | Not Run |
| expected marker returned | Not Run |
| no repository mutation | Not Run |

**Implicit-invocation test.** `agents/openai.yaml` sets
`policy: allow_implicit_invocation: false`. Give an unrelated prompt (for example, "list
the files in this directory") and confirm the fixture is **not** selected. **Do not infer
this from the YAML file alone** — the file states intent; only the host demonstrates
behaviour.

---

## RB-04 — Codex hook-root runtime experiment

Covers E13 (Codex half).

Use **only** `tests/fixtures/host-tests/codex-hook-root/`. Do not copy the hook into the
production plugin.

Verify only:

| Field | Result |
| :--- | :--- |
| `PLUGIN_ROOT` exists in the hook command | Not Run |
| `PLUGIN_DATA` exists in the hook command | Not Run |
| `CLAUDE_PLUGIN_ROOT` compatibility variable exists | Not Run |
| `CLAUDE_PLUGIN_DATA` compatibility variable exists | Not Run |
| plugin root stays inside the disposable installation | Not Run |
| plugin data stays inside the isolated writable location | Not Run |

The hook outputs booleans and fixed markers only — never environment values, never
absolute user paths, never an environment dump.

**Simulating the variables is not host verification.** If no safe documented trigger
exists, mark Runtime **Manual Required**, keep the static fixture validation Passed, and
keep E13 non-Passed.

---

## RB-05 — Codex Skill-script path experiment

Covers Q-IMPL-003 (Codex half).

Use **only** `tests/fixtures/host-tests/skill-script-path/`.

The experiment must not assume: current working directory, `PLUGIN_ROOT`,
`CLAUDE_PLUGIN_ROOT`, `CLAUDE_SKILL_DIR`, or an absolute installation cache path.

| Field | Result |
| :--- | :--- |
| mechanism tested | Not Run |
| was it documented | Not Run |
| fixture helper found | Not Run |
| resolved path stayed inside the plugin | Not Run |
| worked from a path containing spaces | Not Run |
| helper wrote only to the temporary output directory | Not Run |

If no documented portable mechanism works: mark **Failed or Unresolved**, do not invent a
workaround, recommend an adapter-specific launcher or generated host variant for M2
design, keep Q-IMPL-003 open, and keep E13 non-Passed.

---

## RB-06 — ChatGPT Desktop marketplace experiments

Covers E12. **Blocked by DEF-001 for Candidate C** — the generated OpenAI catalog is
rejected by the Codex parser, so Candidate C cannot be meaningfully tested on an OpenAI
surface until M1.3 lands the fix.

### Before any manual step

1. Snapshot `~/.codex/config.toml` (record only whether an `agent-harness` entry exists).
2. Record which marketplaces are already registered — names only.
3. Use a **disposable repository copy**, never the working tree.

### Candidate A — separate independently maintained catalogs

| Field | Result |
| :--- | :--- |
| Claude catalog recognized | Not Run |
| OpenAI catalog recognized | Not Run |
| duplication / drift risk observed | Not Run |

### Candidate B — only `.claude-plugin/marketplace.json`

| Field | Result |
| :--- | :--- |
| ChatGPT Desktop recognizes the legacy path | Not Run |
| Codex CLI behaviour (recorded separately) | Not Run |
| **OpenAI policy metadata preserved** | Not Run |
| Claude behaviour (recorded separately) | Not Run |

**Candidate B may not be selected unless every one of these passes.**

### Candidate C — canonical source, generated catalogs

| Field | Result |
| :--- | :--- |
| Claude marketplace | **Passed** (already verified, CLI) |
| Codex marketplace registration | **Failed** — DEF-001 |
| ChatGPT Desktop Plugins Directory | Not Run |
| plugin installation in Desktop | Not Run |
| fixture Skill appears after installation | Not Run |
| explicit fixture invocation returns marker | Not Run |

### Teardown

1. Disable, then uninstall the plugin through the Desktop UI.
2. Remove the marketplace: `codex plugin marketplace remove agent-harness`.
3. Cache cleanup only where officially documented — do not delete paths by guesswork.
4. Confirm `~/.codex/config.toml` has no `agent-harness` entry.
5. Delete the disposable repository copy.

---

## What the agent already did, so you do not repeat it

| Done automatically | How it stayed safe |
| :--- | :--- |
| Codex marketplace registration | isolated `CODEX_HOME`, disposable repo copy, real config verified clean afterwards |
| Codex plugin installation | same isolation; installed into the isolated cache only |
| Dual-manifest tolerance | proven — installed from a root with both manifests |
| Claude strict validation | read-only |

**M1.3.1 ran no host command at all.** It corrected contract evidence deterministically:
the schema now accepts both documented OpenAI local `source` forms, the documented
kebab-case identifier patterns were restored, and `ON_USE` was relabelled Host-Observed.
The Codex probe was **not** re-run — the ENV-001 side effect below was not approved for
that pass — so every host result in this runbook still stands as recorded. Nothing here
became Passed because of a schema change.

**Disclosed side effect:** every `codex` invocation writes `~/.codex/logs_2.sqlite-wal`,
`~/.codex/models_cache.json`, and temp helper files under `~/.codex/tmp/`. `CODEX_HOME`
does not redirect these. No configuration, marketplace, or plugin state was affected.
