---
name: doctor
description: >-
  Diagnose the agent-harness installation, environment, and project state. Use when asked
  to check the agent-harness installation, diagnose agent-harness, work out why
  agent-harness is not working, check project harness configuration, inspect harness
  health, verify the plugin layout, check config and memory integrity, diagnose Skill
  discovery, or inspect compatibility problems. Read-only: it reports ok, warn, fail or
  unknown for each check with a suggested fix, runs no commands, and repairs nothing.
---

# doctor

Diagnose **agent-harness itself** — is it installed correctly, is the project
initialized, is the state readable — and say what to do about anything broken.

**`doctor` diagnoses the harness. `verify-work` verifies your code.** They both "check
things", and confusing them is the easiest mistake to make here. If the question is "do
my tests pass", that is `verify-work` and it needs configured gates and execution
approval. If the question is "why isn't this working at all", that is `doctor`.

**Read-only, and it runs nothing.** No command, no gate, no `--version`, no PATH lookup.
It repairs nothing, creates nothing, and writes nothing in this milestone.

## Safety contract

<!-- agent-harness:policy
read_only: true
executes_commands: false
modifies_source: false
modifies_config: false
spawns_agents: false
network_access: false
verification_default: Not Run
persistence: on-request-only
-->

`persistence: on-request-only` is the shared read-only profile's field, and it grants no
write permission. **This milestone persists nothing at all** — no `doctor.md`, no run
directory, no state file. Everything comes back in the response.

## Statuses

Every check gets exactly one:

| Status | Meaning |
| :--- | :--- |
| `ok` | the observed state satisfies the expected contract |
| `warn` | usable, but risky, degraded, near a limit, or off the recommended policy |
| `fail` | a required harness condition is observably broken |
| `unknown` | the state cannot be determined safely with read-only capability |

Three rules that matter more than the definitions:

- **Never turn `unknown` into `fail`.** Not knowing is not the same as broken, and
  reporting it as broken sends people to fix something that may be fine.
- **Never turn `warn` into `fail`** just because a host differs from expectation.
- **`doctor` never stops.** A `fail` in one check does not end the run; every applicable
  check still gets a status. A complete run means every check was judged — not that
  everything was `ok`.

### Checks that do not apply

A check whose **Applies** condition in the diagnostic matrix is unmet is reported **`not
applicable`**, with the reason — for example *"not applicable: the project is not
initialized"*.

`not applicable` is **not a fifth status**. It says the check was never in scope, so there
was nothing to judge; the four statuses all describe an outcome of judging something.

- **`not applicable` never affects the overall result** — not `broken`, not `degraded`,
  not `unknown`.
- **Do not report it as `unknown`.** `unknown` means the state could not be determined;
  here it is known precisely, and reporting "I could not tell" would send someone
  investigating a check that was never relevant.
- **Do not omit the section.** The report shape is fixed, so an empty section says *not
  applicable* and why.

This is the common case on a first run: before `init-project`, the Configuration, Memory
and Verification-executable sections have nothing in scope.

### Observations that are not judgements

A few checks exist to **report a fact, not to rule on it**. Those are marked `info`.

`info` follows the same logic as `not applicable`, applied one step later. The four
statuses each describe an outcome of judging something; `not applicable` says the check
was never in scope; **`info` says it was in scope, it was observed, and judging it is not
this Skill's call.**

- **`info` never affects the overall result**, for the same reason `not applicable` does
  not: no judgement was made.
- **Do not report an `info` observation as `ok`.** `ok` says *I checked this and it is
  fine*, and a reader takes it as endorsement. Reporting an optional host agent template
  as `ok` would say this Skill approved of it being installed, which it did not.
- **Do not report it as `warn` either.** Nothing is wrong.
- Say what was found, plainly: *"info: 2 role templates present in `.codex/agents/` —
  researcher, reviewer"*, or *"info: none present"*.

The optional Codex role templates are the case this exists for. Whether installing one is
a good idea depends on what the user wants their agents to be allowed to do, and that is
theirs to decide.

## Findings

Every **`fail`** carries: finding ID, concise reason, affected path or component,
expected state, observed state when safe to disclose, proposed remediation, a remediation
command as an argv array **when a safe concrete one exists**, and
`automatic_remediation: false` — always.

Remediation commands are **suggestions printed for a human**. `doctor` never runs one.
When manual inspection is the right answer, say so instead of inventing a command.

A **`warn`** may carry remediation guidance but needs no command. An **`unknown`** must
say what could not be determined and why.

## Checks

### Environment

**Host identification.** Determine the active host only from what the host context or
readable project structure already exposes. Values: `Claude Code`, `Codex`, `Mixed /
both artifacts present`, `Unknown`. Never run `claude --version` or `codex --version`.

