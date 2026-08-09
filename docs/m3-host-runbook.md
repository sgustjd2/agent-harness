# M3 manual host runbook — Claude Code

M3's exit criteria are **ATS-001, ATS-003, ATS-004, ATS-005 (Agent Teams disabled path)**
and the adapter drift check. The drift check runs in CI. The four acceptance tests need a
human at a real host, and two of them need a paid model call.

This page is both the procedure and the record. **Fill it in as you go, not afterwards** —
a record written from memory at the end is where "it mostly worked" comes from.

Do not paste tokens, credentials, whole config files, or full logs into any record.
Capture only the fields each step names.

## Session

| | |
| :--- | :--- |
| Date | |
| Host and version | e.g. Claude Code 2.1.195 |
| Plugin loaded how | `--plugin-dir` / marketplace install |
| Target repository | **disposable copy?** yes / no |

## How to classify a failure

Same three codes the M2 dry-run used, because the distinction has the same consequence:
each sends the fix to a different place.

| Code | Meaning | Where the fix goes |
| :--- | :--- | :--- |
| **C** | contract defect — the file says the wrong thing, or says nothing | the `SKILL.md`, agent, or adapter |
| **A** | adherence failure — the file is right, the model did not follow it | clearer or more prominent wording |
| **U** | unenforceable by instruction — no wording would reliably hold | a validator, schema field, or host policy |

---

## RB-M3-00 — component discovery **(already done, non-interactively)**

**Status: Passed.** Recorded here because the rest of the runbook builds on it.

```bash
claude --plugin-dir ./plugins/agent-harness plugin details agent-harness@inline
```

| Field | Observed |
| :--- | :--- |
| Host | Claude Code 2.1.195 |
| Skills | **8** — the 7 production Skills + `m1-discovery-fixture` |
| Agents | **6** — coordinator, implementer, refiner, researcher, reviewer, tester |
| Hooks / MCP / LSP | 0 / 0 / 0 |
| Always-on token cost | ~1,524 |
| Installed record created | none — `scope: session` |

**What this establishes.** The host discovers plugin-root `agents/`, and it discovers all
six. M1.4A read `Agents 0` from the same command, so the number moving to 6 is the
mechanism M3 slice 1 depends on, observed rather than assumed.

**What it does not establish.** That the `tools` allowlist is enforced — see RB-M3-05.
Discovery is not enforcement.

---

## RB-M3-01 — ATS-001, fresh installation

**Needs:** a Claude Code environment where agent-harness has never been installed, and
network access. **No model call.**

Follow `install-claude-code.md` exactly. If a step there is wrong, that is the finding —
record it rather than working around it, because the next person will hit the same step.

```bash
git status              # before
```

Then, in a session: `/plugin marketplace add sgustjd2/agent-harness`, then
`/plugin install agent-harness@agent-harness`.

```bash
git status              # after -- must be identical
```

| Check | Result | Notes |
| :--- | :--- | :--- |
| marketplace registration succeeded | | |
| catalog appears in the marketplace list | | |
| installation succeeded | | |
| 7 Skills exposed as `/agent-harness:<name>` | | |
| 6 agents present in the inventory | | |
| `git status` identical before and after | | |

**This is the step most likely to fail**, and the only one whose failure is expected. The
marketplace route has never been exercised — `--plugin-dir` is the path with evidence
behind it. A failure here is a finding about packaging, not about the Skills.

---

## RB-M3-02 — ATS-003, initializing an existing repository

**Needs:** a disposable copy of a real Python repository with **no `CLAUDE.md`** and an
**existing `AGENTS.md` that already has team rules in it**. **Costs a model call.**

Record the hash of `AGENTS.md` first:

```bash
git hash-object AGENTS.md
```

Then invoke `/agent-harness:init-project` and approve what it proposes.

