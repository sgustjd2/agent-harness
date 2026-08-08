# AGENTS.md marker block template

M1 placeholder. Written in M4.

The block inserted into a project's `AGENTS.md` must:

- be delimited by `<!-- BEGIN agent-harness -->` / `<!-- END agent-harness -->`
- stay **at or below 2 KiB**. Codex concatenates `AGENTS.md` from the git root down to the
  working directory under a byte cap, so every byte spent here is taken from the project's
  own instructions
- contain only invocation pointers and a summary of the `.agent-harness/` layout
- contain **no workflow prose** and **no copy of memory contents** -- point at the paths
