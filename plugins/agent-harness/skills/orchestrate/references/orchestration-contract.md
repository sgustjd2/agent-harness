# Orchestration contract

What `orchestrate` may execute, in what order, and how far.

## The ready plan is the authority

`orchestrate` requires a specific run id or an unambiguously latest **ready** run, its
`plan.md`, and the `orchestration` section of `.agent-harness/config.yaml`.

| Situation | Result |
| :--- | :--- |
| no ready plan | **`Blocked`**, recommend `plan-work` |
| several ready runs, target unclear | **ask which one** — never choose silently |
| plan has a cyclic dependency graph | **reject** — never repair it |
| task missing a required field | **reject** — never fill it in |

Required per task: `task_id`, `role`, `completion_criteria`, `depends_on[]`, `reads[]`,
`writes[]`. `gates[]` is used when present.

**Never synthesize a plan.** A plan invented here has been approved by nobody, and the
whole contract rests on the plan having been approved.

## Frontier

A task enters the frontier when:

1. every task in `depends_on` is `done`,
2. it is not already terminal, and
3. its `writes[]` does not overlap another simultaneously selected task.

Walk the graph in topological order. A failed dependency makes its dependents `skipped`,
with the failing task recorded; unrelated branches keep running.

## Parallel cap

| Setting | Default | Hard cap |
| :--- | ---: | ---: |
| `orchestration.max_parallel_agents` | 3 | **5** |
| `orchestration.max_delegation_depth` | 1 | **2** |

Never exceed the configured value, and never exceed the schema cap. The cap exists
because token cost rises linearly with concurrent agents while coordination overhead rises
faster.

Parallel execution requires **all three**: dependency independence, disjoint `writes[]`,
and a host that genuinely exposes parallel subagents. Any one missing means sequential.

## Fallback

1. native parallel subagents
2. ordinary subagent path
3. direct sequential execution in the lead session

**Agent Teams is not a dependency.** Host-specific resolution belongs in adapters, not in
the canonical Skill.

**Degradation is always recorded**: `orchestration_mode: sequential` plus a non-empty
`degraded_reason`. A silent degradation looks identical to a design decision, and the next
reader cannot tell that parallelism was attempted and lost.

## Delegation depth

The coordinator owns orchestration. Workers return results to it; they do not redesign the
plan, do not spawn unbounded descendants, and do not become persistent identities or
sessions. Recursive autonomous agent trees are out of scope for this milestone.

## Roles

Use the role `plan.md` assigned — never silently substitute one. If the host cannot supply
that role, degrade to the closest safe native path and record it. **Do not report a role
as enforced when it was only requested in a prompt**: on one host a role may be a real
tool allowlist, on another only an instruction, and conflating them overstates the
guarantee.

## Planned commands only

Run only commands the plan names. Never infer them from `package.json`, `pyproject.toml`,
a Makefile, CI files, a README, or source comments — that inference is `init-project`'s
proposal step, and it only becomes runnable once a human writes it down.

Do not install a package because a tool appears missing, unless the plan says so and it is
separately approved when destructive or policy-sensitive.

Respect the host permission model; never bypass or weaken it.

**Verification commands belong to `verify-work`**, expressed as configured gates.
`orchestrate` is not a shortcut around that Skill's approval gate.

## Task status

| Status | Meaning |
| :--- | :--- |
| `done` | returned successfully, changes stayed inside `writes[]`, completion criteria assessed, no unresolved conflict |
| `failed` | executed, could not satisfy its completion criteria |
| `skipped` | deliberately not executed — failed dependency or blocked path; record which |

**A worker saying "done" is not sufficient.** `done` is the coordinator's judgement after
checking scope and criteria, not the worker's self-report.

`blocked` is a worker-returned disposition (missing destructive approval, unresolvable
input). It is **not terminal** — it forces the run itself to be reported `blocked`.

## Conceptual state

`ready → executing → reviewing`, or `ready → executing → blocked/failed`.

**No state-machine runtime in this milestone.** Nothing is persisted: no `evidence.md`, no
`result.md`, no queue, no resume engine. Evidence is returned in the response. An existing
`plan.md` may be read; real source changes from the work are expected.

## No completion declaration

`orchestrate` **never declares `completed`.** Completion depends on verification, and
`verify-work` owns gate outcomes.

When execution is ready for verification, return `recommended_next_action: verify-work` —
and do **not** invoke it automatically. If blockers remain, recommend resolving those
first. Partial success is never presented as completion.
