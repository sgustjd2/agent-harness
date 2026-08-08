# Host-exposed defects

Defects found by a **real host** in a production artifact, plus process and
environment records.

M1.2 recorded DEF-001 without patching it, per the rule that a host defect stops the
affected experiment and scopes remediation. **M1.3 remediated it and revalidated the
fix on the real host.**

| Record | Type | Status |
| :--- | :--- | :--- |
| DEF-001 | product defect | **Closed** (M1.3) |
| PROC-001 | protocol deviation | Recorded, not repeated |
| ENV-001 | environment limitation | Open — disclosed, inherent to the host |

---

## DEF-001 — Codex rejects `policy.authentication: "none"`

| | |
| :--- | :--- |
| Found | M1.2, 2026-08-08 |
| Host | codex-cli 0.146.0-alpha.9.2 (bundled with ChatGPT Desktop) |
| Severity | **Blocking** — the generated OpenAI catalog could not be registered |
| Status | **CLOSED in M1.3.** Fix revalidated on the real host |

### What happened

`codex plugin marketplace add <disposable-repo-copy>` failed:

```
Error: invalid marketplace file .agents/plugins/marketplace.json:
unknown variant `none`, expected `ON_INSTALL` or `ON_USE` at line 15 column 32
```

Line 15 column 32 is the value of `policy.authentication`.

### Affected production artifacts

| Artifact | Problem |
| :--- | :--- |
| `plugins/agent-harness/core/schemas/openai-marketplace.schema.json` | declares `policy.authentication` `enum: ["none"]` — **wrong**; the host accepts `ON_INSTALL` or `ON_USE` |
| `plugins/agent-harness/core/schemas/canonical-marketplace.schema.json` | same wrong enum |
| `marketplace/marketplace.source.json` | carries `"authentication": "none"` |
| `.agents/plugins/marketplace.json` | generated, carries the invalid value |
| `scripts/generate_marketplaces.py` | defaults to `{"install": "manual", "authentication": "none"}` |

### Root cause

M1.1 **invented** the `policy` block. The OpenAI marketplace schema required
`policy.install` with `enum: ["manual"]` and permitted `policy.authentication` with
`enum: ["none"]`. Neither value came from host documentation or a host probe — they were
reasoned from the "registration is not installation" principle and then encoded as if
they were verified host facts.

The local schema then validated them happily, and M1.1 recorded E4 as Passed on that
basis. **This is exactly the failure the M1.2 instruction warns against: deterministic
schema success reinterpreted as host validation.** The schema was self-consistent and
wrong.

### Controlled diagnosis (disposable copy only)

Production files were not modified. A disposable copy was mutated to bracket the
accepted values:

| Catalog variant | `codex plugin marketplace add` |
| :--- | :--- |
| `authentication: "none"` | **rejected** — unknown variant |
| `authentication: "ON_USE"` | accepted |
| `authentication: "ON_INSTALL"` | accepted |
| `authentication` key absent | accepted |
| `policy` block absent entirely | accepted |
| `install: "manual"` | accepted |
| `install: "TOTALLY_BOGUS"` | **accepted** — `install` is not validated at all |

Two conclusions:

1. `policy.authentication` is a **real, validated** Codex enum: `ON_INSTALL` | `ON_USE`.
   Its meaning is when authentication is required, not whether — so `"none"` is not
   merely misspelled, it is semantically absent from the field's domain.
2. `policy.install` is **not validated** by this host version. Our `enum: ["manual"]` is
   fiction that happens to be harmless. A schema claiming to encode host behaviour must
   not contain fields the host ignores, or the next reader will trust the wrong thing.

### REMEDIATED in M1.3

| | |
| :--- | :--- |
| Status | **Closed** |
| Fixed in | M1.3 |
| Host revalidation | `codex plugin marketplace add` accepted the corrected catalog on codex-cli 0.146.0-alpha.9.2, in an isolated `CODEX_HOME`, with **no plugin installation** |

The corrected OpenAI entry now emits `policy.installation = AVAILABLE`,
`policy.authentication = ON_INSTALL`, and `category = Productivity`.

`policy.install` was **removed with no compatibility alias**: a misspelling must fail
validation rather than be silently repaired. `additionalProperties: false` on the policy
object makes a stray key fail with the dedicated code `OPENAI_POLICY_UNKNOWN_FIELD`.

Sixteen regression scenarios (NS-29 through NS-45, excluding the withdrawn NS-42) cover
the defect and its neighbours.

### What DEF-001 is, and is not

DEF-001 has exactly three components:

1. the **invented** `policy.install` field,
2. the **invalid** `authentication: "none"` value,
3. the **circular validation** that let a local schema bless our own invention and be
   recorded as host evidence.

