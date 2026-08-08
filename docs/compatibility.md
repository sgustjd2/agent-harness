# Host compatibility record

The durable record of what has been verified, what is inferred, and what has been tried.

**Recording an outcome is the requirement; a positive outcome is not.** A negative
result is valid. An unrecorded result is not.

Last updated: 2026-08-08 (M1.3 contract remediation).

---

## 1. Verification legend

| Label | Meaning |
| :--- | :--- |
| **[V]** Verified | confirmed in official host documentation, or observed from a real host command |
| **[I]** Inferred | not stated in documentation; needs implementation-stage verification |
| **[C]** Composed | individual facts are [V], but the *combination* is unproven |
| **[P]** Plugin behavior | implemented by agent-harness, not by a host |

---

## 2. Validation mechanisms — which tool judged what

M1 exit criteria E3 and E4 require recording the mechanism, not just the result.

| Artifact | Mechanism | Authoritative? |
| :--- | :--- | :--- |
| Claude plugin manifest | **`claude plugin validate ./plugins/agent-harness --strict`** — real host CLI, Claude Code 2.1.195 → exit 0 | **yes, host** |
| Claude marketplace catalog | **`claude plugin validate . --strict`** — real host CLI → exit 0 | **yes, host** |
| Claude plugin manifest (also) | `claude-plugin.schema.json` via jsonschema | local compatibility |
| Claude marketplace catalog (also) | `claude-marketplace.schema.json` via jsonschema | local compatibility |
| **Codex plugin manifest** | `codex-plugin.schema.json` via jsonschema + **indirect host evidence**: `codex plugin add` parsed and installed from it | local + indirect host |
| **Codex marketplace catalog** | `openai-marketplace.schema.json` via jsonschema, **corrected in M1.3 and revalidated on the real host** (`codex plugin marketplace add` accepted the generated catalog, isolated, no install) | local + host-revalidated |
| Canonical marketplace source | `canonical-marketplace.schema.json` via jsonschema | local, agent-harness's own format |
| Skill frontmatter | PyYAML `yaml.safe_load` + `validate_skills.py` | local |

**Claude validation and OpenAI local-schema validation are different things and are
never conflated.** Claude artifacts were judged by a real host validator. Codex
artifacts were judged only by schemas written here, because no official Codex validator
was found (Q-IMPL-009). A Codex artifact passing our schema is **not** evidence that a
Codex host would accept it.

### Codex CLI availability: **AVAILABLE** (M1.2 correction)

M1.1 recorded Codex CLI as Not Available because `command -v codex` failed. That was
incomplete: the CLI ships **inside ChatGPT Desktop** and works when invoked by absolute
path.

| | |
| :--- | :--- |
| Version | `codex-cli 0.146.0-alpha.9.2` |
| On PATH | no |
| Subcommands observed | `plugin {add, list, marketplace, remove}`; `marketplace {add, list, upgrade, remove}` |
| **Official validate subcommand** | **Not Available** — no `validate` in real help output; none invented |
| Config home override | `$CODEX_HOME` (documented) — used for isolation |

**Two findings that change earlier conclusions:**

1. **`codex plugin add` installs a plugin from the CLI alone.** Q-IMPL-011 is resolved:
   ChatGPT Desktop is not required for installation.
2. **`codex plugin marketplace add` REJECTED our generated OpenAI catalog** — DEF-001.
   **Remediated in M1.3**: the invented `policy.install` was removed and
   `authentication: "none"` replaced with the documented contract. The corrected
   catalog was re-registered successfully on the same host, registration only.

---

## 3. Marketplace catalog strategy

**Candidate C is the provisional implementation strategy. DEC-P14 remains Proposed —
and M1.2 found Candidate C FAILS on the real Codex surface (DEF-001).**

Those are different statements. The implementation avoids two hand-edited catalogs;
the architecture decision awaits host evidence.

| | |
| :--- | :--- |
| Hand-edited | `marketplace/marketplace.source.json` — the only one |
| Generated | `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` |
| Enforcement | `generate_marketplaces.py --check` byte-compares in CI |
| Determinism | verified — two runs produce byte-identical output |

Candidate B is **not selected** and cannot be until every mandatory host surface is
positively verified. The ChatGPT desktop app reading the legacy Claude path is not
sufficient: it says nothing about Codex CLI behaviour and nothing about whether policy
metadata survives. Neither has been tested.

Full matrix: [`m1-experiments.md`](m1-experiments.md).

---

