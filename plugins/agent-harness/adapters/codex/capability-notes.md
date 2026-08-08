# Codex capability notes

M1 placeholder. Filled in during M4.

Points already known and binding:

- Codex subagents run in parallel and Codex handles orchestration.
- Custom agents are TOML files in project or user scope. They are **not** a documented
  native plugin component, so agent-harness never distributes them through the manifest.
- Skill invocation policy lives in `skills/<name>/agents/openai.yaml`. Setting
  `policy.allow_implicit_invocation: false` removes a Skill from implicit selection while
  leaving explicit `$skill` invocation working.
