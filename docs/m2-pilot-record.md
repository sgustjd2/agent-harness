# M2 pilot record — fill this in as you go

Companion to [`m2-pilot-plan.md`](m2-pilot-plan.md). The plan says what to do; this is
where the answers go.

**Fill it in as you go, not afterwards.** A record written from memory at the end is where
"it mostly worked" comes from.

## Session

| | |
| :--- | :--- |
| Date | |
| Host and version | e.g. Claude Code 2.1.195 / codex-cli … |
| Plugin loaded how | `--plugin-dir` / marketplace install / other |
| Skills visible | expect **8** — fixture + 7 production |
| Target repository | **disposable copy?** yes / no |
| What isolation did **not** cover | |

## How to classify a failure

Every "no" below gets one of these. Getting this right is the point of the exercise —
the three have different fixes, and conflating them sends the next change to the wrong place.

| Code | Meaning | Where the fix goes |
| :--- | :--- | :--- |
| **C** | **contract defect** — the Skill says the wrong thing, or says nothing | the `SKILL.md` or a reference |
| **A** | **adherence failure** — the Skill says the right thing, the model did not follow it | clearer or more prominent wording |
| **U** | **unenforceable by instruction** — no wording would reliably hold | a validator, schema field, or host policy instead of prose |

If you cannot tell C from A, write **C/A?** and paste what the Skill actually says next to
what the model actually did. That pair is enough for me to classify it later; a verdict
without it is not.

## Phase 1 — the seven Skills

### P1-1 `doctor`, before initialization

| Check | Result | Kind | Note |
| :--- | :--- | :--- | :--- |
| `.agent-harness/` missing → `fail` with `init-project` remediation | | | |
| only `ok`/`warn`/`fail`/`unknown` used | | | |
| ran every applicable check — **did not stop at the first `fail`** | | | |
| overall `broken` | | | |
| **executed nothing** — no `--version`, `which`, PATH probe | | | |

### P1-2 `init-project`

| Check | Result | Kind | Note |
| :--- | :--- | :--- | :--- |
| Phase A proposed every path and wrote nothing | | | |
| asked for approval — invocation alone did not start the write | | | |
| created config, 3 memory files, `runs/`, `proposals/`, `.gitignore` | | | |
| gates proposed, **none enabled, none executed** | | | |
| one marker block; content outside it untouched | | | |
| **break 1 — second run produces no diff** (`git diff`) | | | |

### P1-3 `plan-work`

Goal given: ______________________________________________

| Check | Result | Kind | Note |
| :--- | :--- | :--- | :--- |
| tasks have completion conditions and dependency order | | | |
| `AC-01…`, `V-01…` present | | | |
| every verification item `Not Run` | | | |
| wrote nothing unless explicitly asked | | | |
| claimed nothing as passing | | | |

### P1-4 `verify-work`

| Check | Result | Kind | Note |
| :--- | :--- | :--- | :--- |
| **no gates configured → `Blocked`**, no fallback guess | | | |
| after configuring one gate: showed the gate set and asked | | | |
| classification from the six PRD values | | | |
| `verification_status` reported | | | |
| evidence bounded and redacted; command shown as argv | | | |
| **break 2 — missing executable → `error`** (not `Blocked`, not `fail`) | | | |

### P1-5 `orchestrate`

| Check | Result | Kind | Note |
| :--- | :--- | :--- | :--- |
| no ready plan → `Blocked` recommending `plan-work` | | | |
| **ran no commands**; command-dependent task `blocked` with reason | | | |
| changed files stayed inside each task's `writes[]` | | | |
| wrote nothing under `.agent-harness/**` | | | |
| never declared `completed`; recommended `verify-work` | | | |
| sequential run recorded a non-empty `degraded_reason` | | | |
| **break 3 — `writes[]` missing a needed file → scope violation** | | | |

### P1-6 `refine-harness`

| Check | Result | Kind | Note |
| :--- | :--- | :--- | :--- |
| exactly one file under `.agent-harness/proposals/` | | | |
| every item cites a `<run-id>#<evidence-id>` that resolves | | | |
| `status: proposed` | | | |
| `memory/**` unchanged | | | |
| repeated fact → `sources[]` update, not a second entity | | | |
| `current_hash` trustworthy or `null` — never invented | | | |
| **no usable evidence → no proposal at all**, with the reason | | | |

### P1-7 `apply-refinement`

| Check | Result | Kind | Note |
| :--- | :--- | :--- | :--- |
| presented the file list and diff, then asked | | | |
| **break 4 — declined once → nothing changed** (verify hashes) | | | |
| rollback recorded **before** the first write | | | |
| ran only configured gates | | | |
| **break 5 — gate broken → everything reverted, `status: failed`** | | | |
| a `skill` item, if present, was **refused** | | | |

**Break 4 is the most important line in this document.** FR-015 AC-1 requires target file
hashes to be unchanged after a run that ended without approval. Record the hashes.

## Phase 2 — M1 criteria this session can close

| Criterion | Attempted | Result | Note |
| :--- | :--- | :--- | :--- |
| **E6** — Codex recognises the fixture as a `$` invocation target (ATS-018-4) | | | |
| **E13** — hook-root runtime | | | |
| ATS-018-5 — neither host parses the other's manifest | | | |
| ATS-018-6 — Claude half of cache preservation | | | |

**E12** (ChatGPT Desktop marketplace) is out of scope here — see the plan.

## Summary

| | Count |
| :--- | ---: |
| Skills invoked | / 7 |
| Deliberate breaks attempted | / 5 |
| Contract defects (**C**) | |
| Adherence failures (**A**) | |
| Unenforceable (**U**) | |
| Unclassified (**C/A?**) | |

## Defects found

One block each, following the M1.2 protocol — record, stop that step, **do not patch
silently**, continue the rest.

    ID:
    Skill:
    What the contract says:
    What actually happened:
    Kind: C / A / U / C/A?
    Evidence (redacted):
    Proposed scope:

## Anything the plan did not anticipate

Free text. This is often the most useful section — the plan was written by someone who had
never run the thing either.