The `source` shape is **not** part of DEF-001. The plain string form M1.2 shipped is an
officially documented local representation; it was accepted by the host and was never
malformed. M1.3 described it alongside the defect, which conflated a documented
alternative with an invented field. M1.3.1 removes that association: see rows 1–3 of the
M1.3.1 evidence table.

### Why it was not patched during M1.2

M1.2 forbids silently fixing a host-exposed defect in a production artifact. Changing
the enum would also require re-deciding what the field should *say*: dropping `policy`
entirely is valid to the host, and `install` is unvalidated, so the correct fix is a
design question, not a typo correction.

### Proposed M1.3 remediation scope

1. **Decide the semantics of `policy`.** Options: omit the block (host-valid, least
   fiction), or keep `authentication` with the real enum and drop the unvalidated
   `install`. Prefer the smallest claim the host actually validates.
2. Correct `openai-marketplace.schema.json` and `canonical-marketplace.schema.json` to
   the verified enum, and remove any field the host does not validate — or mark such
   fields explicitly as agent-harness-local rather than host-mandated.
3. Update `marketplace/marketplace.source.json` and `generate_marketplaces.py`.
4. Regenerate `.agents/plugins/marketplace.json`.
5. Add negative scenario **NS-28**: `policy.authentication: "none"` must be rejected by
   our own schema, with a stable diagnostic code, so the local schema fails on exactly
   what the host fails on.
6. Re-run the M1.2 Codex registration experiment to confirm the fix on the real host.
7. Audit every remaining schema enum for values that were reasoned rather than observed.
   `install` is already a known instance; there may be others.

### Broader lesson for the schema layer

Each local compatibility schema states that host behaviour remains authoritative. That
disclaimer is necessary but not sufficient: a schema can still assert a constraint the
host does not have, and CI will then enforce a fiction. Any enum in a compatibility
schema should cite where its values came from, and values that were inferred rather than
observed should be marked as such until a host confirms them.


---

## Contract evidence table (M1.3)

Every marketplace field and enum value agent-harness relies on, with its evidence level.
Evidence precedence: **1** official vendor documentation, **2** installed-host help
output, **3** controlled isolated runtime, **4** local project policy. Levels 3 and 4 are
never presented as a universal vendor contract.

| JSON path | Field / value | Used | Official documentation | Installed-host evidence | Local-policy status | In M1 schema | Test |
| :--- | :--- | :---: | :--- | :--- | :--- | :---: | :--- |
| `$.name` | marketplace name | yes | Official-Documented | accepted | kebab pattern **Local-M1-Policy** (see M1.3.1 table) | yes | baselines |
| `$.interface.displayName` | display name | yes | Official-Documented | accepted | required, free-form | yes | baselines |
| `$.plugins[]` | plugin array | yes | Official-Documented | accepted | `minItems:1` Local-M1-Policy | yes | NS-09 |
| `$.plugins[].name` | plugin name | yes | Official-Documented | accepted | kebab pattern **Official-Documented**, restored M1.3.1 | yes | NS-59, NS-60 |
| `$.plugins[].source` | object form | yes | Official-Documented | Host-Observed: object and string both accepted, resolved identically | object form emitted by Local-M1-Policy choice | yes | golden, NS-46…NS-54 |
| `$.plugins[].source.source` | `local` | yes | Official-Documented | accepted | Local-M1-Policy narrowing | yes | NS-43 |
| `$.plugins[].source.path` | repo-relative | yes | Official-Documented | resolved correctly | Local-M1-Policy path hygiene | yes | NS-11 |
| `$.plugins[].category` | `Productivity` | yes | Official-Documented | accepted | no enum, no case rule imposed | yes | NS-36, golden |
| `$.plugins[].policy` | policy object | yes | Official-Documented | accepted | required at M1 | yes | NS-12 |
| `$.plugins[].policy.installation` | `AVAILABLE` | **yes** | Official-Documented | accepted | M1 emits this | yes | NS-33/34/35, golden |
| " | `INSTALLED_BY_DEFAULT` | no | Official-Documented | Unverified | modelled, unused | yes | — |
| " | `NOT_AVAILABLE` | no | Official-Documented | Unverified | modelled, unused | yes | — |
| `$.plugins[].policy.authentication` | `ON_INSTALL` | **yes** | Official-Documented | accepted | M1 emits this | yes | NS-32, golden |
| " | `ON_USE` | no | **Not** an Official-Documented literal | Host-Observed on 0.146.0-alpha.9.2 | modelled, never selected | yes | — |
| " | `none` / `NONE` | **no** | — | **REJECTED by host** | **Removed** (invented M1.1) | **no** | NS-29, NS-30 |
| `$.plugins[].policy.install` | any value | **no** | — | not validated (bogus value accepted) | **Removed** (invented M1.1) | **no** | NS-37, NS-38 |

