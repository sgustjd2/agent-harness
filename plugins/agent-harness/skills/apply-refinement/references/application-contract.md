# Application contract

What may be applied, to where, and in what order.

## One proposal

Exactly one proposal per run. **Never batch, never apply two.** Batching would mean one
approval covering changes a user reviewed separately, and a failure in one would leave the
others in an undefined state.

Applies only from `status: proposed` or `approved`. An `applied`, `rejected`, `failed` or
`reverted` proposal is not re-applied.

If the proposal is missing, schema-invalid, or cites evidence that does not exist:
**apply nothing**, record `status: failed`, report the reason.

## Staleness — `current_hash`

Where an item carries a `current_hash`, verify it against the target's current content
**before applying that item**.

A mismatch means the file changed after the proposal was written. The diff a human
approved is therefore **not** the diff that would land: **stop, report the drift, apply
nothing.** Applying anyway would put a change into a file whose reviewed state no longer
exists.

Where `current_hash` is `null`, say so plainly rather than implying the check ran.
`refine-harness` sets it only when a trustworthy hash was available without running a
command, and never invents one — precisely so that this check means something.

## Scope

Changes are confined to the `target_path` set the proposal enumerates. Every target is
normalized and repository-contained; traversal, outside-absolutes, user-home scope and
symlink escape are rejected.

**The final changed-file list must match the proposal's target set exactly.** Anything
extra, or anything missing, means stop and report — not a widened plan and not a partial
success.

| Change type | Applied to | Notes |
| :--- | :--- | :--- |
| `fact` | `.agent-harness/memory/facts.md` | fact validation rules apply |
| `decision` | `.agent-harness/memory/decisions.md` | supersede, never delete |
| `pattern` | `.agent-harness/memory/patterns.md` | — |
| `config` | `.agent-harness/config.yaml` | must stay schema-valid, including the §13.5 caps |
| `role` | `CLAUDE.md` / `AGENTS.md` | **inside the managed marker block only** |
| `workflow` | a project instruction target under `.agent-harness/` | none exists in the current layout |
| `skill` | — | **refused, see below** |

`decision` supersession: the existing entry's `status` becomes `superseded` with
`superseded_by`; the new entry records `supersedes`. **Decisions are never deleted** —
the history is the point of keeping them.

`role` edits stay strictly inside the managed marker block. Malformed or missing markers
are reported, never repaired here.

## Skill changes are refused

**A `skill` item is never applied.** `plugins/agent-harness/skills/**` is absent from the
write roots, and the item is refused outright with a report that it needs a human pull
request upstream.

A plugin that can rewrite its own Skills is lost on the next update **and** outside the
trust model that made it installable in the first place. There is deliberately no code
path for it — not a disabled one, not a guarded one.

## Never touched

`plugins/**` · `.git/` · source files outside the proposal · user scope (`~/.claude/`,
`~/.codex/`, `~/.agents/`) · another proposal · any host setting.

No package installation. No Git mutation. No network. No agent spawning.

## Order

1. Validate the proposal and its evidence references.
2. Verify every `current_hash` that is present.
3. Present the exact file list and diff; obtain approval bound to this proposal.
4. **Record rollback information** — before the first write.
5. Re-confirm.
6. Apply, minimally, only to the enumerated targets.
7. Run the configured verification gates.
8. On pass: `status: applied`, `applied_at`, `rollback`. On fail: revert, then
   `status: failed`.

Step 4 comes before step 6 deliberately. Rollback information recorded after the change
describes a state that no longer exists.

## Verification

Run the project's **configured** `verification.gates[]` — the same argv arrays and
timeouts `verify-work` uses. **No other command may run**: nothing inferred from
`package.json` or a Makefile, no shell string, no install, no Git.

If no gates are configured, report that verification could not be established. That is not
a pass, and it is not reported as one.
