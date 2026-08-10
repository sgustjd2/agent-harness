# Example: python-service

A reference `.agent-harness/config.yaml`. Validated against `config.schema.json` in CI,
so it cannot drift from the schema. **Documentation, not a runnable project.**

## The one thing to copy from here

```yaml
command:
  - .venv/bin/python
  - -m
  - pytest
  - -q
```

Not `python -m pytest`.

A bare interpreter name is resolved by `PATH` at the moment the gate runs. That may be a
different Python than the one your packages are installed in. On Windows it is commonly
an app-execution stub that **runs nothing and exits non-zero** — which a contract dry-run
of this project hit on the first try.

The failure mode is worse than it sounds. `verify-work` reports `fail`, correctly: the
process ran and exited non-zero. `doctor` reports the executable as fine, also correctly.
Both are right, the tests pass, and the run says otherwise. **No status in the model
distinguishes "the check failed" from "the check never ran but looked like it did"** —
which is exactly why the interpreter is named here instead.

## This path is platform-specific, and that is a real cost

`.venv/bin/python` is POSIX. On Windows the same interpreter is
`.venv/Scripts/python.exe`.

`config.yaml` is **committed and shared**, so a mixed-platform team cannot write one path
that works for everyone. There is no clever fix in this file. The options are a committed
wrapper script that both platforms can invoke, per-developer local overrides, or accepting
the bare name and its risk with eyes open.

Naming the problem beats a config that silently only works on whoever wrote it.

## The other fields

`run_budget_seconds` bounds the whole gate set, separately from each gate's own
`timeout_seconds` — three gates that each finish inside their limit can still take longer
than anyone wants to wait.

`required: false` on the typecheck gate means a failure is **recorded in evidence but does
not block completion**. That is the setting for a check you are adopting gradually, and it
is honest in a way that deleting the gate would not be.