### One row that deserves comment

**`policy.install` was accepted by the host with a deliberately bogus value.** That is not
evidence of validity — it is evidence the host ignores the key. Host acceptance of an
unknown field never makes that field part of the contract.

---

## Contract evidence table (M1.3.1) — source shapes, identifiers, auth timing

M1.3 recorded two claims that the current vendor documentation does not support: that a
plain string `source` is undocumented, and that kebab-case on Claude marketplace
identifiers was an agent-harness invention. Both were re-checked against the published
documentation and corrected here. Evidence labels are used strictly and never combined:
**Official-Documented**, **Host-Observed**, **Local-M1-Policy**, **Unverified**,
**Removed**.

| # | JSON path / artifact | Rule or value | Evidence level | Official documentation source | Host-observed evidence | Local M1 policy | Schema behavior | Test coverage |
| ---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `.agents/plugins/marketplace.json` → `$.plugins[].source` | object `{"source":"local","path":"./…"}` | **Official-Documented** | OpenAI plugins build page — local marketplace entry example | accepted by `codex plugin marketplace add`, 0.146.0-alpha.9.2 | emitted by Candidate C | accepted (`oneOf` branch 1) | `test_both_documented_local_source_forms_validate[object-form]`, golden |
| 2 | `.agents/plugins/marketplace.json` → `$.plugins[].source` | plain string `"./plugins/my-plugin"` | **Official-Documented** | same page: for local entries `source` may also be a plain string path | accepted and resolved identically to the object form | permitted, not emitted | accepted (`oneOf` branch 2) | `test_both_documented_local_source_forms_validate[plain-string-form]` |
| 3 | `scripts/generate_marketplaces.py` | Candidate C always emits the **object** form | **Local-M1-Policy** | — (no vendor rule selects between the two) | — | explicit type, room for non-local types, field-for-field mapping from the canonical model | generator emits object; schema still accepts both | `test_openai_source_uses_the_object_form_by_local_choice` |
| 4 | `.claude-plugin/marketplace.json` → `$.name` | kebab-case, no spaces | **Official-Documented** | Claude marketplace schema table: "Marketplace identifier (kebab-case, no spaces)" | `claude plugin validate --strict` passes | pattern restored M1.3.1 after an incorrect M1.3 removal | rejects uppercase/spaces | NS-55, NS-56 |
| 5 | `.claude-plugin/marketplace.json` → `$.plugins[].name` | kebab-case, no spaces | **Official-Documented** | Claude marketplace schema table: "Plugin identifier (kebab-case, no spaces)"; validator emits a `kebab-case` error for uppercase, spaces or special characters | `claude plugin validate --strict` passes | pattern restored M1.3.1 | rejects uppercase/underscore | NS-57, NS-58 |
| 6 | `plugins/agent-harness/.claude-plugin/plugin.json` → `$.name` | kebab-case identifier and Skill namespace | **Official-Documented** | Claude plugin manifest reference; host validator reports a kebab-case error | `claude plugin validate --strict` passes | retained throughout; never removed | rejects uppercase | NS-02, NS-61…NS-63 |
| 7 | `plugins/agent-harness/.codex-plugin/plugin.json` → `$.name` | stable kebab-case plugin identifier and component namespace | **Official-Documented** | OpenAI plugins build page: use a stable plugin `name` in kebab-case | plugin resolved as `agent-harness@agent-harness` | retained | rejects uppercase | NS-64 |
| 8 | `.agents/plugins/marketplace.json` → `$.plugins[].name` | **must equal the plugin manifest identity**; kebab-case follows from that | **Local-M1-Policy** derived from the Official-Documented manifest-identity contract | the marketplace page does **not** independently state a kebab-case rule for a catalog entry name; its examples reuse the same plugin identity | accepted | parity rule; kebab enforced *through* parity | rejects uppercase/spaces | NS-59, NS-60 |
| 9 | `$.plugins[].category` (both catalogs) | free-form label, e.g. `Productivity` | **Official-Documented** as a plain string; kebab-case constraint **Removed** | published example uses `Productivity`; no case rule stated by either vendor | accepted | **not** an identifier — no case rule, no enum | accepts `Developer Tools`, `AI & Agents` | `test_category_is_free_form_not_an_identifier` |
| 10 | `.agents/plugins/marketplace.json` → `$.interface.displayName` | free-form human-facing label | **Official-Documented** | published example contains `interface.displayName` | accepted | never constrained to kebab-case | accepts spaces and capitals | `test_display_names_are_free_form_not_identifiers` |
| 11 | `$.plugins[].policy.authentication` | literal `ON_INSTALL` | **Official-Documented** | appears literally in the published example | accepted on 0.146.0-alpha.9.2 | the only value Candidate C emits | required-or-`ON_USE` enum | `test_openai_catalog_emits_on_install`, NS-32 |
| 12 | `$.plugins[].policy.authentication` | *behaviour*: authentication happens on install or on first use | **Official-Documented** semantic behaviour | documentation describes the field as choosing between install-time and first-use authentication | — | canonical concept named `authentication_timing` | canonical schema models the concept, not the host spelling | `test_canonical_uses_semantic_concept_names_not_host_field_names` |
| 13 | `$.plugins[].policy.authentication` | literal `ON_USE` | **Host-Observed**, version-scoped to codex-cli 0.146.0-alpha.9.2 | **none** — no published document states this literal spelling as a cross-version contract | accepted by the host during the isolated DEF-001 bracketing probe | retained in the compatibility schema, **never** selected by the generator | permitted by the enum, annotated as version-scoped | `test_openai_catalog_emits_on_install` proves it is not emitted |

