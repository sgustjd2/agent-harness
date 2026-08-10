# Example: typescript-web

A reference `.agent-harness/config.yaml`. Validated against `config.schema.json` in CI,
so it cannot drift from the schema. **Documentation, not a runnable project.**

## Project-local binaries

```yaml
command:
  - node_modules/.bin/tsc
  - --noEmit
```

Not `npx tsc`.

`npx` will **fetch and run** a package that is not installed locally. That turns a
verification gate into a download: the gate can behave differently on two machines,
differently on the same machine tomorrow, and can reach the network during a run that is
otherwise offline.

Same principle as the Python example -- name the thing the project owns.

## The flaky gate

```yaml
flaky_policy: rerun-once
```

The only retry this product performs, and the only gate here that gets it.

Browser tests fail intermittently for reasons that have nothing to do with the change.
One rerun tells you which kind of failure you have.

**A gate that passes on the rerun is classified `flaky`, not `pass`.** That distinction is
the entire value: a test that only passes sometimes is a problem, and a policy that reruns
until green is a way of not seeing it. `flaky` says *this needs attention* while still
letting the run proceed.

Do not apply it to deterministic gates. A typecheck that fails and then passes is not
flaky; it means something else is wrong, and hiding that costs more than the rerun saves.

## `working_dir`

Relative to the repository root, and validated to stay inside it. Use it when a gate must
run from a subdirectory -- a monorepo package, a separate e2e project -- rather than
wrapping the command in a shell that changes directory first.

That wrapping is what the argv-array rule exists to prevent: a shell string is where
quoting bugs and injection live, and `working_dir` removes the reason to reach for one.
