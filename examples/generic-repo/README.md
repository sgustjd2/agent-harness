# Example: generic-repo

A reference `.agent-harness/config.yaml`. Validated against `config.schema.json` in CI,
so it cannot drift from the schema. **Documentation, not a runnable project.**

## No gates is a real configuration

```yaml
verification:
  gates:
```

Empty, on purpose.

`verify-work` reports **`unverified`** and stops. It does not read your `Makefile` or your
`package.json` and run what it finds there.

That restraint is the feature. A guessed command is one nobody approved, and running it to
see what happens is precisely the side effect the approval gate exists to prevent. So the
answer is `unverified` -- **not `passed`, not `failed`.** Nothing was checked, which is
true, and more useful than a green tick from a check invented on the spot.

`init-project` will *propose* gates it detects. Proposing is not enabling: they reach this
file only after you approve them.

## `generic` is a placeholder, not a fallback

Put it here when nothing identifies the project. Not when the signals are sitting in the
repository unread -- a `pyproject.toml` with a pytest section means `python`, and recording
`generic` beside it claims the project has no identity rather than being cautious about it.

## Project-specific redaction

The built-in patterns catch credential shapes that look the same in every project: known
token prefixes, private key headers, connection strings, absolute home paths. They cannot
know that *your* internal hostnames or customer identifiers matter. `extra_patterns` is
where that goes.

Applied **before** anything is written -- to evidence excerpts, result bodies, proposal
text, and memory entries. Not afterwards: by the time anyone reviews, the file exists.

**Fail-closed.** A value that cannot be established as safe is replaced rather than
stored. That costs you some legitimate text, and the trade is deliberate.

## `commit_evidence`

Left `false`. Setting it `true` un-ignores `runs/` and commits raw command output to your
history, and `doctor` reports that as a `warn` -- redaction reduces the leakage risk, it
does not remove it, and Git history is the wrong place to discover the difference.
