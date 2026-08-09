# Installing agent-harness in Codex / OpenAI surfaces

**M1 placeholder.** Written in M4.

Will cover **three** separate things — see
`plugins/agent-harness/adapters/codex/install-surface.md` for the current record:

1. **Register the marketplace source** (Codex CLI) — `codex plugin marketplace add …`
   After this the host knows the plugin exists. Nothing is installed or enabled.
2. **Install and enable the plugin** (ChatGPT desktop app) — Plugins screen, then restart.
3. **Fallback for environments with no installation surface** — copy
   `plugins/agent-harness/skills/` into `$REPO_ROOT/.agents/skills/`. Costs the plugin
   lifecycle; keeps Gate A, because the policy file travels inside the Skill directory.

The registration section will not claim the plugin is installed, and no CLI install
subcommand will be shown, because none is documented. Whether a CLI-only installation
path exists is an open question — see `docs/compatibility.md`.

**Status.** All seven Skills are implemented as of M2 — they are no longer
placeholders. This installation guide itself is still a draft, to be written in
M4. The verified way to load the plugin today is session-scoped
`--plugin-dir` (Claude); marketplace installation has not been exercised.