Co-located `.claude-plugin/` and `.codex-plugin/` prove **packaging compatibility**, not
which host is executing. If identity cannot be established safely, report `unknown` — and
never fail the installation for that alone.

**Python 3.10+.** Do not launch Python. Use interpreter or executable metadata the host
already exposes. If Python is visible but its version needs execution to establish,
prefer `unknown` — "Python version cannot be verified without process execution". A
filename alone justifies a conclusion only when it explicitly encodes the version, and
then only as a clearly qualified one. If Python is unavailable, continue with reduced
file-based checks and say that is what happened.

**Git.** Prefer readable repository metadata such as a `.git/` directory, or VCS metadata
the host already exposes. Never run `git status` or `git rev-parse`. `ok` when confidently
identified, `warn` when the project deliberately uses `vcs: none`, `unknown` when it
cannot be determined safely. A valid `vcs: none` project is not a failure.

### Plugin installation

Check that `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` both exist, that
`skills/` exists, and that **all seven** production Skills are present — `plan-work`,
`init-project`, `verify-work`, `doctor`, `orchestrate`, `refine-harness`,
`apply-refinement` — plus the `m1-discovery-fixture` compatibility fixture.

Any one of them missing is a `fail`. A Skill directory that is **not** on that list is
also a finding: the installable root admits exactly the Skills the milestone declares.

If the plugin root cannot be resolved safely, report `unknown`. Do not guess a
home-directory cache path. Never use `~/.claude/plugins/cache` as a lookup root.
Never use `~/.codex/plugins/cache` as one either.

### Skill integrity

Per shipped Skill: the directory exists, `SKILL.md` exists, the frontmatter `name`
matches the directory, the frontmatter carries only the canonical allowed fields,
referenced files exist inside the Skill root, and `agents/openai.yaml` parses when
present.

Report findings at that level. Do not restate the whole deterministic validator suite in
prose — this is a health check, not a second copy of CI.

A missing **currently implemented** Skill is `fail`. A not-yet-implemented Skill being
absent is `ok` / not applicable.

### Project state

**If `.agent-harness/` does not exist: `fail`**, with the remediation "run `init-project`".
Do not create it.

If it exists, inspect `config.yaml`, `memory/facts.md`, `memory/decisions.md`,
`memory/patterns.md`, `.gitignore`, `runs/` and `proposals/` against the state schemas:
config parses, `schema_version` exists and is supported, required sections exist, memory
files are structurally readable, and `.agent-harness/.gitignore` exists and protects the
local-only paths.

`runs/` must be ignored by that file. If it is not, `warn` — run evidence is the most
likely place for something sensitive to reach history.

**Never repair.** Do not regenerate config, do not delete corrupt memory, do not rewrite
anything. A corrupt file is a finding, not permission to fix it.

### Configuration and schema version

The current supported `schema_version` is **1**.

| Observed | Status |
| :--- | :--- |
| supported version | `ok` |
| valid but unsupported version, migration needed | `fail` |
| config cannot be parsed | `fail` |
| version cannot be determined without unsafe assumptions | `unknown` |

Point remediation at the documented migration path or at `init-project` recovery. **Never
auto-migrate.**

**`runs.commit_evidence: true` is a `warn`** — explain that committing run evidence
raises the risk of sensitive output reaching history. Do not change the value and do not
edit `.gitignore`.

**Config drift** is only checkable when Git metadata and a committed baseline are
available without running commands. If comparison would require executing Git, report
`unknown`. Drift found means `warn`. Being unable to tell is not a failure.

### Memory

Inspect `facts.md`, `decisions.md` and `patterns.md` **independently**, and classify each
separately — one corrupt file must not make the other two unreadable.

Check structure and integrity only. Do not judge whether a recorded fact is *true*, do
not rewrite entries, do not merge duplicates, do not prune. Those belong to the
refinement workflow.

### Verification executables — the boundary that matters

`doctor` may inspect whether the executable named by a configured gate **appears**
available. It must **never run it**.

Forbidden here, all of them: running the gate, running a "harmless subset" of the gate,
`--version`, `command -v`, `which`, `where`, `Get-Command`, or any other lookup that
starts a process. This Skill declares `executes_commands: false`, and executing anything
to answer a question would make that declaration false.

Order of attempts:

1. Read the first argv token of the configured gate.
2. If it is an explicit repository-relative executable path — normalize it, confirm it
   stays inside the repository, check filesystem existence, and inspect executable
   metadata the host exposes without spawning anything.
