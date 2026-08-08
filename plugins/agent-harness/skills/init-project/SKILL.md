---
name: init-project
description: >-
  Initialize agent-harness in a repository. Use when asked to set up this repository for
  agent-harness, create the .agent-harness project structure, configure project
  verification gates, prepare portable project memory, or add agent-harness to an
  existing repository. Inspects the project, proposes every file it would create, and
  writes nothing until you approve that specific proposal. It never overwrites existing
  content and never runs the verification commands it detects.
---

# init-project

Create the `.agent-harness/` structure in a repository and link it to the host
instruction file — after showing exactly what will be written and getting approval for
that specific list.

**This Skill writes files. That is why it asks first.** Invoking it is a request to
*inspect and propose*, never a licence to write.

## Safety contract

<!-- agent-harness:policy
read_only: false
requires_explicit_invocation: true
requires_mutation_approval: true
executes_commands: false
network_access: false
installs_packages: false
modifies_user_settings: false
overwrites_existing_files: false
idempotent: true
deletes_preexisting_content: false
may_rollback_current_attempt: true
allowed_path_roots:
  - .agent-harness/
  - CLAUDE.md
  - AGENTS.md
-->

Those three roots are the entire write surface. In `CLAUDE.md` and `AGENTS.md` the only
writable region is the **managed-marker-block**; everything outside it is immutable.

## Two phases, always

### Phase A — inspect and propose

Read only. No file is created, modified, or deleted; no command is executed.

1. Determine whether this is a Git repository. If it is not, continue but record
   `vcs: none` in the proposed config and say plainly that rollback will be manual.
2. Read what is already there: `AGENTS.md`, `CLAUDE.md`, `README`, `pyproject.toml`,
   `package.json`, lockfiles, test and lint configuration, and any existing
   `.agent-harness/` directory.
3. Infer project type **conservatively**. A test directory suggests Python tests; it
   does not prove a runner is installed. Detection is a hypothesis, not a fact.
4. Classify every target path as **create**, **unchanged**, **append**, or **conflict**.
5. Propose verification gates from what was detected. Every gate is proposed
   `enabled: false` until the user says otherwise.
6. Present the full report (below) and ask for approval.

### Phase B — apply, only with approval

1. **Require explicit confirmation tied to this proposal.** "Yes, apply the 7 files
   listed above" is approval. Having invoked the Skill is not, and neither is a general
   "go ahead" given before the proposal was shown.
2. **Re-check every target immediately before writing.** The repository may have changed
   since Phase A — a file that was absent may now exist.
3. If anything material changed since the proposal, **stop**. Report the drift and
   re-propose. An approval refers to the state it was shown for; stale approval is not
   approval.
4. Create only approved paths. Never overwrite an existing non-empty file. Never merge
   conflicting configuration silently.
5. Report every path as created, unchanged, skipped, conflicted, or failed.

## Failure and rollback

**Partial initialization is a defect.** When Phase B fails partway, the boundary is
what the *current attempt* created — not what was already there.

1. **Never delete or restore any file or content that existed before this Phase B
   attempt.** Pre-existing user content is out of scope for cleanup, always. If a file
   was there when the attempt started, the attempt does not remove it, truncate it, or
   revert it to an earlier version.
2. **A best-effort rollback may withdraw only what this attempt created**: the exact
   files it wrote, and the exact managed-marker-block content it inserted. Nothing else.
3. **If complete rollback is impossible**, stop and report the remaining partial state —
   naming each file and block that survives — together with the exact manual cleanup
   steps to finish it.
4. **Never report initialization as successful while partial state remains.** A run that
   left files behind and could not withdraw them did not succeed; say so plainly and
   list what is there.

"Nothing is ever deleted" and "clean up after a failed attempt" only look like a
contradiction. The line is ownership: an attempt may withdraw its own writes, and may
never touch what it found.

## What gets created

| Path | Content |
| :--- | :--- |
| `.agent-harness/config.yaml` | project configuration; see `references/config-template.yaml` |
| `.agent-harness/memory/facts.md` | durable project facts |
| `.agent-harness/memory/decisions.md` | decisions and their rationale |
| `.agent-harness/memory/patterns.md` | reusable procedures |
| `.agent-harness/runs/.gitkeep` | run artifacts live here; local by default |
| `.agent-harness/proposals/.gitkeep` | refinement proposals; local by default |
| `.agent-harness/.gitignore` | exactly four lines: `runs/`, `proposals/`, `*.tmp`, `.migration-backup/` |

