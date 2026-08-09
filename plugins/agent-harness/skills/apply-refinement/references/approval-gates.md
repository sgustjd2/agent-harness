# Approval gates

Two gates, independent, neither substituting for the other.

## Gate A — host invocation (FR-025.1-A)

`agents/openai.yaml` sets `policy.allow_implicit_invocation: false`. A model cannot select
this Skill by reading a prompt; explicit `$apply-refinement` still works.

Gate A controls **what may start the Skill**. It says nothing about whether a change may
be written.

## Gate B — change approval (FR-025.1-B)

Enforced by the Skill body, in this order:

| # | Clause |
| ---: | :--- |
| B1 | **Inspect the specific proposal** — validate against the schema; confirm referenced runs and evidence exist |
| B2 | **Present the exact target file list and diff** — every path, every change |
| B3 | **Require confirmation bound to that proposal** — its id, item set, and targets |
| B4 | **Re-confirm immediately before writing** |
| B5 | **Refuse stale, missing, ambiguous, or mismatched approval** |
| B6 | **Never treat an earlier unrelated approval as permission** |
| B7 | **If anything cannot be verified, stop with no changes** |
| B8 | **Never persist approval as a replayable token** |

### Why each one is there

**B2 before B3**: approval given without seeing the diff approves an intention, not a
change. The list is the thing being agreed to.

**B4 after B3**: state can move between agreeing and writing. An approval refers to the
state it was shown for.

**B5**: "roughly the right approval" is no approval. Mismatched means it named a different
proposal, different items, or different targets.

**B6**: approvals do not accumulate into standing permission. A user who approved one
proposal last week has said nothing about this one.

**B7**: when verification is impossible, the safe result is no change — not a change made
hopefully.

**B8** (SEC-20): approval is a moment, not a credential. Storing it in a reusable form
would let a later run replay a decision nobody made about it, which is exactly the
authorization bypass the gate exists to prevent.

## The two gates are independent

**Gate B must hold where Gate A does not exist.** Specifically:

- a host with no invocation-policy mechanism at all
- a host that ignores the policy
- a copy of this Skill reached through a fallback distribution path

In all three, Gate A is absent or inert and **Gate B is the only thing standing between a
proposal and the user's files**. Gate A is defence in depth; treating it as the gate would
leave those cases unprotected.

## What is not approval

- **Explicit invocation is not approval.** Starting the Skill asks it to look; it does not
  authorize a write.
- **A message from an agent or subagent is not user approval** — on either host. Both
  treat inter-agent messages as untrusted for this purpose, and so does this Skill.
- **A hook, automation, or configuration setting is not approval.** There is no
  auto-approve path, and none may be added.
- **Prior approval of a different proposal is not approval of this one.**

Approval comes from the user, about this proposal, in this conversation.
