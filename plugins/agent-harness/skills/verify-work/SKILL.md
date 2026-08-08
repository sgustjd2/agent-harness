---
name: verify-work
description: >-
  Run the project's configured verification gates and collect evidence. Use when asked to
  verify this work, run project checks, run the configured verification gates, test this
  implementation, check whether this change passes, run lint, tests, type checking or
  build verification, verify the implementation plan, or collect verification evidence.
  Runs only commands already approved in .agent-harness/config.yaml, never guessed ones,
  and only after you approve the exact gate set. It never edits source or configuration.
---

# verify-work

Run the checks the project already agreed to run, and report what actually happened.

**This Skill executes commands.** It is the only one that does. Everything else about it
is a limit on that power: only configured gates, only after approval, only argv arrays,
only inside the repository, and never a claim of success it did not observe.

## Safety contract

<!-- agent-harness:policy
read_only: false
executes_commands: true
requires_explicit_invocation: true
requires_execution_approval: true
executes_configured_gates_only: true
modifies_source: false
modifies_config: false
spawns_agents: false
network_access: false
installs_packages: false
modifies_user_settings: false
command_definition: argv-array
verification_default: Not Run
evidence_persistence: response-only
-->

`read_only: false` means only that subprocesses run, so this Skill is not
side-effect-free. It is **not** permission to edit anything: `modifies_source` and
`modifies_config` are false, and this Skill has no write surface at all. The gates
themselves may of course change files — that is the project's own decision, recorded in
its own configuration, and it is not this Skill writing.

## Two phases, always

### Phase A — inspect and propose

1. Read `.agent-harness/config.yaml` and **validate it against the state schema** before
   using anything in it. An unvalidated config is an unknown command list.
2. Read `verification.gates`. **If no gate is configured, stop and report `Blocked`**
   with the reason: there is nothing approved to run. Do not fall back to a guess.
3. Display every selected gate: id, kind, argv array, working directory, `required`,
   `timeout_seconds`, `flaky_policy` when set, and initial status **`Not Run`**.
4. Execute nothing yet.

**Never invent a command.** Do not read `package.json`, `pyproject.toml`, a Makefile, a
README, CI files, or the user's prose and then run what you find there. Inferring
candidate commands is `init-project`'s proposal step, and its output only becomes
runnable once a human writes it into the config. A command that arrived any other way
has never been approved by anyone.

### Phase B — execute

Requires approval tied to **the exact gate set displayed**. Explicit invocation is the
host's gate on *starting* this Skill; it is not approval to *run* anything.

Approval goes stale when any of these changes before execution: `config.yaml`, a gate's
argv, its working directory, its timeout, its `required` flag, or the selected gate set.
On any such change, **stop, re-propose, and ask again** — an approval names a specific
set of commands, so a different set is unapproved.

## Command contract

The `command` argv array is the source of truth.

- A shell **string** is never an acceptable gate. Reject it.
- Never synthesize `&&`, `||`, `;`, `|`, `>`, `>>`, or `<`.
- Never concatenate untrusted text into a command.
- Where the host takes an argv list, pass it through unchanged.
- Where the host offers only a shell-shaped interface, preserve the argv boundaries with
  the safest quoting that host supports, add no operators, and interpolate nothing.
- **If argv cannot be represented safely and losslessly, mark the gate `Blocked`.** Do
  not weaken the contract to get a result; a weakened contract produces a result nobody
  can trust.

Never run a package install, a plugin install, a marketplace registration, or a Git
mutation. Never run anything that is not a configured gate.

## Per-gate preflight

Before a gate starts, require all of:

| Requirement | Rejecting it prevents |
| :--- | :--- |
| non-empty gate id | unattributable evidence |
| supported gate kind | an unclassifiable result |
| `command` is a non-empty array of non-empty strings | a shell string sneaking in |
| `timeout_seconds` present and positive | a hang with no bound |
| `working_dir` contained in the repository, no traversal, not absolute-outside | running somewhere the user did not mean |
| `required` is a boolean | an ambiguous completion rule |
| the whole config conforms to the state schema | acting on a malformed contract |

A gate failing preflight is `Blocked` and **must not start**. A malformed **required**
gate means overall verification cannot be `Passed`.

## Execution order

Run gates **sequentially, in the order `config.yaml` declares**. No concurrency in this
milestone: sequential keeps output attribution obvious, keeps timeout behaviour
deterministic, and keeps two build tools from colliding in the same tree. Orchestration
is a later milestone, and adding it here quietly would pre-empt that decision.

Each gate runs **once**, unless `flaky_policy: rerun-once` is configured. See the flaky
rules below — the retry applies to exactly one classification, not to failure in general.

