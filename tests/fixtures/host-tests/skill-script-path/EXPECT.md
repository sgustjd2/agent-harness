# Experiment B fixture — expected behaviour

Manual host test (ATS-020). Not collected by CI.

Candidates, in order: Skill-directory-relative path with no cwd assumption; a
host-provided path variable; whether `PLUGIN_ROOT` is inherited into Skill-started
commands; a project-local launcher installed only after explicit approval.

Record host name, host version, and `verified` / `not-verified` / `not-applicable`
per candidate in `plugins/agent-harness/adapters/<host>/path-resolution.md`.

Static inspection is not a result. Only an actual execution counts as `verified`.
