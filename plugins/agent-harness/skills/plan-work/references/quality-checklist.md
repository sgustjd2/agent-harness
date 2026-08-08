# Plan quality checklist

Run this before returning a plan. Any "no" is a reason to fix the plan, not a reason to
add a caveat to it.

## Objective and boundaries

- [ ] The objective states an **observable** end state, not an activity.
- [ ] Scope is explicit.
- [ ] Non-goals are explicit and specific enough to refuse work later.

## Honesty about what is known

- [ ] Every assumption is written in the assumptions section, not buried in a task.
- [ ] Each assumption says what changes if it turns out to be wrong.
- [ ] Known facts cite a path or the user's own words.
- [ ] Blockers and decisions needed are **separate** from assumptions. An assumption
      lets work proceed; a blocker does not. Merging them hides the difference.

## Tasks

- [ ] Every task has a completion condition someone else could check.
- [ ] No task's completion condition is "it works" or "it is done".
- [ ] Every task has a recommended role and a one-line reason.
- [ ] No file-writing task is assigned to `researcher` or `reviewer`.
- [ ] Expected files are listed, with uncertain ones marked as assumptions.

## Ordering

- [ ] Dependencies are listed per task and the order is derivable from them.
- [ ] There are no dependency cycles.
- [ ] Tasks claimed to be parallel neither depend on each other nor write the same
      files, and the write sets are listed so the claim can be checked.

## Acceptance and verification

- [ ] Acceptance criteria are testable by someone who did not write the plan.
- [ ] Each acceptance criterion is a single condition, not a paragraph of several.
- [ ] Every verification item has a gate, a proposed command or inspection, an expected
      result, and what a failure would mean.
- [ ] Every verification item's status is `Not Run`.
- [ ] Commands are labelled **proposed**, and nothing in the plan implies one was run.

## Risk

- [ ] Every risk has a mitigation, or an explicit statement that it is accepted
      untreated.
- [ ] Irreversible steps are named in the rollback section.

## The claim check

- [ ] The plan nowhere states that a task, acceptance criterion, or verification gate
      passed, succeeded, or completed — unless the user supplied actual evidence in
      this conversation.

This last one is the one that matters most. A plan is written before the work, so it
has nothing to report; every success it appears to describe is either a prediction
worded as a fact or a gate that was never run.