## 4. Facts recorded from documentation

### 4.1 Marketplace registration is not plugin installation **[V]**

| Step | Who | How |
| :--- | :--- | :--- |
| 1. register a marketplace source | Codex CLI | `codex plugin marketplace add <source>` |
| 2. install and enable a plugin | Codex CLI **or** ChatGPT Desktop | CLI: `codex plugin add PLUGIN@MARKETPLACE`. Desktop: Plugins screen |

**M1.2 empirically confirmed the separation.** After registration succeeded,
`codex plugin list` reported the plugin as `not installed`. Only after
`codex plugin add` did it become `installed, enabled`. Two distinct steps on the real
host, not merely in our documentation.

**Q-IMPL-011 — host-verified on codex-cli 0.146.0-alpha.9.2; cross-version and
stable-documentation status remains Open.**

Three claims, kept separate:

| Claim | Status |
| :--- | :--- |
| the install-class subcommand appeared in actual help output | **Host-Observed**, version 0.146.0-alpha.9.2 |
| CLI installation succeeded on that alpha version | **Host-Observed**, isolated (PROC-001) |
| current public documentation defines it as the stable general installation path | **No** — the published packaging documentation covers `marketplace add/list/upgrade/remove` and ChatGPT Desktop installation |

So the CLI path is real on the tested build but is **not** a stable cross-version
contract, and is not presented as one. The literal string this repository guards
against still does not exist — the subcommand is `add` — so
`check_no_install_command.py` stays correct.

### 4.2 Codex plugin manifest **[V]**

`.codex-plugin/plugin.json`; minimal form is `name`, `version`, `description`, `skills`.
`skills` is a **relative directory path string** — `"./skills/"` — not an array. Encoded
in `codex-plugin.schema.json` as `type: string` with a path-shape pattern, so an array
is a schema violation rather than a silently accepted variant.

### 4.3 Skill invocation policy **[V]**

`skills/<name>/agents/openai.yaml` supports `policy.allow_implicit_invocation`. When
`false`, Codex will not implicitly select the Skill; **explicit `$skill` invocation
still works.** It is a separate file from `SKILL.md`, so it does not affect the
canonical frontmatter minimum set.

### 4.4 Plugin hook environment **[V], hook context only**

Plugin hook commands receive `PLUGIN_ROOT` and `PLUGIN_DATA`, plus compatibility aliases
`CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA`.

**Verified for hooks. Not verified for Skill-started commands.** Inheritance into the
Skill execution context is undocumented, so the canonical layer must not assume it;
`check_path_portability.py` fails on any `PLUGIN_ROOT` reference there. The MVP ships no
hooks in any case.

### 4.5 Marketplace paths readable by the ChatGPT desktop app **[V]**

`$REPO_ROOT/.agents/plugins/marketplace.json`, legacy
`$REPO_ROOT/.claude-plugin/marketplace.json`, and `~/.agents/plugins/marketplace.json`.

**Four things this does not establish**, none of which is assumed anywhere:

1. that Codex CLI accepts the same schema at both paths
2. that Claude Code accepts OpenAI-specific marketplace policy fields
3. that one physical catalog file is proven sufficient
4. that desktop-app compatibility implies Codex CLI compatibility

---

## 5. Host commands executed

No plugin installed into the **real** user cache; no marketplace registered in the
**real** user config; no user configuration changed. All Codex state changes landed in an
isolated `CODEX_HOME` against a disposable repository copy, both deleted afterwards.

| Command | Host | Version | Exit | Result |
| :--- | :--- | :--- | ---: | :--- |
| `claude plugin validate . --strict` | Claude Code | 2.1.195 | 0 | `✔ Validation passed` |
| `claude plugin validate ./plugins/agent-harness --strict` | Claude Code | 2.1.195 | 0 | `✔ Validation passed`, `.codex-plugin/` present |
| `codex --version` | Codex CLI | 0.146.0-alpha.9.2 | 0 | available (absolute path) |
| `codex plugin --help` / `plugin marketplace --help` | Codex CLI | 0.146.0-alpha.9.2 | 0 | no `validate` subcommand |
| `codex plugin marketplace add <disposable>` | Codex CLI | 0.146.0-alpha.9.2 | **≠0** | **DEF-001** — rejected `policy.authentication: "none"` |
| `codex plugin marketplace add` (diagnostic variants) | Codex CLI | 0.146.0-alpha.9.2 | 0 | accepted with `ON_USE` / `ON_INSTALL` / field absent |
| `codex plugin marketplace list` | Codex CLI | 0.146.0-alpha.9.2 | 0 | disposable marketplace resolved |
| `codex plugin list` | Codex CLI | 0.146.0-alpha.9.2 | 0 | `agent-harness@agent-harness`, `not installed` |
| `codex plugin add agent-harness@agent-harness` | Codex CLI | 0.146.0-alpha.9.2 | 0 | `installed, enabled`, v0.0.1 |

