# Remediation guide

How `doctor` offers fixes, and the limits on what it may offer.

## The one rule

**Remediation is a suggestion printed for a human. `doctor` never executes it.**

`automatic_remediation` is `false` on every finding, without exception. There is no flag
that changes this, and a diagnostic that repaired things would stop being a diagnostic —
the next run could no longer tell you what state you were actually in.

## What every `fail` owes

| Field | Note |
| :--- | :--- |
| Finding ID | the matrix ID, e.g. `CFG-03` |
| Reason | one concise sentence |
| Affected path or component | which file or which Skill |
| Expected | the contract |
| Observed | what was found, when safe to disclose |
| Impact | what stops working |
| Remediation | the next step, in words |
| Remediation command | an argv array, **or `none`** |
| `automatic_remediation` | always `false` |

A `warn` may carry guidance without a command. An `unknown` must say what could not be
determined and why — "cannot establish X without executing Y" is the useful form.

## Commands

Prefer argv arrays, for the same reason gates use them: a shell string invites quoting
and injection problems an array cannot have.

    remediation_command: ["python", "-m", "pytest", "-q"]

**Do not invent a command when manual inspection is the correct action.** A plausible
command that does not fit the situation is worse than `none` — someone will run it. When
the fix is "open this file and look at it", say that, and set the command to `none`.

**Never suggest a destructive fix by default.** Do not propose deleting a corrupt memory
file, resetting a config, or removing a directory. Corruption is a finding; what to do
about it is the user's decision, and the file may hold the only copy of something.

**Never suggest modifying user scope** — `~/.claude/`, `~/.codex/`, `~/.agents/`. Normal
operation never writes there, which is why a file appearing there is itself a `warn`.

## Routing

| Situation | Point them at |
| :--- | :--- |
| `.agent-harness/` missing, or initialization incomplete | **`init-project`** — it proposes every path first and writes nothing without approval |
| Project code needs checking | **`verify-work`** — and only that; `doctor` never runs a gate |
| Unsupported `schema_version` | the documented migration path, or `init-project` recovery. **Never auto-migrate** |
| Malformed or duplicated marker block | manual inspection. Ambiguous ownership must not be resolved by guessing |
| Corrupt memory file | manual inspection. Name the file; do not offer to delete or rewrite it |
| `commit_evidence: true` | explain the leak risk and leave the decision with the user |
| Missing manifest or Skill directory | reinstall or marketplace guidance — **only when the packaging diagnosis actually indicates it** |

That last row matters. "Reinstall the plugin" is the tempting universal answer and is
usually wrong: it discards evidence about what was actually broken, and it does nothing
for a project-state problem. Suggest it only when a packaging check is the finding.

## Reporting honestly

`doctor` never stops because a check failed — every applicable check still gets a status.

The summary counts `ok` / `warn` / `fail` / `unknown` separately, and `unknown` is never
folded into another bucket to make the report look better. **A green report obtained by
not looking is worse than an honest `unknown`**, because it ends the investigation.
