# Claude Code capability notes

M1 placeholder. Filled in during M3.

Points already known and binding:

- Agent Teams is experimental and disabled by default. It must not be a hard dependency;
  prefer it when present, fall back to ordinary subagents, then to sequential execution.
- Plugin subagents do not support `hooks`, `mcpServers` or `permissionMode` frontmatter.
  Role permission constraints have to be expressed through the `tools` allowlist.
- Claude Code has **no Gate A** today, because `disable-model-invocation` cannot go in the
  canonical frontmatter while Codex behaviour on unknown keys is unresolved. Gate B is the
  sole defence on this host until an adapter strategy lands (THR-022).