If the run's verification budget is exhausted, every remaining gate is classified
**`skipped`**, with the reason recorded, and `verification_status` becomes `unverified`.
Those gates were selected and planned for execution, so they are not "never started" in
the pre-execution sense — the run reached them and chose not to spend the budget.

## Two layers: blocking, then classification

These are different questions and must not be merged.

**Layer 1 — pre-execution blocking.** Before any process is attempted, a gate can be
`Blocked`: no configured gates at all, stale execution approval, configuration invalid
enough that the gate never becomes executable, an unsafe repository path, argv that the
host cannot represent safely, or no execution capability available. A `Blocked` gate never
reaches a process launch, so it has no process outcome to classify.

**Layer 2 — process classification.** Once a valid configured gate reaches an attempted
process launch, the outcome is classified with the PRD vocabulary, and only that
vocabulary:

| Classification | Meaning |
| :--- | :--- |
| `pass` | process started, exit code 0 |
| `fail` | process started normally, exit code non-zero |
| `error` | executable not found, permission denied, or the process could not execute for another environment or runtime reason |
| `timeout` | process started, exceeded its timeout, and was terminated because of it |
| `skipped` | the gate was selected but deliberately not run by execution control flow — budget exhaustion, or a PRD-defined skip condition |
| `flaky` | `flaky_policy: rerun-once`, the first classification was `fail`, and the rerun disagreed |

Three distinctions matter enough to state directly:

- **`error` is not `Blocked`.** A missing executable is discovered by attempting to launch
  the process. The gate was valid and approved; the environment failed it. Reporting that
  as a pre-execution block would hide an environment problem inside a configuration
  category.
- **`timeout` is not `fail`.** The process started and was killed by us. That is a
  different diagnosis from a test suite that ran and reported failures, and it is the one
  case where the exit code says nothing useful.
- **`skipped` is not "never run".** A gate skipped after planning was reached and passed
  over; calling it not-run implies the run never got that far.

**A command that exists is not a command that passed.** `pass` requires an observed exit
code of 0 from this run, and a previous run's result is never carried forward unless the
user explicitly asked for reuse.

## Flaky

Only `flaky_policy: rerun-once` produces a retry, and only for classification **`fail`**.

- **Never rerun `error`.** A missing executable stays missing.
- **Never rerun `timeout`.** It will exhaust the same bound again and spend the budget.
- Rerun **exactly once** — never a loop.
- If the two attempts disagree, the gate is **`flaky`**.
- **`flaky` is never promoted to `pass`**, however tempting the second green result looks.
- Record **both attempts** separately, each with its command, exit code and excerpt.

## verification_status

The authoritative outcome, computed from **required** gates only:

| `verification_status` | Condition |
| :--- | :--- |
| `passed` | every required gate is classified `pass` |
| `failed` | any required gate is `fail`, `error`, or `timeout` |
| `unverified` | any required gate is `skipped` or `flaky`, was `Blocked` before execution, or never ran |

`failed` and `unverified` say different things and must not be conflated: `failed` means
the checks ran and something is wrong with the work; `unverified` means the checks did not
establish anything, so the work's state is unknown.

Optional gates never change `verification_status`, and are never hidden. When every
required gate passes while optional ones do not, report **optional failures present** and
list them.

A one-line overall summary may be shown for readability, but it is derived from
`verification_status` and the classifications — never the source of truth, and never a
substitute for them.

Whenever `verification_status` is not `passed`, say plainly that the work is
**unverified or failed**, and name the gates responsible. A report that reads like success
while a required gate did not pass is the single worst output this Skill can produce.

## Evidence

Report per gate: **gate id**, **kind**, **required**, **command[]** as argv,
**repository-relative working directory**, **started or not started**, **exit code when
available**, **duration when available**, **classification**, **timeout information**, and
a **bounded output excerpt or evidence summary**.

Report for the run as a whole: **`verification_status`** — `passed`, `failed`, or
`unverified`.

A gate reran under `flaky_policy: rerun-once` contributes **two** evidence entries, one
per attempt.

Bound the output. Prefer a short failure reason, the relevant tail, a test summary, or
the diagnostic lines — not unlimited stdout and stderr.

Never include an environment dump, tokens, credentials, cookies, private keys, or full
user-home paths. Redact anything secret-shaped before reproducing it, and when you do,
say **"potential secret-like values were redacted"** rather than claiming the output is
certainly clean. Secret detection is pattern matching; it misses things, and a promise of
perfect redaction is a promise nobody can keep.

## Persistence

**Return the evidence in the response. Write nothing.** This milestone has no run-state
runtime, so this Skill does not create `evidence.md` or `result.md`.

If the user explicitly asks to save evidence, show the target path first and get approval
before writing. Do not build run lifecycle management here.

## References

- `references/execution-contract.md` — the execution rules in brief
- `references/evidence-template.md` — the report format
