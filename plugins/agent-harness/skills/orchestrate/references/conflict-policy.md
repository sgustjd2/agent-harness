# Conflict policy

Three different collisions, detected at three different moments, with three different
answers. None of them is an automatic merge.

## Before anything — is the planned path even safe?

Ahead of every comparison below, each `reads[]` and `writes[]` entry is interpreted
relative to the repository root and **normalized**, and is rejected if it escapes the
repository by traversal, by being absolute, or through symlink resolution.
**Being listed in `writes[]` is not permission to leave the repository.**

An unsafe planned path means the task is **`blocked`** and not delegated; the path is
reported and the plan is never rewritten to make it pass.

Every check that follows uses the normalized, contained form — raw strings would let two
spellings of the same path miss each other.

`.agent-harness/**` is **read-only** to `orchestrate`: a task planning to write there is
`blocked`, because config, memory, and run artifacts each have their own approval path.

## Before delegation — overlapping planned writes

Intersect the `writes[]` sets of the tasks selected for this round. **Any overlap means
those tasks are reclassified to sequential execution** — they do not run concurrently.

This is the cheapest of the three checks and the only one that prevents the problem rather
than reporting it. The plan already declares who writes what, so the overlap is knowable
before a single agent starts.

## After delegation — the same file in two results

If two completed results both list the same path in `changed_files` despite the preflight
check:

1. **Do not merge them automatically.**
2. Hold the later result.
3. Report: the conflicting task IDs, the path, the first result, the later result, and a
   recommended resolution.
4. Require a human or coordinator decision before either is treated as accepted.

**There is no automatic conflict merge in this milestone.** An automatic merge of two
agents' edits produces a file neither agent verified and no human reviewed — and it does
so at exactly the moment the plan's assumptions have already been shown wrong.

## After delegation — a path outside the plan

If a result's `changed_files` contains a path outside that task's `writes[]`:

- the task is **not** `done` — report a **scope violation**
- **do not silently keep** the out-of-scope change as accepted work
- **do not auto-revert** unless an approved rollback contract already exists
- **never expand the plan to justify the file that appeared**

That last one matters most. Widening `writes[]` after the fact makes every future scope
check pass by construction, and converts the plan from a constraint into a record of
whatever happened.

## Destructive actions

Explicit invocation authorises ordinary planned work. It does **not** authorise these,
which need separate approval **immediately before** the action:

- force push
- destructive file-tree deletion
- migration execution
- destructive database operations
- rewriting remote history
- weakening a permission or sandbox

Without approval: do not perform it, mark the task **blocked**, record why, and continue
independent safe tasks. Approval is asked at the point of action, not collected up front —
an approval given before the run cannot refer to a situation that had not happened yet.

Never bypass or weaken the host's own permission model to make an action possible.

## Failure isolation

A failed task does not stop the run. Its dependents become `skipped` with the failing task
recorded; unrelated branches continue.

Report blockers, scope violations and conflicts as their own sections — never folded into
a summary that reads like success. **Partial success is not completion.**
