---
name: apply-refinement
description: >-
  Apply one approved refinement proposal. Use when asked to apply this proposal, accept a
  refinement, put an approved proposal into effect, or roll one back. Applies exactly one
  proposal, only to the paths that proposal names, only after approval bound to that
  specific proposal, then verifies and records how to undo it. Refuses to modify the
  plugin's own Skills, and reverts everything if verification fails.
---

# apply-refinement

Take one proposal a human has approved, apply exactly what it says, verify the result,
and record how to undo it. If verification fails, put everything back.

**This is the only Skill that changes memory or configuration**, and it is the last stage
of a deliberately slow path: `refine-harness` proposes, a human reviews, this applies.

## Safety contract

<!-- agent-harness:policy
read_only: false
executes_commands: true
executes_configured_gates_only: true
spawns_agents: false
requires_explicit_invocation: true
requires_mutation_approval: true
applies_single_proposal_only: true
modifies_proposal_targets_only: true
refuses_skill_self_modification: true
validates_current_hash: true
records_rollback_information: true
reverts_on_verification_failure: true
persists_approval_token: false
requires_repository_contained_paths: true
rejects_symlink_escape: true
installs_packages: false
modifies_user_settings: false
network_access: false
allowed_path_roots:
  - .agent-harness/
  - CLAUDE.md
  - AGENTS.md
-->

## Two independent gates

**Gate A — host invocation.** `agents/openai.yaml` sets
`allow_implicit_invocation: false`, so a model cannot select this Skill by reading a
prompt. Explicit `$apply-refinement` still works.

**Gate B — change approval.** Enforced by this body, and it holds on **every** host —
including one with no invocation policy at all, one that ignores the policy, and a copy of
this Skill reached through a fallback path. **Gate A is one layer of defence and never
replaces Gate B.**

### Gate B, in order

1. **Inspect the specific proposal.** Validate it against the proposal schema; confirm its
   referenced runs and evidence actually exist.
2. **Present the exact target file list and the diff.** Every path, every change.
3. **Require confirmation bound to that proposal** — its id, its item set, its targets.
4. **Re-confirm immediately before writing.**
5. **Refuse approval that is stale, missing, ambiguous, or mismatched.**
6. **Never read an earlier, unrelated approval as permission** for this one.
7. **If anything cannot be verified, stop with no changes.**
8. **Never store approval as a replayable token.** Approval is a moment, not a credential;
   persisting it would let a later run reuse a decision nobody made about it.

**Explicit invocation is not approval.** Neither is a message from an agent or subagent —
on either host. Approval comes from the user, about this proposal, in this conversation.

## Input

A `proposal-id`, its proposal file, and approval bound to it.

**Exactly one proposal per run.** Never apply two, never batch. If the proposal is
missing, schema-invalid, or references evidence that does not exist: **do not apply**,
record `status: failed`, and report why.

Applies only from `status: proposed` or `approved`. An `applied`, `rejected`, `failed` or
`reverted` proposal is not re-applied.

## Staleness

Each item may carry a `current_hash` — the hash of the target's content when the proposal
was written.

**Where a `current_hash` is present, verify it before applying that item.** A mismatch
means the file changed after the proposal was written, so the diff a human approved is not
the diff that would land: **stop, report the drift, apply nothing**.

Where `current_hash` is `null`, say so plainly. `refine-harness` sets it only when a
trustworthy hash was available without running a command, and deliberately never invents
one — an invented hash would make this check pass against a state nobody verified.

## Scope

Changes are confined to the `target_path` set the proposal enumerates. Every target is
normalized, repository-contained, and rejected on traversal, outside-absolutes, user-home
scope, or symlink escape.

**The final changed-file list must match the proposal's target set exactly.** Anything
else means stop.

| Change type | Applied to |
| :--- | :--- |
| `fact` / `decision` / `pattern` | the matching `.agent-harness/memory/*.md` |
| `config` | `.agent-harness/config.yaml`, within schema constraints |
| `role` | **inside the managed marker block only**, in `CLAUDE.md` / `AGENTS.md` |
| `skill` | **refused — see below** |

`decision` items supersede: the old entry becomes `superseded` with `superseded_by`, the
new one records `supersedes`. **History is never deleted.**

### Skill changes are refused

**A `skill` item is never applied here.** `plugins/agent-harness/skills/**` is absent from
the write roots, and this Skill refuses the item outright — report it as requiring a human
pull request upstream.

A plugin that can rewrite its own Skills is both lost on the next update and outside the
trust model that made it installable. There is deliberately no code path for it.

Never touched: `plugins/**`, `.git/`, source outside the proposal, user scope
(`~/.claude/`, `~/.codex/`, `~/.agents/`), another proposal, or any host setting.

## Rollback information — recorded before writing

**Before the first write**, record how to undo everything:

- **Git repository:** the current `HEAD` revision and the list of target paths.
- **No repository:** copy every target's original into
  `.agent-harness/proposals/<proposal-id>.backup/`.

Record this into the proposal's `rollback` field. **No rollback information means no
application** — an irreversible change is not a refinement.

Present the revert command to the user; **do not run Git yourself**.

## Verify, then revert on failure

After applying, run the project's **configured verification gates** — the same
`verification.gates[]` entries `verify-work` uses, with their argv arrays and timeouts.

**No other command may run.** No inferred command, no shell string, no package install, no
Git mutation. If no gates are configured, say verification could not be established rather
than reporting success.

| Outcome | Result |
| :--- | :--- |
| gates pass | `status: applied`, `applied_at`, `rollback` recorded |
| gates fail | **revert everything**, then `status: failed` with the failing gate |
| revert itself fails | **stop and report the exact partial state** and manual steps |

**Never report success while any part failed or any change remains unreverted.**

## Status

Only the six schema values, and only the documented transitions: `proposed` → `approved`
or `rejected`; `approved` → `applied` or `failed`; `applied` → `reverted`; `failed` →
`proposed` after revision. `rejected` and `reverted` are terminal, and both files are kept.

## Output

**Refinement application** — proposal id, status, approval confirmation, items applied,
changed files (matching the target set), verification result, rollback information, and
the revert command.

On refusal: **Application refused** — the reason (missing or stale approval, hash
mismatch, schema failure, skill item), what changed (**nothing**), and what is needed.

Never describe a change as applied unless it was written **and** verified.

## References

- `references/approval-gates.md` — Gate A, Gate B's eight clauses, and their independence
- `references/application-contract.md` — scope, order, staleness, skill refusal
- `references/rollback-contract.md` — recording, reverting, and failure reporting
