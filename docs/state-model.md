# Portable state model

**M1 placeholder.** Written in M5.

Will document `.agent-harness/` in operational terms.

The schemas already exist and are validated in CI:
`plugins/agent-harness/core/schemas/`.

Two defaults worth stating early: reviewed memory files are committed; run evidence and
proposals are local-only. Declaring a run complete never requires committing raw evidence.
