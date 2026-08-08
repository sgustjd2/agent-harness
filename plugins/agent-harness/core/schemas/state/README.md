# State schemas — NOT packaging schemas

These five schemas describe **project state files** under `.agent-harness/`:
`config.yaml`, `plan.md`, `evidence.md`, `result.md`, and refinement proposals.

They are kept in M1 because the PRD explicitly lists them as an M1 deliverable
(§29 item 4: "`core/schemas/`의 `config`/`plan`/`evidence`/`result`/`proposal` 5개 JSON
Schema"). They are held in this subdirectory, separate from the packaging schemas one
level up, for one reason:

> **A state schema is never evidence for plugin or marketplace validation.**

M1 exit criteria E3 and E4 concern the **Codex plugin manifest** and the **Codex
marketplace catalog**. Those are validated by `codex-plugin.schema.json` and
`openai-marketplace.schema.json` in the parent directory. The schemas here validate
runtime state that M1 does not yet produce, and they contribute nothing to E3 or E4.

The state files these describe are written from M5 onward. Nothing in M1 creates one.
