# CLAUDE.md marker block template

M1 placeholder. Written in M3.

The block inserted into a project's `CLAUDE.md` must:

- be delimited by `<!-- BEGIN agent-harness -->` / `<!-- END agent-harness -->`
- contain only invocation pointers and a summary of the `.agent-harness/` layout
- contain **no workflow prose** -- that lives in `skills/` (PRIN-01)
- never overwrite content outside the markers
