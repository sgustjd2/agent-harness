# Execution contract

The rules that bound what `verify-work` may run. Every one of them narrows execution;
none of them widens it.

## What may run

- **Configured gates only.** The command set comes from `verification.gates` in
  `.agent-harness/config.yaml`, validated against the state schema before use.
- **No guessed commands.** Never derive a command from `package.json`, `pyproject.toml`,
  a Makefile, a README, CI files, or the user's prose. Proposing candidates is
  `init-project`'s job; a command becomes runnable only once a human writes it into the
  configuration.
- **No configured gates means `Blocked`**, with the reason stated. It does not mean fall
  back to something plausible.

## Approval

- **Explicit execution approval is required**, tied to the exact gate set displayed.
- Invoking the Skill is the host's gate on starting it. It is not approval to run
  anything.
- Approval is **stale** — and must be requested again — if `config.yaml`, a gate's argv,
  its working directory, its timeout, its `required` flag, or the selected gate set
  changes before execution.

## Command shape

- **The argv array is the source of truth.** A shell string is never an acceptable gate.
- Never synthesize `&&`, `||`, `;`, `|`, `>`, `>>`, `<`.
- Never concatenate untrusted text into a command.
- Pass argv through unchanged where the host accepts it. Where the host offers only a
  shell-shaped interface, preserve argv boundaries with the safest quoting it supports,
  add no operators, interpolate nothing.
- **If argv cannot be represented safely and losslessly, the gate is `Blocked`.** A
  weakened contract produces a result nobody can trust, which is worse than no result.

## Per-gate preflight

Required before a gate starts: non-empty id; supported kind; `command` a non-empty array
of non-empty strings; `timeout_seconds` present and positive; `working_dir` contained in
the repository with no traversal and no outside-absolute path; `required` a boolean; and
the configuration conforming to the state schema.

A gate failing preflight is `Blocked` and does not start -- that is layer 1, below. A
malformed **required** gate means `verification_status` cannot be `passed`.

## Execution

- **Sequential, in declared order.** No concurrency in this milestone.
- Each gate runs **once**, unless `flaky_policy: rerun-once` is configured — then, and
  only then, a gate classified **`fail`** may be rerun **exactly once**.
- **Never rerun `error`.** A missing executable stays missing.
- **Never rerun `timeout`.** It exhausts the same bound again and spends the budget.
- Disagreeing attempts mean **`flaky`**, which is **never promoted to `pass`**. Record
  both attempts separately, each with command, exit code and excerpt.
- Budget exhaustion classifies every remaining gate **`skipped`**, and
  `verification_status` becomes `unverified`.

## Never

Package installation. Plugin installation. Marketplace registration. Git mutation.
Network access initiated by this Skill. Editing source or configuration. Anything that is
not a configured gate.

## Two layers

**Pre-execution blocking** and **process classification** are different questions.

**`Blocked`** applies *before* any process is attempted: no configured gates, stale
execution approval, configuration that never becomes executable, an unsafe repository
path, argv the host cannot represent safely, or no execution capability. A `Blocked` gate
has no process outcome to classify.

**Classification** applies once a valid gate reaches an attempted launch, using the PRD
vocabulary and only that vocabulary:

| Classification | Meaning |
| :--- | :--- |
| `pass` | started, exit code 0 |
| `fail` | started normally, exit code non-zero |
| `error` | executable not found, permission denied, or otherwise unable to execute |
| `timeout` | started, exceeded its timeout, terminated because of it |
| `skipped` | selected, then deliberately not run — budget exhaustion or a PRD-defined skip |
| `flaky` | `rerun-once`, first attempt `fail`, rerun disagreed |

`error` is **not** `Blocked` — the gate was valid and approved; the environment failed it,
and burying that in a configuration category hides an environment problem. `timeout` is
**not** `fail` — the process started and we killed it, which is a different diagnosis.
`skipped` is **not** "never run" — the run reached the gate and passed over it.

## verification_status

From **required** gates only:

| Value | Condition |
| :--- | :--- |
| `passed` | every required gate is `pass` |
| `failed` | any required gate is `fail`, `error`, or `timeout` |
| `unverified` | any required gate is `skipped`, `flaky`, pre-execution `Blocked`, or never ran |

`failed` means the checks ran and something is wrong. `unverified` means the checks
established nothing. Do not conflate them.

Optional gates never change `verification_status`, and are never hidden. A one-line
overall summary may be shown, but it is derived from this — never the source of truth.

## Evidence and output

- Bound the output: a concise failure reason, the relevant tail, a test summary, the
  diagnostic lines. Not unlimited stdout and stderr.
- Never include an environment dump, tokens, credentials, cookies, private keys, or full
  user-home paths.
- Redact secret-shaped values before reproducing them, and say **"potential secret-like
  values were redacted"** rather than claiming the output is certainly clean. Pattern
  matching misses things; a promise of perfect detection is one nobody can keep.
- Raw output stays **local by default** and in the response only. This milestone writes
  no evidence file.

## No false success

A command that exists is not a command that passed. `pass` requires an observed exit
code of 0 from this run. A previous run's result is not this run's result unless the user
explicitly asked for reuse. `flaky` is never promoted to `pass`.

When `verification_status` is anything but `passed`, say the work is **failed or
unverified** -- whichever applies -- and name the gates responsible.
