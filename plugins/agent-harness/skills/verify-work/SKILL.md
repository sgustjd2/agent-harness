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

Each gate runs **once**, unless `flaky_policy: rerun-once` is configured — then a gate
whose result is a plain non-zero exit may be rerun **exactly once**. A gate that failed
because the command was missing, was denied, or timed out is **never** retried: those
repeat identically and only burn the budget. When two runs disagree the gate is **flaky**,
which is **not** a pass — record both runs separately, with command, exit code and
excerpt for each.

If the run's verification budget is exhausted, remaining gates are `Not Run` with the
reason recorded, and verification is unverified rather than complete.

## Statuses

Exactly four, per gate:

| Status | Meaning |
| :--- | :--- |
| `Not Run` | execution never started |
| `Passed` | started, exited 0, within timeout |
| `Failed` | started and exited non-zero, **or** started and timed out |
| `Blocked` | could not safely start |

`Blocked` covers invalid gate configuration, an unavailable executable, an unsafe working
directory, argv that cannot be represented safely, a missing execution capability, and
stale approval.

**A command that exists is not a command that passed.** Never report `Passed` without an
observed exit code of 0, and never carry a previous run's result forward as this run's
result unless the user explicitly asked for reuse.

## Overall result

Computed conservatively from **required** gates only:

| Overall | Condition |
| :--- | :--- |
| `Passed` | every required gate ran **and** every one `Passed` |
| `Failed` | at least one required gate `Failed` |
| `Blocked` | no required gate `Failed`, and at least one is `Blocked` |
| `Not Run` | no required gate started |

Optional-gate failures never flip the overall result on their own — and they are never
hidden. When required gates all pass while optional ones fail, the overall result may
stay `Passed`, but the report must say **optional failures present** and list them.

When verification is anything other than `Passed`, say plainly that the work is
**unverified** and name the gates responsible. A result that reads like success while a
required gate did not pass is the single worst output this Skill can produce.

## Evidence

Per executed gate report: id, kind, argv command, repository-relative working directory,
whether it started, exit code when available, timeout status, duration when the host
exposes it, final status, and a concise evidence summary.

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
