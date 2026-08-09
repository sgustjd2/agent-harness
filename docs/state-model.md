# Portable state model

Everything agent-harness knows about your project is a text file under
`.agent-harness/`, in your repository. There is no database, no daemon, no cache
elsewhere on your machine, and nothing on a server.

That is the whole design. State you can read is state you can review, diff, correct and
delete — and state that survives switching hosts, because neither host owns it.

## The layout

```
.agent-harness/
  config.yaml                     gates and settings          committed
  memory/facts.md                 what is true                committed after review
  memory/decisions.md             why it was chosen           committed after review
  memory/patterns.md              how it is done              committed after review
  runs/<run-id>/plan.md           what was planned            local only
  runs/<run-id>/evidence.md       what happened               local only
  runs/<run-id>/result.md         how it ended                local only
  proposals/<proposal-id>.md      what could change           local only
  .gitignore                      keeps the local half local
```

`init-project` creates all of it, after showing you the list.

## Committed, or local

The split is not about tidiness. **Memory is the product; evidence is the exhaust.**

| Committed after review | Local only |
| :--- | :--- |
| `config.yaml` | `runs/**` |
| `memory/*.md` | `proposals/**` |

Memory and config are shared because a team that does not share them is running three
different harnesses. Runs and proposals stay local because they quote raw command
output — redacted, bounded, and still the likeliest place for something sensitive to
reach a permanent history (THR-002).

**"After review" is literal.** The plugin never runs `git add` or `git commit`. A memory
change arrives as an edit you read like any other diff.

Proposals are local for a reason worth stating: a proposal quotes the same evidence a run
produced, so it has the same leakage surface. **The audit trail is the Git history of
what was actually applied** — not a folder of drafts, most of which were never accepted.

**Completing a run never requires committing evidence.** Completion requires that the
evidence *exist*, not that it be published.

## Run artifacts

Three files per run, under `.agent-harness/runs/<run-id>/`, written by three different
Skills with three different immutability rules. The differences are the point.

| File | Written by | Rule |
| :--- | :--- | :--- |
| `plan.md` | `plan-work` | immutable except `state` |
| `evidence.md` | `orchestrate`, `verify-work` | **append-only** |
| `result.md` | whichever Skill ends the run | written once, in every terminal state |

**Append-only means a correction is a new entry.** Not an edit. An evidence file that can
be revised after someone has read it is a file whose history nobody can trust, and writing
things down was supposed to stop results being restated from memory.

**A plan is not a to-do list you tick off.** Its `state` moves; its content does not.
Changing the plan means a new run, so that what was planned and what happened stay
separately readable afterwards.

**`result.md` is written even when the run failed, blocked, or was cancelled.** A run with
no result file is indistinguishable from a run that never started.

### This turned on in M5

Through M4, `orchestrate` and `verify-work` returned evidence in the response and wrote
nothing. Each deferral was reasonable on its own, and together they left `refine-harness`
and `apply-refinement` with no reachable input — they read run artifacts that nothing
produced. A contract dry-run found it (**D-01**); no test did, because every Skill is
validated in isolation.

Worth keeping in mind when reading anything below: **the union of verified parts is not a
verified whole.**

## Run ids

`YYYYMMDD-HHMMSS-<slug>`. Sortable, unique in practice, and readable without a lookup.

Two writers hitting one run directory is unlikely rather than impossible, so a Skill that
finds the directory already there mints a new id instead of merging into it. The MVP
assumes **a single writer** and says so; file locking is deferred, because cross-platform
locking behaves differently on Windows and POSIX and the assumption has held.

Several people in one repository is a different question, and Git already answers it. The
state is Markdown, so a conflict arrives in a form a human can read.

## What memory is allowed to hold

An entry earns its place by being all seven of: concise (1–3 sentences, ≤ 400 characters),
reusable, project-specific, evidence-backed with at least one source, free of secrets,
free of raw environment values — variable *names* are fine — and reviewed by a person
before it is committed.

The exclusions do more work than the inclusions:

- **Nothing time-varying.** Branch names, progress, current assignees. A fact that expires
  is a fact that will be wrong before anyone notices.
- **Nothing generic.** How Python decorators work is true everywhere and belongs nowhere
  here.
- **Nothing unsourced.** No source, no entry.

**Decisions are never deleted.** A reversed decision is marked `superseded` and points at
what replaced it; the new entry points back. Only `active` decisions load into context —
the history stays available for whoever asks why.

**Every memory file says, in its own header, that it is data and not instructions.**
Memory is read back into an agent's context on every later run, so a memory file is a
standing injection surface. The header is what makes it read as evidence rather than as
orders.

## Retention

| | Default | Behaviour |
| :--- | :--- | :--- |
| `runs/` | keep 20 | older runs are **marked**, not removed |
| `memory/` | unlimited | never deleted |
| `proposals/` | unlimited | never deleted; local, so they cost nothing |

**Nothing is deleted automatically unless you set `runs.auto_prune: true`.** Deletion is
irreversible and can quietly destroy an audit trail, which is a bad thing for a default to
do on your behalf.

## Redaction

Applied **before** anything is written, never after: command arrays and output excerpts in
evidence, result bodies, `current`/`proposed` in proposals, and every memory entry.

**Fail-closed.** If a value cannot be established as safe, it is replaced rather than
stored. Storing uncertain text and reviewing later inverts the risk — the file already
exists by then.

Output is bounded too: 200 lines from each end, 64 KiB per excerpt, with the middle marked
as omitted. Truncation is visible, so nobody mistakes a clipped log for a short one.

## Schema versions

Every state file carries `schema_version`, currently `1`.

| Situation | Behaviour |
| :--- | :--- |
| file older than supported | migration is **offered**, never run automatically |
| file newer than supported | **writing stops**; upgrade the plugin |

The second is the one that matters. A newer file means something understands the format
better than this version does, and writing to it anyway risks discarding what it knows.

Migrations keep the original under `.agent-harness/.migration-backup/<timestamp>/`.

## When state is damaged

| Damage | What happens |
| :--- | :--- |
| `config.yaml` will not parse | stop, run `doctor`, restore from Git. **Never rewritten automatically** |
| a memory file breaks its schema | skip that file, warn, record `memory: partial`, keep going |
| `plan.md` missing | `orchestrate` asks for `plan-work`. It does not invent a plan |
| `evidence.md` truncated | read up to the last intact entry and append after it |
| `result.md` missing | the run was interrupted; recovery is offered on the next invocation |
| the whole directory gone | `doctor` says so and points at `init-project` and Git |

The pattern across every row: **degrade, report, and let a human decide.** Regenerating a
config nobody reviewed would replace a visible problem with an invisible one.

## Reading the schemas

The machine-readable definitions live in
[`plugins/agent-harness/core/schemas/state/`](../plugins/agent-harness/core/schemas/state/)
and are validated in CI, so this page cannot drift far from them without something
failing. Where they disagree, the schemas are authoritative and this page is the bug.