`--strict` was accepted, so Claude strict validation genuinely ran. All output is bounded
and home paths redacted.

**Two notable results:**

1. Claude accepted a plugin root containing `.codex-plugin/` — ATS-018-1 (validator
   tolerance only, not runtime loading).
2. Codex **installed** from a root containing `.claude-plugin/`, and the install cache
   preserved both manifests, `skills/`, and `agents/openai.yaml` — ATS-018-2 and
   ATS-018-6.

**Disclosed side effect.** Every `codex` invocation writes `~/.codex/logs_2.sqlite-wal`,
`~/.codex/models_cache.json`, and temp helper files under `~/.codex/tmp/`. `CODEX_HOME`
does not redirect these. No configuration, marketplace, or plugin state was affected —
verified by inspecting the real `config.toml` and plugin cache afterwards.

---

## 6. CI versus manual host tests

| Test | Where | Model needed |
| :--- | :--- | :--- |
| manifest / catalog schema validation (jsonschema) | CI | no |
| Skill metadata and boundary (PyYAML) | CI | no |
| containment, portability, version sync, no-network | CI | no |
| catalog generation determinism | CI | no |
| 27 negative scenarios (pytest) | CI | no |
| **`claude plugin validate`** | **manual, executed** | no (host CLI) |
| **ATS-018-2/3/4/5/6** | **manual, not run** | no (host CLI) |
| **ATS-022 host surfaces** | **manual, not run** | no (CLI / desktop app) |
| **ATS-028** hook root | **manual, not run** | no |
| **ATS-020** Skill script path | **manual, not run** | **possibly** |

No CI workflow configures a model API key or invokes a model. pytest markers
(`deterministic`, `host_cli`, `manual`) enforce the split, and CI runs
`-m "not manual and not host_cli"`.

---

## 7. Platform support

Supported: **macOS, Linux, WSL.** Native Windows outside WSL is **Deferred**.

CI covers `ubuntu-latest` and `macos-latest`; WSL is represented by the Linux runner,
which is stated here rather than implied. One M1.1 finding is relevant: catalog
generation emitted CRLF on Windows, which broke byte-determinism. Fixed by pinning LF
and adding `.gitattributes` — the kind of defect a Windows-adjacent developer hits first.

NS-19 (symlink escape) is skipped on Windows because creating a symlink there needs
elevation. The check itself is platform-neutral and runs on CI.

---

## 8. Open after M1.1

| ID | Question | Blocking M2? |
| :--- | :--- | :--- |
| Q-IMPL-002 | Does Codex ignore or reject unknown `SKILL.md` frontmatter keys? | no — the minimum set is safe either way |
| Q-IMPL-003 (Skill half) | How does a canonical Skill locate bundled scripts? | no — helper execution deferred until answered |
| Q-IMPL-004 | Codex private-repository authentication | no |
| Q-IMPL-009 | Is there an official Codex validator? | no — local schemas documented in §2 |
| Q-IMPL-010 | Approval interaction model and non-replayable representation | no for M2, **yes before M6** |
| Q-IMPL-011 | Can the Codex CLI alone install a plugin? | no — fallback documented |
| DEC-P13 | Is manifest co-location viable? | **needs a Codex host** |
| DEC-P14 | Which marketplace candidate? | **needs host surfaces** |


---

## 9. M1.3 marketplace contract (corrected)

The generated OpenAI catalog now carries only fields with documented evidence:

| Field | Value | Evidence |
| :--- | :--- | :--- |
| `policy.installation` | `AVAILABLE` | Official-Documented |
| `policy.authentication` | `ON_INSTALL` | Official-Documented (published example) |
| `category` | `Productivity` | Official-Documented (published example) |
| `source` | `{"source": "local", "path": "./plugins/agent-harness"}` | object form: Official-Documented. **Emitting it rather than the equally documented plain string is Local-M1-Policy.** |

Removed: `policy.install` (invented, never documented, ignored by the host) and
`authentication: "none"` (invented, rejected by the host).