3. If it is a bare executable name — use host-exposed PATH information only when
   available without starting a process, inspect candidate files directly, and account
   for `PATHEXT` on Windows only when that information is already safely exposed.
4. Otherwise: **`unknown`**, stating that availability could not be established without
   executing a lookup.

**An `unknown` executable is never a `fail`.** We do not know; that is the finding.

**Finding a file does not mean finding the right interpreter.** When a gate's first argv
token is a bare interpreter name (`python`, `node`, `ruby`) and the project carries its own
interpreter — a virtualenv, a version-manager file — report **`warn`**, not `ok`: the name
will be resolved by `PATH` at run time and may not be the interpreter the project's tooling
lives in. On Windows it may be an app-execution stub that runs nothing.

This matters because the failure it produces is invisible downstream: the gate exits
non-zero, verification correctly reports failure, and nothing distinguishes it from a real
one. Saying `ok` here because a file exists on `PATH` would let diagnosis call an
environment healthy while verification calls the work broken.

### Host instructions

Inspect `CLAUDE.md` and `AGENTS.md` when present, for the managed marker block
`<!-- BEGIN agent-harness -->` … `<!-- END agent-harness -->`:

| Observed | Status |
| :--- | :--- |
| exactly one valid block | `ok` |
| no block | `warn`, with the `init-project` remediation |
| unmatched, duplicated, or nested markers | **`fail`** — ownership is ambiguous |

When both files carry a managed block, compare the block contents. A mismatch means the
two hosts are being told different things, which is the drift the parity requirement
exists to catch — report it. **Never repair either file.**

### Host agent templates

Look in `.codex/agents/` for the six optional Codex role templates — coordinator,
researcher, implementer, reviewer, tester, refiner — and report which are present as
**`info`**. None present is equally correct and reported the same way.

**Report, never judge.** Whether a role template belongs in a project is a decision about
what the user's agents may do, and it is theirs. `ok` would read as approval of a choice
this Skill never evaluated.

**Never look in `~/.codex/agents/`.** That is user scope, outside the repository, and
reading it would mean inspecting state the project does not own to report a fact the user
already knows. Nothing in this product writes there; nothing here reads there.

If a file in `.codex/agents/` is not one of the six, say so as part of the same
observation and leave it alone. It is not this plugin's file.

### Compatibility (informational)

**`AGENTS.md` size.** Codex concatenates `AGENTS.md` from the Git root down against a
32 KiB budget. `warn` above 80% of that. If the accumulated applicable size cannot be
determined safely, report `unknown` — do **not** fabricate it from a single `AGENTS.md`
when parent-directory files would also count.

**Claude Agent Teams.** Report the state as informational when the host context exposes
it. Not enabled is not a failure; unknown is not a failure. It is not a dependency, and
`doctor` neither enables it nor edits any setting.

**Codex custom agents.** If project-scope `.codex/agents/*.toml` exists, report its
presence as info and validate only basic readable structure. Absence is `ok`. Never
inspect or modify user-scope `~/.codex/agents/`, and never create or delete a template.

**User-scope files.** If anything under the user's home scope appears to have been created
by agent-harness, `warn` — normal operation never writes there.

**Helper path.** The current Skill set ships **no bundled runtime helper**, so there is
nothing to resolve: report `ok` — "no helper required by the current implemented Skill
set". Portable Skill-script path resolution (Q-IMPL-003) remains unresolved; do not
invent a future helper path and do not claim the question is settled.

## Report

    # agent-harness doctor
    
    Overall: healthy | degraded | broken | unknown

Then: **Environment**, **Plugin installation**, **Skill integrity**, **Project state**,
**Configuration**, **Memory**, **Verification executables**, **Host instructions**,
**Compatibility**, **Findings**, **Summary**, **Recommended next action**.

Each finding carries ID, Check, Status, Expected, Observed, Impact, Remediation, and
Remediation command (argv or none). The summary counts `ok`, `warn`, `fail` and `unknown`,
and lists `not applicable` and `info` separately — neither is an outcome. One says the
check was out of scope; the other says it was observed and not judged.

Overall is computed in this order:

| Overall | Condition |
| :--- | :--- |
| `broken` | one or more `fail` |
| `degraded` | zero `fail`, one or more `warn` |
| `unknown` | zero `fail`, zero `warn`, one or more `unknown` |
| `healthy` | every applicable required check is `ok`, with no `warn`, `fail` or `unknown` |

**Never hide an `unknown` to reach `healthy`.** A green report that was achieved by not
looking is worse than an honest `unknown`.

## References

- `references/diagnostic-matrix.md` — every check and its four status conditions
- `references/remediation-guide.md` — how remediation is offered, and its limits