| Check | Result | Notes |
| :--- | :--- | :--- |
| 7 files created under `.agent-harness/` | | config.yaml, 3 memory files, 2 `.gitkeep`, `.gitignore` |
| the file list was shown **before** anything was written | | |
| existing `AGENTS.md` content preserved exactly | | compare against the hash above |
| a marker block was appended, and only one | | |
| marker block ≤ 2 KiB | | |
| a Python gate candidate is in `config.yaml` | | |
| **the gate was not executed** | | detection proposes; it must not run anything |
| memory files carry the *data, not instructions* header | | D-04's fix, first real check |

The gate row matters more than it looks. Running a detected command to see whether it
works is precisely the side effect this Skill must not have.

---

## RB-M3-03 — ATS-004, repeated initialization

**Needs:** the state RB-M3-02 left behind. **Costs two model calls.**

Invoke `/agent-harness:init-project` twice more, then:

```bash
git diff --stat
```

| Check | Result | Notes |
| :--- | :--- | :--- |
| `git diff --stat` empty | | zero bytes changed |
| no second marker block | | |
| the Skill said it had nothing to do | | rather than re-proposing the same writes |

The last row is a softer expectation than the first two — but a Skill that silently
rewrites identical content is idempotent by luck rather than by design, and the two look
the same in a diff.

---

## RB-M3-04 — ATS-005, degraded orchestration

**Needs:** a session with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` **unset** — which is the
default, so this is the ordinary path. **Costs several model calls.**

M3's exit criterion names only the Agent-Teams-disabled path. The second condition in
ATS-005 — delegation artificially blocked — is a separate run, and it is not required
here.

Plan a task that `plan-work` grades **`parallel`**, then invoke `/agent-harness:orchestrate`.

| Check | Result | Notes |
| :--- | :--- | :--- |
| the workflow completed without error | | |
| `orchestration_mode` reported as `sequential` | | |
| `degraded_reason` present and non-empty | | |
| the output schema matches the parallel-mode shape | | |
| the result mentions the degradation | | |

> **Read this before recording a failure.** ATS-005's stated verification is that
> `evidence.md` contains those fields. **No M2 or M3 Skill writes `evidence.md`** — the
> run-state runtime is deferred, and `orchestrate` returns evidence in the response only.
> That is dry-run finding D-01 reappearing at the acceptance-test level.
>
> So check the **response** for those fields, and record the substitution explicitly.
> ATS-005 cannot be closed as literally written until the run-state runtime lands, and
> recording a response-based pass as though it were the artifact-based one would hide a
> milestone dependency behind a green checkmark.

---

## RB-M3-05 — Q-IMPL-007, is the tools allowlist enforced?

**Needs:** the fixture at `tests/fixtures/host-tests/agent-tool-enforcement/`. **Costs a
model call.** Read its `EXPECT.md` first — it explains why the obvious version of this
test proves nothing.

```bash
claude --plugin-dir ./tests/fixtures/host-tests/agent-tool-enforcement
```

Then invoke `/m3-tool-enforcement-probe:m3-write-attempt-fixture`.

| Field | Result |
| :--- | :--- |
| the probe's report, **verbatim** | |
| does `.probe-output/attempted-write.txt` exist? | |
| report and filesystem agree? | |

| Outcome | Meaning | Consequence |
| :--- | :--- | :--- |
| no write tool available | **enforced** | Q-IMPL-007 closes; `researcher` and `reviewer` are read-only at tool level |
| the file was written | **not enforced** | the PRD fallback fires: role permissions are instruction-level on this host too, and the Claude/Codex enforcement gap this repository documents does not exist |
| anything else | **inconclusive** | record verbatim, say what would settle it |

Do not soften a *not enforced* result. It would change what `agents/` means, what
`docs/compatibility.md` claims, and the asymmetry table in the PRD — and it is exactly the
kind of finding that gets rounded off because it is inconvenient.

Delete `.probe-output/` afterwards.

---

## After the run

Update, in this order:

1. this file — every row filled, including the ones that failed
2. `plugins/agent-harness/adapters/claude/capability-notes.md` — anything that moves from
   *Documented* to *Observed*, or the reverse
3. `docs/compatibility.md` — Q-IMPL-007, if RB-M3-05 settled it
4. `docs/m1-traceability.md` — the exit criteria this closes

**A negative result is a valid outcome. An unrecorded result is not.**
