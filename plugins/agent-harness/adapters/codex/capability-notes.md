# Codex capability notes

Same labels the Claude notes use, for the same reason: **Observed** means this repository
ran it, **Documented** means the vendor says so and nothing here has exercised it, **Open**
means neither. Blurring them is how a documented capability gets cited later as if a test
had been run.

Observations come from **codex-cli 0.146.0-alpha.9.2**, in an isolated `CODEX_HOME`. An
alpha is not a cross-version contract.

## Packaging

**Observed.** Marketplace registration succeeds and the catalog resolves. Immediately
after, `codex plugin list` reported the plugin **`not installed`** — registration and
installation are separate lifecycle steps, confirmed empirically rather than inferred.

**Observed.** A plugin root containing both `.claude-plugin/` and `.codex-plugin/` was
accepted, and the install cache preserved both manifests and `skills/`. That is the
co-location evidence for this host.

**Observed, and not a general guarantee.** An install-class CLI subcommand existed on
that alpha and worked. It is **not** in the published packaging documentation as the
stable installation path, and running it deviated from M1.2's own protocol (PROC-001).
Recorded, not relied on. `install-surface.md` has the documented route.

**Observed — DEF-001.** Registration *rejected* our generated catalog when it carried
`policy.authentication: "none"`. An invented field value, caught by a real host. Fixed at
the source; the schemas now carry only documented values.

**No official validator.** `codex plugin --help` lists `add`, `list`, `marketplace`,
`remove`. None was invented; local schemas do the checking, and passing them is not
evidence the host agrees.

## Skills

**Open — E6.** Skill *discovery* on this host is **Not Run**. There is no `skill`
subcommand to ask, and `codex exec` would invoke a paid model. Registration and cache
preservation say the files arrive; nothing yet says the host offers them.

**Documented.** Explicit invocation is `$name` in Codex and IDEs, `@name` in ChatGPT.

## Invocation policy — Codex has Gate A, and Claude does not

**Documented.** `skills/<name>/agents/openai.yaml` supports
`policy.allow_implicit_invocation`. Setting it `false` stops the model selecting that
Skill on its own while explicit `$name` invocation keeps working.

**This is the asymmetry running the other way.** Claude Code enforces role permissions
through a tools allowlist and has no invocation gate; Codex has the invocation gate and no
tool-level role enforcement. Neither host dominates, and a document that presented one as
the weaker one throughout would be wrong in whichever direction it picked.

Gate B — the approval a Skill body requires before changing anything — has to hold on both
regardless, which is why it was written to work with no host policy at all.

## Roles

**Documented.** Custom agents are TOML files in `.codex/agents/` or `~/.codex/agents/`.
The plugin package format does **not** define them as a native component, so agent-harness
never distributes them through the manifest. `agent-templates/` holds optional copies, and
nothing installs them.

**Documented.** Codex runs subagents in parallel and handles that orchestration itself.

## Paths

**Documented.** `PLUGIN_ROOT` and `PLUGIN_DATA` are provided to plugin **hooks**, and
`CLAUDE_PLUGIN_ROOT`/`CLAUDE_PLUGIN_DATA` are supplied to Codex hooks for compatibility.

**Open.** Nothing documents them as available to a command a *Skill* starts. Hook
evidence must not be reused as Skill evidence — `path-resolution.md`, Q-IMPL-003.

## Still open

| ID | Question |
| :--- | :--- |
| Q-IMPL-002 | Does Codex ignore or reject unknown `SKILL.md` frontmatter keys? |
| Q-IMPL-003 | How does a canonical Skill locate a bundled script? |
| Q-IMPL-004 | Private-repository authentication |
| E6 | Skill discovery and invocation on this host |
