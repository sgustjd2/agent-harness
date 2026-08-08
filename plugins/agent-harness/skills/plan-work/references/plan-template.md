# Plan template

The output structure for `plan-work`. Headings are the contract; prose under them is
free. Omit a section only when it is genuinely empty, and say so rather than deleting
the heading.

## ID conventions

| Kind | Format | Notes |
| :--- | :--- | :--- |
| Task | `T-01`, `T-02` | stable within a plan; never renumber, add new IDs instead |
| Acceptance criterion | `AC-01` | one observable condition each |
| Verification gate | `V-01` | always starts at `Not Run` |
| Risk | `R-01` | paired with a mitigation |
| Open question / decision | `Q-01` | blocks or shapes the plan |

## Frontmatter

Present only when the plan is saved as a file:

| Field | Meaning |
| :--- | :--- |
| `schema_version` | integer, the plan schema this file follows |
| `run_id` | `YYYYMMDD-HHMMSS-<slug>`, sortable and collision-free |
| `created` | when the plan was written |
| `goal` | the goal in one line |
| `classification` | `trivial`, `single-agent`, `parallel`, or `sequential` |
| `state` | the only field that may change after the plan is written |

## Sections

**1. Plan metadata** — title, status, planning timestamp when available, the source
request in the user's own words, and the applicable project.

**2. Objective** — what will be true when this is done, in one or two sentences. If it
cannot be stated observably, the plan is not ready.

**3. Current context** — what the repository already does that matters here. Known
facts only; cite paths.

**4. Assumptions** — each one labelled, with what changes if it is wrong.

**5. Scope** — what this work covers.

**6. Non-goals** — what it deliberately does not cover. This is what stops scope drift
later, so be specific rather than polite.

**7. Constraints** — technical, procedural, or policy limits the plan must respect.

**8. Work breakdown** — every task carries:

| Field | Meaning |
| :--- | :--- |
| task ID | `T-01` |
| description | what is done, concretely |
| expected files or components | best-known paths; mark uncertain ones as assumptions |
| dependencies | task IDs that must finish first; empty is fine and better |
| recommended role | `coordinator`, `researcher`, `implementer`, `reviewer`, `tester`, `refiner`, with a one-line reason |
| completion condition | how someone else can tell this task is done |

A task without a completion condition is not a task yet. Split it or raise it as an
open question.

**9. Dependency order** — the order tasks must run in, and why. No cycles: if two tasks
depend on each other, they are one task or the split is wrong.

**10. Parallelization opportunities** — tasks that may run at once. Two tasks qualify
only when they neither depend on each other nor write the same files. Say which files
each writes, so the claim is checkable.

**11. Acceptance criteria** — `AC-01`… Each one observable and testable by someone who
did not write the plan. "Works correctly" is not a criterion; "returns 404 for an
unknown id" is.

**12. Verification plan** — every item carries:

| Field | Meaning |
| :--- | :--- |
| gate | what is being checked |
| proposed command or inspection | written as a code span and labelled proposed |
| expected result | what success looks like |
| failure meaning | what a failure would tell you |
| execution status | `Not Run` |

Nothing here has been executed. `Not Run` is the only honest starting value, and it
stays until someone runs the gate and records real output.

**13. Risks and mitigations** — `R-01`… Each risk gets a mitigation or an explicit
acceptance that it is untreated.

**14. Blockers and decisions needed** — `Q-01`… Keep these separate from assumptions.
An assumption lets work continue; a blocker does not.

**15. Rollback or recovery considerations** — how to undo this if it goes wrong, and
anything that cannot be undone. Name the irreversible parts explicitly.

**16. Recommended next action** — the single next step, and who should take it.

## Example

A deliberately small one, to show shape rather than depth.

```
Objective: /health returns build metadata so deploys can be identified.

Assumptions
- A-01  The service exposes routes in src/routes/. If routes are registered
        elsewhere, T-01's file list changes.

Work breakdown
- T-01  Add a /health route returning version and commit.
        Files: src/routes/health.ts   Depends on: none
        Role: implementer -- a scoped source change.
        Done when: GET /health returns 200 with both fields.
- T-02  Add a route test.
        Files: src/routes/health.test.ts   Depends on: T-01
        Role: tester -- writes a check, not the feature.
        Done when: the test fails without T-01 and passes with it.

Acceptance criteria
- AC-01  GET /health returns 200.
- AC-02  The body contains a non-empty version and commit.

Verification plan
- V-01  Unit tests. Proposed: `npm test`. Expected: exit 0.
        Failure means the route or its test is wrong. Status: Not Run.

Risks
- R-01  Commit metadata may be unavailable in the container.
        Mitigation: fall back to "unknown" rather than failing the route.

Next action: confirm A-01, then start T-01.
```

Note the shape of `V-01`: a command, an expectation, and `Not Run`. It stays `Not Run`
in the plan no matter how confident anyone is about the outcome.
