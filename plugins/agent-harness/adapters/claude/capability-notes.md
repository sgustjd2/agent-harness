# Claude Code capability notes

What this host does, and how each claim is known. **Documented capability and observed
behaviour are different things**, and a note that blurs them is worse than no note: it
gets cited later as if a test had been run.

| Label | Meaning |
| :--- | :--- |
| **Observed** | this repository ran it against a real host and recorded the result |
| **Documented** | the vendor documents it; nothing here has exercised it |
| **Open** | neither — a question with no answer yet |

Observations below come from Claude Code **2.1.195**. A single version is not a
cross-version contract.

## Components

**Observed.** The host reports a per-plugin component inventory. During M1.4A it read
Skills 1, Agents 0, Hooks 0, MCP 0, LSP 0 — from a plugin root that also contained a
`.codex-plugin/` manifest, which is the co-location evidence.

That inventory is the cheapest post-install check available, and M3 changed what it
should say: **Agents must now read 6.** A lower number means the role definitions did not
load, and it is visible without invoking a model.

**Observed.** Session-scoped loading from a directory path works, including a path
containing spaces, and creates no installed record. Marketplace installation is
**Open** — validation passing is not installation succeeding.

## Role subagents

**Documented.** Plugin subagents support `name`, `description` and `tools`. They do not
support `hooks`, `mcpServers` or `permissionMode`.

The consequence is the whole shape of `../../agents/`: **the tools allowlist is the only
permission surface this host offers a plugin subagent.** Nothing else in the frontmatter
constrains anything, so a role's limits are either expressible as a set of tools or they
are prose in the body.

**Open — Q-IMPL-007.** Whether the host refuses a tool outside the list at runtime. The
allowlist's *expressiveness* is settled by construction and recorded in
`docs/compatibility.md`; its *enforcement* needs a write-attempt test on a live host.

## Agent Teams

**Documented.** Experimental, off unless the user enables it.

Never depend on it. Prefer it when present, fall back to ordinary subagents, then to
sequential execution — and say in the run's evidence which one actually happened. A run
that quietly degrades teaches nobody that the capability was missing.

## Invocation policy — there is no Gate A here

**Open.** Claude Code has no invocation-policy gate in this plugin.

`disable-model-invocation` cannot go into the canonical frontmatter while Codex's
behaviour on unknown keys is unresolved (Q-IMPL-002), and the canonical layer is one file
serving both hosts. So on Claude Code, **Gate B — the approval a Skill body requires
before it changes anything — is the only defence** (THR-022).

Gate B was written to hold on a host with no invocation policy at all, which is why this
is a documented weakness rather than a hole. A Claude-side Gate A strategy would belong
in this directory, and none is adopted.

## Paths

**Documented.** `${CLAUDE_PLUGIN_ROOT}` exists, and plugin `bin/` executables can be put
on the Bash tool's PATH. **Runtime Not Run** — inspecting a string is not executing one.

Neither may appear in the canonical layer under any circumstances (FR-027-B). If a path
variable is ever used, it is used here. See `path-resolution.md`.
