---
name: orchestrate
description: >-
  Execute an approved plan. Use when asked to execute this plan, implement the planned
  work, coordinate these tasks, delegate independent tasks, run tasks in dependency
  order, continue this ready run, or perform the planned implementation. Works only from
  an existing ready plan, delegates within the plan's declared write scope, runs only
  commands the plan names, and never declares the work complete on its own.
---

# orchestrate

Execute a plan that already exists. Walk the dependency graph, delegate what can safely
run at once, keep every change inside the scope the plan declared, and report what
actually happened.

**The authority comes from the plan, not from this Skill.** A human approved that plan;
`orchestrate` carries it out. It never decides *what* to do — only how to sequence and
delegate what was already decided.

## Safety contract

<!-- agent-harness:policy
read_only: false
executes_commands: true
spawns_agents: true
modifies_source: true
requires_explicit_invocation: true
requires_ready_plan: true
executes_planned_commands_only: true
modifies_planned_paths_only: true
destructive_actions_require_approval: true
respects_dependency_graph: true
max_parallel_from_config: true
auto_merge_conflicts: false
network_access: false
modifies_user_settings: false
evidence_persistence: response-only
run_state_runtime: deferred
-->

This is the widest contract in the product, and the three `..._only` fields are what make
it acceptable: planned commands only, planned paths only, dependency graph respected.

## Invocation and approval

Explicit invocation is required — implicit invocation is off.

**For ordinary planned work, explicit invocation is sufficient.** Do not stop and ask
again for every task; the plan was already approved, and re-approving each step turns a
safety gate into a rubber stamp nobody reads.

**Ask again, immediately before the action, for anything destructive or irreversible:**
force push, destructive file-tree deletion, migration execution, destructive database
operations, rewriting remote history, or weakening a permission or sandbox. Without
approval: do not perform it, mark that task **blocked**, and continue independent safe
tasks.

Never bypass or weaken the host's own permission model.

## Input

Requires a specific run id, or an unambiguously latest **ready** run, plus that run's
`plan.md` and the `orchestration` settings from `.agent-harness/config.yaml`.

- **No ready plan → `Blocked`**, recommending `plan-work`. Never synthesize a plan.
- **Several ready runs and the target is unclear → ask which one.** Never pick silently.
- Validate the plan before executing it: every task needs `task_id`, `role`,
  `completion_criteria`, `depends_on[]`, `reads[]`, `writes[]`; `gates[]` is used when
  present. **Reject a cyclic graph. Never repair a malformed plan.**

## Frontier and execution

A task is ready when every `depends_on` is `done`, it is not already terminal, and its
planned writes do not overlap another simultaneously selected task.

Parallel execution requires all three: dependency independence, disjoint `writes[]`, and
a host that actually exposes parallel subagents. Otherwise run sequentially. Respect
`orchestration.max_parallel_agents` — never exceed the configured value or the schema cap.

Fallback order: native parallel subagents → ordinary subagent path → direct sequential
execution in the lead session. **Agent Teams is not required**, and host-specific
resolution belongs in adapters, not here.

**Never degrade silently.** Record `orchestration_mode: sequential` with a non-empty
`degraded_reason`.

Respect `orchestration.max_delegation_depth`. The coordinator owns orchestration; workers
return results to it. They do not redesign the plan, do not spawn unbounded descendants,
and do not become persistent identities.

## Roles

Use the role `plan.md` already assigned. Never silently change it. If the host cannot
provide that role, degrade to the closest safe native path and **record the degradation** —
do not report a role as enforced when it was only requested in a prompt.

## Scope

**Paths.** A task may modify only what its `writes[]` permits. Overlapping planned writes
force sequential execution. Afterwards, compare each result's `changed_files` against its
planned `writes[]`: an unplanned path means the task is **not** `done` — report a scope
violation. Do not keep the out-of-scope change as accepted work, do not auto-revert
without an approved rollback contract, and **never expand the plan to justify a file that
appeared**.

**Commands.** Run only commands the plan names. Never infer them from `package.json`,
`pyproject.toml`, a Makefile, CI files, a README, or source comments. Do not install a
package because a tool looks missing unless the plan says so and it is separately approved
when destructive.

**`orchestrate` is not a substitute for `verify-work`.** Commands whose purpose is
verification belong there, expressed as verification gates.

## Handoff

Every delegated result returns a structured handoff — `task_id`, `role`, `status`,
`summary`, `changed_files`, `artifacts`, `open_questions`, `commands_executed` when
applicable, `blockers`, and a `completion_criteria` assessment.

**Record the worker's result as returned.** Rewriting it into fresh prose first loses the
facts the evidence exists to preserve.

Forward to the next role only: the previous `summary`, the `artifacts` and
`open_questions`, and the memory excerpt relevant to that task. **Never the whole
conversation.**

## Task status

Terminal: **`done`**, **`failed`**, **`skipped`**. A task is `done` only when the work
returned successfully, changed paths stayed inside `writes[]`, completion criteria were
explicitly assessed, and no scope conflict is unresolved. *A worker saying "done" is not
enough by itself.*

`failed` — it ran and could not satisfy its completion criteria. `skipped` — deliberately
not executed, because a dependency failed or the path was blocked; record which one.
**`blocked`** is a worker-returned disposition (missing destructive approval, unresolvable
input); it is not terminal, and it forces the run to report `blocked`.

Keep failure isolated. A failed dependency skips its dependents; unrelated tasks continue.

## State, conceptually

`ready → executing → reviewing`, or `ready → executing → blocked/failed`.

Entering from a valid ready plan is `executing`; when every task is `done`/`failed`/
`skipped`, the run reaches `reviewing` — unless a blocking failure means it must be
reported `blocked` or `failed` instead.

**`orchestrate` must never declare `completed`.** Completion depends on verification, and
`verify-work` owns gate outcomes. When execution is ready for verification, return
`recommended_next_action: verify-work` — but **do not call it automatically**. If blockers
remain, recommend resolving those first.

**No run-state runtime in this milestone.** Nothing is persisted: no `evidence.md`, no
`result.md`, no queue, no resume engine. Evidence comes back in the response. An existing
`plan.md` may be read, and real source changes from the work itself are expected.

## Report

    # Orchestration result
    Run: / Plan:
    Orchestration mode: parallel | sequential
    Degraded reason: <reason or none>
    Conceptual transition: ready -> executing -> reviewing | blocked/failed

Then **Tasks** (per task: id, role, status, dependencies, planned writes, changed files,
completion-criteria assessment, summary, artifacts, commands executed, blockers, open
questions), **Scope violations**, **Conflicts**, **Evidence summary**, **Remaining work**,
**Recommended next action**.

**Never present partial success as completion.**

## References

- `references/orchestration-contract.md` — frontier, caps, fallback, statuses
- `references/handoff-contract.md` — worker result fields and what is forwarded
- `references/conflict-policy.md` — overlap, collision, scope violation, destructive gate
