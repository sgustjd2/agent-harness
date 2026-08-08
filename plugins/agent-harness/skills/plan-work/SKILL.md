---
name: plan-work
description: >-
  Plan work before implementing it. Use when asked to plan a feature, break a task
  into steps, prepare an implementation plan, define acceptance criteria, identify
  risks, dependencies or blockers, prepare work for multiple agents, plan a bug fix
  before editing code, or create a verification plan. Produces a structured plan with
  stable task IDs, recommended roles, dependency order, acceptance criteria and
  proposed verification commands. Read-only: it plans work, it never performs it, and
  it runs no commands.
---

# plan-work

Turn a goal into a plan someone can execute and check: tasks with completion
conditions, an honest dependency order, acceptance criteria, and a verification plan
that has not been run.

**This Skill plans. It does not implement, and it does not verify.** Everything it
produces is a proposal until a human or another Skill acts on it.

## Safety contract

<!-- agent-harness:policy
read_only: true
modifies_source: false
modifies_config: false
executes_commands: false
spawns_agents: false
network_access: false
verification_default: Not Run
persistence: on-request-only
-->

| May | Must not |
| :--- | :--- |
| read repository files, project instructions, existing plans | modify source code or configuration |
| identify constraints and existing conventions | execute tests, builds, or any shell command |
| propose commands, labelled as proposed | create branches, commit, push, install anything |
| write a plan file **when explicitly asked** | write a file merely because it was invoked |
| state assumptions and proceed | spawn agents or delegate work |
| ask when a missing fact blocks planning | claim anything passed, or claim work is done |

**A proposed command is not an executed command.** Every command in the output is a
suggestion for a human to run, and must be labelled so. If a plan ever reports a gate
as passing, that is a defect in how it was written, not a result.

## Procedure

1. **Read before planning.** Look at the files the request touches, the project's own
   instructions, and any existing plan. Prefer what the repository already does over
   what is generically good practice.
2. **Separate what you know from what you are guessing.** Use the labels below. An
   assumption written down is useful; an assumption hidden inside a task is a trap.
3. **Decide whether you can write completion conditions.** If a task cannot be given a
   condition that someone could check, either break it down further or record it as an
   open question. Do not paper over it with a vague task.
4. **Ask only when the answer changes the plan.** If the missing fact would change the
   task breakdown, ask. Otherwise state the assumption and continue — a plan delivered
   under a stated assumption beats a question that stalls the work.
5. **Classify the shape of the work** as `trivial`, `single-agent`, `parallel`, or
   `sequential`. Two tasks are only parallel when they neither depend on each other nor
   write the same files.
6. **Assign a recommended role per task** from the roles below, with a one-line reason.
7. **Write the plan** using the structure in `references/plan-template.md`.
8. **Check it** against `references/quality-checklist.md` before returning it.

## Labels

Use these words with these meanings. They are the difference between a plan and a
guess dressed as a plan.

| Label | Meaning |
| :--- | :--- |
| **Known fact** | observed in the repository or supplied by the user |
| **Assumption** | taken as true to proceed; not verified; would change the plan if wrong |
| **Open question** | unknown, and the plan is weaker until answered |
| **Decision needed** | a choice only the user can make; name the options |
| **Proposed action** | something to do later; not done |
| **Acceptance criterion** | an observable condition that decides whether the work is complete |
| **Verification step** | a gate to run later; always starts at `Not Run` |

## Recommended roles

Roles describe *what kind of work* a task is, and imply how much authority it needs.

| Role | Reads | Writes source | Runs commands |
| :--- | :---: | :---: | :---: |
| `coordinator` | yes | no | limited |
| `researcher` | yes | no | no |
| `implementer` | yes | yes, scoped | build and format only |
| `reviewer` | yes | no | no |
| `tester` | yes | no | gate commands only |
| `refiner` | yes | no | no |

Never assign file-writing work to `researcher` or `reviewer`.

## Output

Follow `references/plan-template.md`. Task IDs are `T-01`, acceptance criteria are
`AC-01`, verification gates are `V-01`, risks are `R-01`, and IDs are stable within a
plan — later edits add new IDs rather than renumbering existing ones.

Every task carries a completion condition, a dependency list, a recommended role, and
the files it is expected to read and write. Every verification item carries an
execution status, and that status is `Not Run` unless the user supplied real evidence
of a run in this conversation.

## Persistence

**By default, return the plan in the response and write nothing.** Being invoked is not
a request to create files.

When the user explicitly asks to save the plan:

1. Derive a run id of the form `YYYYMMDD-HHMMSS-<slug>` from the goal.
2. Show the target path — `.agent-harness/runs/<run-id>/plan.md` — and what will be
   written, before writing.
3. If a plan already exists at that path, stop and report it. Do not overwrite it and
   do not silently pick a different name.
4. Write only that one file. No memory entries, no run-state files, no configuration.

The plan file carries frontmatter with `schema_version`, `run_id`, `created`, `goal`,
`classification`, and `state`, matching the project's plan schema. Once written, treat
the plan as immutable apart from its `state` field: a changed plan is a new plan or an
explicit revision section, not an edit that erases what was decided.

## When not to plan

If the goal is too vague to produce a single checkable completion condition, do not
produce a plan. Say what is missing and ask for it. An empty or generic plan is worse
than no plan, because it looks like progress.

## References

- `references/plan-template.md` — the output structure and field meanings
- `references/quality-checklist.md` — the check to run before returning a plan
