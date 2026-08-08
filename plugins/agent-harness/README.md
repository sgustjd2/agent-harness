# agent-harness (installable plugin)

This directory is what gets installed. It is **self-contained**: no file here references
anything outside it.

## Layout

```
.claude-plugin/plugin.json      Claude Code manifest
.codex-plugin/plugin.json       Codex manifest, "skills": "./skills/"
skills/m1-discovery-fixture/    the ONLY Skill here during M1
core/schemas/                   five packaging schemas
core/schemas/state/             state schemas -- NOT packaging evidence
adapters/claude/                Claude integration
adapters/codex/                 Codex integration + experiment records
templates/                      files init-project will copy, from M5
```

Both manifests point at the same physical `skills/` directory. That is the design: one
workflow layer, two thin adapters.

## M1 status

**There are no production Skills here, and none may be added until M2.**

`skills/m1-discovery-fixture/` is a compatibility fixture. It exists so the hosts have
something to discover during experiment ATS-018, and it does nothing by design. It
carries `agents/openai.yaml` with implicit invocation disabled, which also demonstrates
that the policy file travels inside the Skill directory through packaging and copy.

## Constraints binding everything here

- No file may reference a path outside this directory.
- No production Skill name (`init-project`, `plan-work`, `orchestrate`, `verify-work`,
  `refine-harness`, `apply-refinement`, `doctor`) may appear as a directory here.
- No `agents/`, `hooks/`, `workflows/`, `monitors/`, `scripts/`, `.mcp.json`,
  `.app.json`, `.lsp.json` or `settings.json`.
- Canonical Skills assume no host path variable, no installation cache path, no
  `PLUGIN_ROOT`, and no working directory.
- Skill frontmatter is `name` + `description` only.
- Nothing writes to user-scope configuration.
- No hooks. No network access. No telemetry. No third-party dependency.
