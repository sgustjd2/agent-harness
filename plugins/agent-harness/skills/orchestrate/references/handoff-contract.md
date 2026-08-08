# Handoff contract

What a delegated worker returns, and what travels onward.

## The worker result

Every delegated task returns a structured result. These fields are the minimum:

| Field | Note |
| :--- | :--- |
| `task_id` | the id from `plan.md` |
| `role` | the role the plan assigned |
| `status` | `done`, `failed`, `blocked`, or `skipped` |
| `summary` | a few sentences — what was done, not how it felt |
| `changed_files` | every path actually modified |
| `artifacts` | files created or produced |
| `open_questions` | unresolved items the next role needs |
| `commands_executed` | when any ran: the argv, exit code, duration |
| `blockers` | what stopped progress, if anything |
| `completion_criteria` assessment | explicitly, against the plan's criteria |

`changed_files` and the completion-criteria assessment are what the coordinator checks
before granting `done`. A result missing either cannot be accepted as complete — there is
nothing to check it against.

## Record it as returned

**Do not rewrite a worker result into fresh prose before recording it.**

Paraphrasing loses exactly what evidence exists to keep: the actual paths, the actual exit
codes, the specific open question. A summary of a summary is where "it mostly worked"
comes from — and a run that reads well while hiding which file changed is worse than a
verbose one.

Preserve the structure. Add coordinator judgement alongside it, not on top of it.

## What travels to the next role

Only three things:

1. the previous role's **`summary`**
2. its **`artifacts`** and **`open_questions`**
3. the **memory excerpt** relevant to this task

**Never forward the whole conversation history.** It costs tokens linearly, buries the
three things that matter, and hands the next worker context it has no reason to act on —
including instructions aimed at someone else.

## Roles are declarations, not guarantees

A logical role describes responsibility and authority. How a host realises it differs: on
one, a role may be a genuine tool allowlist; on another, only an instruction in a prompt.

When the requested role cannot be enforced natively, degrade to the closest safe path and
**record the degradation**. Do not describe a role as enforced when it was merely
requested — that turns a prompt into a permission boundary it was never able to be.
