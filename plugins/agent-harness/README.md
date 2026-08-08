# agent-harness (installable plugin)

This directory is what gets installed. It is **self-contained**: no file here references
anything outside it.

## Layout

```
.claude-plugin/plugin.json      Claude Code manifest
.codex-plugin/plugin.json       Codex manifest, "skills": "./skills/"
skills/m1-discovery-fixture/    compatibility fixture -- does nothing, by design
skills/plan-work/               production Skill (experimental), read-only
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

**No other production Skill is implemented.** `init-project`, `orchestrate`,
`verify-work`, `refine-harness`, `apply-refinement` and `doctor` are planned, and
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
- No *unimplemented* production Skill name (`init-project`, `orchestrate`,
  `verify-work`, `refine-harness`, `apply-refinement`, `doctor`) may appear as a
  directory here. The allowlist widens one Skill at a time, as each is implemented.
- No `scripts/`, `assets/` or dependency manifest inside any Skill: Skills are
  instruction-only, so there is nothing to execute and nothing to install.
- No `agents/`, `hooks/`, `workflows/`, `monitors/`, `scripts/`, `.mcp.json`,
  `.app.json`, `.lsp.json` or `settings.json`.
- Canonical Skills assume no host path variable, no installation cache path, no
  `PLUGIN_ROOT`, and no working directory.
- Skill frontmatter is `name` + `description` only.
- Nothing writes to user-scope configuration.
- No hooks. No network access. No telemetry. No third-party dependency.
