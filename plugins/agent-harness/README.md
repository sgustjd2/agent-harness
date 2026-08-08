# agent-harness (installable plugin)

This directory is what gets installed. It is **self-contained**: no file here references
anything outside it.

## Layout

```
.claude-plugin/plugin.json      Claude Code manifest
.codex-plugin/plugin.json       Codex manifest, "skills": "./skills/"
skills/m1-discovery-fixture/    compatibility fixture -- does nothing, by design
skills/plan-work/               production Skill (experimental), read-only
skills/init-project/            production Skill (experimental), approval-gated
skills/verify-work/             production Skill (experimental), bounded execution
skills/doctor/                  production Skill (experimental), read-only diagnostics
core/schemas/                   five packaging schemas
core/schemas/state/             state schemas -- NOT packaging evidence
adapters/claude/                Claude integration
adapters/codex/                 Codex integration + experiment records
templates/                      files init-project will copy, from M5
```

Both manifests point at the same physical `skills/` directory. That is the design: one
workflow layer, two thin adapters.

## Skills in this plugin

| Skill | Kind | State |
| :--- | :--- | :--- |
| `m1-discovery-fixture` | compatibility fixture | inert by design -- **not** a product Skill |
| `plan-work` | production | **experimental**, read-only |
| `init-project` | production | **experimental**, approval-gated mutation |
| `verify-work` | production | **experimental**, bounded command execution |
| `doctor` | production | **experimental**, read-only harness diagnostics |

**No other production Skill is implemented.** `orchestrate`, `refine-harness` and
`apply-refinement` are planned, and
`validate_skills.py` rejects any of those names appearing here until each is actually
built. A shipped `SKILL.md` is host-discoverable whatever its body says, so a
placeholder would be a product surface with nothing behind it.

### `m1-discovery-fixture`

Exists so the hosts have something to discover during experiment ATS-018, and does
nothing else. It carries `agents/openai.yaml` with implicit invocation **disabled**,
which also demonstrates that the policy file travels inside the Skill directory through
packaging and copy.

### `plan-work`

Turns a goal into a plan: tasks with completion conditions, dependency order,
acceptance criteria, and a verification plan that starts at `Not Run`.

**Read-only.** It writes no source, changes no configuration, runs no command, and
spawns no agent. It creates a file only when the user explicitly asks it to save a
plan, and then only `.agent-harness/runs/<run-id>/plan.md`.

Its body declares a machine-checkable safety contract in an `agent-harness:policy`
marker, which `validate_skills.py` parses as YAML. That is deliberate: a read-only
Skill's prose legitimately contains sentences like "never run the tests", and a
substring scan cannot tell a promise from a violation. The marker is the claim; the
prose is for the reader.

Implicit invocation is **enabled** here, unlike the fixture. Both follow the same rule
applied to different Skills -- reachability should match side effects. A model choosing
`plan-work` for "plan this feature" costs the user a document, not a change to their
repository.

## Constraints binding everything here

- No file may reference a path outside this directory.
- No *unimplemented* production Skill name (`orchestrate`, `refine-harness`,
  `apply-refinement`) may appear as a directory here. The allowlist widens one
  Skill at a time, as each is implemented.
- No `scripts/`, `assets/` or dependency manifest inside any Skill: Skills are
  instruction-only, so there is nothing to execute and nothing to install.
- No `agents/`, `hooks/`, `workflows/`, `monitors/`, `scripts/`, `.mcp.json`,
  `.app.json`, `.lsp.json` or `settings.json`.
- Canonical Skills assume no host path variable, no installation cache path, no
  `PLUGIN_ROOT`, and no working directory.
- Skill frontmatter is `name` + `description` only.
- Nothing writes to user-scope configuration.
- No hooks. No network access. No telemetry. No third-party dependency.

### `init-project`

Creates the `.agent-harness/` structure in a repository and links it to the host
instruction file.

**Approval-gated, not read-only.** It works in two phases: inspect and propose, then
apply only what the user approved for that specific proposal. Explicit invocation is not
mutation approval — the two gates are independent, which is why implicit invocation is
**disabled** here while `plan-work` leaves it on.

