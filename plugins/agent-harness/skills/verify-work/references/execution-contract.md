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

A gate failing preflight is `Blocked` and does not start. A malformed **required** gate
means overall verification cannot be `Passed`.

## Execution

- **Sequential, in declared order.** No concurrency in this milestone.
- Each gate runs **once**, unless `flaky_policy: rerun-once` is configured — then a plain
  non-zero exit may be rerun **exactly once**. A missing executable, a permission denial,
  or a timeout is **never** retried.
- Disagreeing runs mean **flaky**, which is **not** a pass. Record both runs separately.
- Budget exhaustion leaves remaining gates `Not Run`, and verification unverified.

## Never

Package installation. Plugin installation. Marketplace registration. Git mutation.
Network access initiated by this Skill. Editing source or configuration. Anything that is
not a configured gate.

## Statuses

`Not Run` never started · `Passed` started, exited 0, within timeout · `Failed` exited
non-zero **or** timed out after starting · `Blocked` could not safely start.

Overall, from **required** gates only: `Passed` when all ran and all passed; `Failed` when
any failed; `Blocked` when none failed and any is blocked; `Not Run` when none started.

Optional failures never flip the overall result by themselves, and are never hidden.

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

A command that exists is not a command that passed. `Passed` requires an observed exit
code of 0 from this run. A previous run's result is not this run's result unless the user
explicitly asked for reuse.

When the overall result is anything but `Passed`, say the work is **unverified** and name
the gates responsible.
