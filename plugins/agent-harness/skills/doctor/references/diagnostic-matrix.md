# Diagnostic matrix

Every check `doctor` performs, with the condition that produces each status. Checks that
cannot apply to the current project are reported as not applicable, not as failures.

`unknown` is a real answer everywhere in this table. It is never upgraded to `fail`.

## Environment

| ID | Diagnostic | Applies | `ok` | `warn` | `fail` | `unknown` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| ENV-01 | Host identification | always | host identified from context or readable structure | — | — | identity not safely determinable |
| ENV-02 | Python 3.10+ | always | version established from exposed metadata | present, version below policy | — | present but version needs execution, or not visible |
| ENV-03 | Git repository | always | repository metadata readable | project uses `vcs: none` | — | cannot determine without running Git |

ENV-01 never fails: not knowing which host is executing says nothing about whether the
installation is sound. Co-located manifests prove packaging compatibility, not identity.

## Plugin installation

| ID | Diagnostic | Applies | `ok` | `warn` | `fail` | `unknown` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PKG-01 | Claude manifest | always | `.claude-plugin/plugin.json` present | — | missing | root unresolvable |
| PKG-02 | Codex manifest | always | `.codex-plugin/plugin.json` present | — | missing | root unresolvable |
| PKG-03 | `skills/` directory | always | present | — | missing | root unresolvable |
| PKG-04 | Implemented Skills present | always | `plan-work`, `init-project`, `verify-work`, `doctor` all present | — | any one missing | root unresolvable |
| PKG-05 | Compatibility fixture | always | `m1-discovery-fixture` present | absent | — | root unresolvable |
| PKG-06 | Unimplemented Skills | always | `orchestrate`, `refine-harness`, `apply-refinement` absent — expected | — | — | — |

PKG-06 can only be `ok`. Their absence is the current design, and reporting it as a
problem would send someone looking for a bug that does not exist.

## Skill integrity

| ID | Diagnostic | Applies | `ok` | `warn` | `fail` | `unknown` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| SKL-01 | `SKILL.md` present | per Skill | present | — | missing | unreadable |
| SKL-02 | Frontmatter name matches directory | per Skill | matches | — | mismatched | unparseable |
| SKL-03 | Canonical frontmatter fields only | per Skill | only allowed keys | — | disallowed key present | unparseable |
| SKL-04 | Referenced files exist inside the Skill root | per Skill | all present and contained | — | missing or escaping the root | unreadable |
| SKL-05 | `agents/openai.yaml` parses | when present | parses | — | malformed | unreadable |

## Project state

| ID | Diagnostic | Applies | `ok` | `warn` | `fail` | `unknown` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PRJ-01 | `.agent-harness/` present | always | present | — | **absent — run `init-project`** | path unreadable |
| PRJ-02 | `.agent-harness/.gitignore` present | initialized | present and protects local-only paths | present but incomplete | absent | unreadable |
| PRJ-03 | `runs/` ignored | initialized | ignored | **not ignored** | — | cannot determine |
| PRJ-04 | `runs/`, `proposals/` present | initialized | both present | either missing | — | unreadable |

## Configuration

| ID | Diagnostic | Applies | `ok` | `warn` | `fail` | `unknown` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CFG-01 | `config.yaml` parses | initialized | parses | — | **malformed** | unreadable |
| CFG-02 | `schema_version` present | initialized | present | — | absent | unparseable |
| CFG-03 | `schema_version` supported | initialized | supported (currently `1`) | — | **valid but unsupported — migration required** | undeterminable |
| CFG-04 | Required sections present | initialized | all present | — | any missing | unparseable |
| CFG-05 | `runs.commit_evidence` | initialized | `false` | **`true`** | — | unreadable |
| CFG-06 | Config drift vs committed baseline | Git + baseline readable | no drift | drift detected | — | comparison needs Git execution |

CFG-01 and CFG-03 are `fail` but never auto-repaired: no regeneration, no migration.
CFG-06 being `unknown` is normal and is not a failure.

## Memory

| ID | Diagnostic | Applies | `ok` | `warn` | `fail` | `unknown` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| MEM-01 | `facts.md` integrity | initialized | structurally readable | present but incomplete | corrupt or unparseable | unreadable |
| MEM-02 | `decisions.md` integrity | initialized | structurally readable | present but incomplete | corrupt or unparseable | unreadable |
| MEM-03 | `patterns.md` integrity | initialized | structurally readable | present but incomplete | corrupt or unparseable | unreadable |

Three separate IDs on purpose. One corrupt file must not make the other two unreadable,
and collapsing them into one finding would hide which file needs attention. Structure
only — never a judgement about whether a recorded fact is true.

## Verification executables

| ID | Diagnostic | Applies | `ok` | `warn` | `fail` | `unknown` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| EXE-01 | Gate executable appears available | gates configured | found by static inspection | — | explicit repo-relative path does not exist | cannot establish without executing a lookup |
| EXE-02 | Gate working directory contained | gates configured | inside the repository | — | escapes the repository | unresolvable |

**EXE-01 never runs anything.** No gate, no subset of a gate, no `--version`, no
`command -v` / `which` / `where` / `Get-Command`. `unknown` is the honest and common
answer for a bare executable name, and it is not a failure.

## Host instructions

| ID | Diagnostic | Applies | `ok` | `warn` | `fail` | `unknown` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| HST-01 | Managed marker block | file present | exactly one valid block | no block | **unmatched, duplicated, or nested markers** | unreadable |
| HST-02 | Block parity across `CLAUDE.md` / `AGENTS.md` | both carry a block | contents match | contents differ | — | either unreadable |

HST-01 fails on malformed markers because ownership becomes ambiguous, and resolving that
by guessing risks destroying user content. `doctor` reports it and changes nothing.

## Compatibility (informational)

| ID | Diagnostic | Applies | `ok` | `warn` | `fail` | `unknown` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CMP-01 | `AGENTS.md` accumulated size | Codex context | below 80% of the 32 KiB budget | at or above 80% | — | accumulated size not safely determinable |
| CMP-02 | Claude Agent Teams state | Claude context | informational | — | — | not exposed |
| CMP-03 | Project `.codex/agents/*.toml` | always | present and readable, or absent | unreadable structure | — | not inspectable |
| CMP-04 | User-scope files created by agent-harness | always | none | **any present** | — | home scope not inspectable |
| CMP-05 | Helper path resolvable | always | **`ok` — no helper required by the current Skill set** | — | — | — |

CMP-02 is never a failure: Agent Teams is not a dependency. CMP-05 is `ok` because this
milestone ships no bundled runtime helper — that is not a claim that Q-IMPL-003 is
resolved.