Its declared write surface is the whole of what it may touch:

| Root | Access |
| :--- | :--- |
| `.agent-harness/` | create |
| `CLAUDE.md`, `AGENTS.md` | the **managed-marker-block** only; everything outside it is immutable |

**The managed-marker-block.** `<!-- BEGIN agent-harness -->` … `<!-- END agent-harness -->`
is the single owned region inside a file the user owns. With no block present, exactly
one is appended at the end; with one present, only its inner content is replaced, and
only when that content would change. Markers that are malformed, nested, duplicated or
unmatched are a **conflict** — reported, never resolved by guessing. This is not
"append-only", because the block's own contents may legitimately be replaced.

**Rollback is bounded by ownership.** Nothing that existed before a Phase B attempt is
ever deleted or restored. A failed attempt may make a best-effort withdrawal of the
exact files and block content *that attempt* created, and nothing else. If it cannot
finish, it reports the remaining partial state and the manual cleanup steps — and does
not call the result initialized.

It never overwrites an existing non-empty file, never touches `.git/`,
never writes to user scope (`~/.claude/`, `~/.codex/`, `~/.agents/`), and never executes
the verification commands it detects — detection is a hypothesis that a tool exists, and
running it to find out is precisely the side effect this Skill must not have.

Re-running against an initialized repository produces no diff.

### `verify-work`

Runs the project's configured verification gates and reports what happened.

**Bounded command execution.** It is the only Skill that runs a subprocess, and every
other rule is a limit on that: only gates already written into
`.agent-harness/config.yaml`, only after approval tied to the exact gate set shown, only
as argv arrays, only inside the repository, each with a required timeout, sequentially.

It never guesses a command. Reading `package.json` or a Makefile and running what it
finds is `init-project`'s proposal step, and even there the output only becomes runnable
once a human writes it into the configuration. No configured gate means `Blocked`, never
a fallback guess.

`read_only: false` in its contract means only that subprocesses run. It grants no
authority to edit anything — `modifies_source` and `modifies_config` stay false, and the
Skill has no write surface at all. This milestone writes no evidence file; results come
back in the response.

### `doctor`

Diagnoses **agent-harness itself** — installation, environment, and project state — and
says what to do about anything broken.

**`doctor` diagnoses the harness; `verify-work` verifies your code.** Both "check things",
and that is the easiest confusion to fall into. "Do my tests pass" is `verify-work`, and
it needs configured gates plus execution approval. "Why isn't this working at all" is
`doctor`.

Every check reports `ok`, `warn`, `fail` or `unknown`. It never stops on a failure —
every applicable check still gets a status — and a complete run means everything was
judged, not that everything was fine. `unknown` is never upgraded to `fail`, and never
hidden to reach a green report.

**Read-only, and it runs nothing.** No gate, no `--version`, no `command -v` / `which` /
`where`. It reuses the existing `read-only` profile unchanged, so an executable whose
availability cannot be established statically is reported `unknown` rather than probed.
It repairs nothing: a corrupt config or memory file is a finding, not permission to fix
it. Remediation commands are printed as suggestions and never executed.

### How the four production Skills are checked

All three declare an `agent-harness:policy` marker, but against **different safety
profiles**: `plan-work` and `doctor` are `read-only`, `init-project` is
`approval-gated-mutation`, `verify-work` is `bounded-verification`. One flattened table
would let a Skill that writes files claim it does not.

`doctor` reusing `read-only` unchanged is the point of having profiles: a diagnostic that
needed the profile widened to fit would not have been a diagnostic.

`executes_commands` used to be a universal guarantee. It stopped being one the moment a
verification Skill existed, so it moved into the individual profiles. Keeping it
universal with an override would have been worse: a guarantee with an exception is a
default wearing the wrong name. `network_access: false` remains genuinely universal, and
a test asserts that exactly one profile may execute — so no future Skill acquires that
power by inheriting it.