Memory files and `config.yaml` are meant to be **committed** — they are the portable
part. Run evidence and proposals stay local, which is what the `.agent-harness/.gitignore`
achieves without touching the repository's own ignore file.

If the user sets `runs.commit_evidence: true`, drop `runs/` from that ignore file and
tell them the tradeoff: run output is the most likely place for something sensitive to
end up in history.

## Host instruction file — the managed-marker-block

`CLAUDE.md` (Claude Code) and `AGENTS.md` (Codex) are **not** generally editable. The
only region this Skill may write is the **managed-marker-block**, delimited exactly:

`<!-- BEGIN agent-harness -->` … `<!-- END agent-harness -->`

**All content outside that block is immutable** — never rewritten, reordered,
reformatted, or removed. This is not "append-only", because the block's own contents may
legitimately be replaced; it is a single owned region inside a file the user owns.

| Situation | Action |
| :--- | :--- |
| no block exists | append **one** block at the end of the file |
| exactly one block exists | replace **only the content inside it**, and only when that content would actually change |
| malformed, nested, duplicated, or unmatched markers | **conflict** — report it, change nothing |

Never create a second block. If a `BEGIN` has no matching `END`, the markers are nested,
or more than one block is present, the file's ownership is ambiguous — resolving it by
guessing risks destroying user content, so report the conflict and leave the file alone.

Creating a missing `CLAUDE.md` or `AGENTS.md` remains allowed, following the host rule
above: Claude Code gets `CLAUDE.md`, Codex gets `AGENTS.md`, and if both files exist both
receive the same block.

Keep the block **under 2 KiB**. Codex concatenates `AGENTS.md` files from the Git root
down, against a byte budget; a large block spends someone else's budget.

The block holds invocation guidance and a summary of the `.agent-harness/` layout —
**not** the workflow itself. Duplicating Skill bodies into an instruction file creates a
second copy that drifts.

## Verification gates

Detection **proposes**; it never enables. Present each candidate with:

| Field | Note |
| :--- | :--- |
| gate id | kebab-case, e.g. `py-test` |
| purpose | what failing it would tell you |
| proposed command | an **argv array**, never a shell string |
| working directory | usually the repository root |
| required | whether completion should be blocked by it |
| timeout | a placeholder for the user to set |
| evidence policy | what gets recorded when it runs |
| status | `Not Run` |

Only `id`, `kind`, `command`, `required`, `timeout_seconds` and optionally
`working_dir` belong in `config.yaml` — the rest are for the human reading the proposal.

Commands are argv arrays because a shell string invites quoting and injection problems
that an array cannot have.

**Nothing here is executed by this Skill.** A detected command is a guess that a tool
exists; running it to find out is exactly the side effect this Skill must not have.

## Idempotency

Re-running against an initialized repository must produce no diff.

- A file that exists and is valid is reported **unchanged**, not rewritten.
- Only missing approved files are created.
- Sections are never duplicated; managed-marker-blocks are never stacked.
- User content is never reset, and no pre-existing file or content is ever deleted. The
  single exception is narrow and stated above: a failed Phase B attempt may withdraw the
  files and block content **that same attempt** created.

The check is simple: run it twice, and the second run creates nothing.

## Never

Application source, build configuration, package manifests, CI workflows, plugin
manifests, marketplace catalogs, Git remotes, branches, commits, or `.git/` in any form.
Never write to user scope — `~/.claude/`, `~/.codex/`, `~/.agents/` — under any
circumstance. Never install a package, register a marketplace, install a plugin, copy
agent templates, or reach the network.

## Output report

Report in this order: repository assessment; existing agent-harness state; proposed
files (path, action, reason, overwrite risk, approval required); proposed configuration;
proposed verification gates; Git ignore changes; conflicts; assumptions; and an explicit
approval request naming the exact file count.

After approval, report the result as **created / unchanged / skipped / conflicted /
failed**. If anything failed, the initialization did not succeed — say so directly
rather than reporting success with a footnote.

## References

- `references/config-template.yaml` — the configuration to propose
- `references/initialization-checklist.md` — the check to run before and after applying
