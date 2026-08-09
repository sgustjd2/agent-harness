# Rollback contract

How a change is made undoable, and what happens when it has to be undone.

## Recorded before the first write

**No rollback information means no application.** An irreversible change is not a
refinement.

| Project | Recorded |
| :--- | :--- |
| Git repository | the current `HEAD` revision, plus the list of target paths |
| No repository | a copy of every target's original content in `.agent-harness/proposals/<proposal-id>.backup/` |

Both go into the proposal's `rollback` field.

**Order matters:** this is recorded *before* the first write, not after. Rollback
information captured afterwards describes the state the change already produced, which is
the one state nobody needs to get back to.

## Reverting

Verification failure means **revert everything this application wrote** — every target,
not just the one that failed a gate — then record `status: failed` with the failing gate
named.

Partial application is not a state to leave behind: half a proposal is a configuration
nobody reviewed and nobody intended.

## If reverting itself fails

**Stop and report the exact partial state**: which targets were restored, which were not,
what their current condition is, and the precise manual steps to finish.

Do not retry silently, do not approximate, and **do not report success**. A failed revert
is the one situation where the user must know exactly what is on disk, so guessing is
worse than admitting the boundary.

## Presenting the revert command

Present the revert command to the user. **Do not run Git.**

The plugin does not execute version-control mutations — an automatic `git checkout` or
`git reset` could discard work the user had in progress alongside the applied change, and
the plugin has no way to know what else is uncommitted.

## After a successful revert

`status: reverted`, and the proposal file is **kept**. Both `rejected` and `reverted`
proposals are preserved: they record a decision that was made, and deleting them would
erase why the current state is the way it is.

## Never

- Never apply without recorded rollback information.
- Never delete a backup directory as part of applying or reverting.
- Never report `applied` while any change remains unreverted.
- Never report success when verification failed.
- Never treat a revert as undoing the *approval* — a reverted proposal returns to a
  reviewable state, not to an approved one.