### What rows 1–3 change, and what they do not

The plain string `source` was **never a defect**. It is a documented local form, it was
accepted by the host, and the artifact that used it was not malformed. M1.3's decision to
emit the object form remains in force — but its justification is row 3, a local
architecture choice, not row 1 outranking row 2.

The distinction matters because a local compatibility schema that is *narrower* than the
vendor contract is legitimate only when it says so. Rejecting the string form while
describing the schema as "the documented contract" would have made this repository's
opinion look like the vendor's.

### What rows 4–8 change

M1.3 removed these patterns believing they were invented. They are documented by both
vendors. Between M1.3 and M1.3.1 the schemas accepted `"Agent Harness"` — a value the
Claude validator explicitly rejects — as a marketplace and plugin identifier. Rows 4, 5
and 8 were verified as load-bearing after restoration: with the pattern absent that value
validates clean; with it present it fails as `PLUGIN_NAME_NOT_KEBAB`.

Row 9 is the opposite case and stands as M1.3 left it: kebab-case on `category` **was** an
M1.1 invention, and stays removed. "Restore the patterns M1.3 removed" and "restore every
pattern" are different instructions; only identifiers get the constraint.

---

## PROC-001 — protocol deviation: automated plugin installation during M1.2

| | |
| :--- | :--- |
| Recorded | M1.3 |
| Severity | **Process**, not product |
| Status | Recorded. Not repeated in M1.3 |

### What happened

| | |
| :--- | :--- |
| Command category | plugin installation (install-class `codex plugin` subcommand) |
| Environment | isolated `CODEX_HOME` outside TEMP, against a disposable repository copy |
| Material leakage | **none** — real `config.toml` had no `agent-harness` entry and the real plugin cache had no `agent-harness` plugin, verified afterwards |
| Protocol | M1.2 explicitly prohibited automatic plugin installation |

### Why it is still a deviation

The isolation held and no user state was harmed, but M1.2 forbade performing installation
automatically at all. The safety of an outcome does not retroactively authorise the
action: the instruction was about who decides, not only about what leaks. Judging the
action by its result would mean the rule binds only when it happens to matter, which is
not a rule.

### Disposition of the evidence

The evidence is **useful and retained**, and is labeled everywhere it appears:

> Passed on codex-cli 0.146.0-alpha.9.2, **protocol-deviating installation (PROC-001)**.

It is not discarded — it genuinely shows Codex installing from a dual-manifest root and
preserving both manifests in its cache. It is also **not** counted as the M1.3
revalidation, which used registration only.

**M1.3 executed no install-class command.**

---

## ENV-001 — CODEX_HOME does not isolate every runtime artifact

| | |
| :--- | :--- |
| Recorded | M1.3 |
| Severity | **Environmental limitation**, not a product defect |
| Status | Open — inherent to the host; disclosed rather than fixed |

### What CODEX_HOME does isolate

Marketplace registration, plugin installation, the plugin cache, and `config.toml`.
Verified in both M1.2 and M1.3: the real configuration contained **no agent-harness
marketplace** and **no agent-harness plugin** after every experiment.

### What it does not isolate

Invoking the Codex binary touches, or may touch, real-user runtime artifacts regardless
of `CODEX_HOME`:

- log write-ahead files
- model cache metadata
- temporary helper files

This occurs on **any** invocation, including a bare version probe. Contents were never
read, and none are recorded here — only the categories above.

### The distinction that matters

**A runtime-artifact write is not a configuration mutation.** Logs, caches and temp files
are host bookkeeping. Configuration, marketplace registration and plugin installation are
user-meaningful state, and none of those leaked in any experiment.

Conflating the two would mislead in both directions: it would overstate the harm of a log
write, or understate the significance of a real configuration change.

### Requirement going forward

Any future Codex probe must **disclose this limitation before execution**, not after. A
reviewer authorising a probe needs to know that complete isolation is not achievable on
this host.