### Both local `source` forms are officially supported (M1.3.1)

OpenAI documents two representations for a local marketplace entry:

| Form | Example | Status |
| :--- | :--- | :--- |
| object | `{"source": "local", "path": "./plugins/agent-harness"}` | **Official-Documented** |
| plain string | `"./plugins/agent-harness"` | **Official-Documented** |

Both are accepted by the host and resolve identically. **A plain string `source` is not a
defect and not a malformed artifact.** The local compatibility schema accepts both.

Candidate C emits the object form **by local choice** — it names the source type
explicitly, leaves room for non-local types, and maps field-for-field from the canonical
model. That is this repository's preference, not a vendor requirement, and a hand-written
catalog using the string form is equally valid.

### Identifiers are kebab-case; labels are not (M1.3.1)

| Field | Constraint | Evidence |
| :--- | :--- | :--- |
| Claude marketplace `name` | kebab-case, no spaces | Official-Documented |
| Claude marketplace `plugins[].name` | kebab-case, no spaces | Official-Documented |
| Claude plugin manifest `name` | kebab-case | Official-Documented |
| OpenAI plugin manifest `name` | stable kebab-case identifier | Official-Documented |
| OpenAI marketplace `plugins[].name` | must equal the Codex manifest identity; kebab-case follows | **Local-M1-Policy** derived from the Official-Documented manifest-identity contract (corrected M1.4A) |
| `category` | **none** — free-form label | kebab-case here was an M1.1 invention, removed |
| `interface.displayName`, descriptions, owner names | **none** — free-form | — |

M1.3 removed the identifier patterns as inventions. They are documented; the removal was a
regression, restored in M1.3.1. Rejection of leading, trailing and repeated hyphens is a
Local-M1-Policy refinement of "kebab-case, no spaces", not a separately published rule.

### `ON_USE` is host-observed, not documented (M1.3.1)

| Claim | Status |
| :--- | :--- |
| `ON_INSTALL` literal | **Official-Documented** — appears in the published example |
| authentication on install vs. first use (the *behaviour*) | **Official-Documented** semantics |
| `ON_USE` literal spelling | **Host-Observed** on codex-cli 0.146.0-alpha.9.2 only |

The compatibility schema still permits `ON_USE` so a host-observed variant validates, but
the generator never selects it: Candidate C always emits `ON_INSTALL`.

**No compatibility alias was kept for `policy.install`.** A misspelling must fail
validation rather than be silently repaired.

The Claude catalog carries **no** installation or authentication policy fields, because
Claude publishes no equivalent. Emitting them there would assert a contract Claude does
not define — the same error as DEF-001, in the other direction.

Local schemas are evidence-backed but remain **local compatibility schemas, not official
vendor schemas**. Host acceptance of an unknown field does not make that field valid: the
host accepted `policy.install` with a deliberately bogus value, which proves only that it
ignores the key.

Full field-by-field evidence: [`m1-defects.md`](m1-defects.md) contract table.


---

## 10. Claude runtime evidence (M1.4A)

Claude Code **2.1.195**, non-interactive, no model invoked.

| Fact | Status | How |
| :--- | :--- | :--- |
| strict validator accepts a root containing `.codex-plugin/` | **Passed** | `claude plugin validate --strict` (earlier phases) |
| host **loads** that same root at runtime | **Passed** | `claude --plugin-dir <root> plugin list --json` -> `agent-harness@inline`, `scope: session` |
| host **discovers** the shared `skills/` directory | **Passed** | `claude --plugin-dir <root> plugin details agent-harness@inline` -> `Skills (1) m1-discovery-fixture` |
| loading and discovery survive a path containing spaces | **Passed** | repeated against a byte-identical disposable copy |
| host **invokes** the Skill | **Not Run** | requires a model |
| `${CLAUDE_PLUGIN_ROOT}` helper execution | **Not Run** | M1.4B |

These are five separate facts. There is no aggregate "Claude host Passed" status, because
a validator result, a load, a discovery and an invocation fail in different ways.

**Session-scoped loading creates no installed record.** Documented, and verified in both
directions: the plugin appears when the flag precedes the subcommand, and a bare
`claude plugin list` omits it. The plugin-cache tree and `~/.claude/settings.json` were
byte-identical before and after every command.

### Identifier assigned by the host

The host named the session-scoped plugin `agent-harness@inline`. The `@inline` suffix is
the **source**, not part of the plugin identity - the identity is `agent-harness`, matching
both manifests and both catalogs.
