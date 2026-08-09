# M2 contract dry-run — findings

_2026-08-09. Run against a disposable Python repository with passing tests._

> **D-01 and D-02 are resolved** (see *Resolution* at the end). D-03, D-04 and D-05 remain
> open decisions. A sixth defect, D-06, was found while fixing them.

## What this is, and what it is not

**This is not the pilot.** [`m2-pilot-plan.md`](m2-pilot-plan.md) still needs running, and
[`m2-pilot-record.md`](m2-pilot-record.md) is still blank on purpose.

What happened here: the Skill instructions were followed **literally** against a real
repository, checking whether following them is even possible and whether the result is
coherent. No host invoked anything; the Skills were read as documents and executed by hand.

### What it cannot produce

- **Adherence evidence.** The same author wrote these Skills and followed them. "Did a
  model that has never seen this follow it?" is the pilot's central question and this
  exercise cannot answer it.
- **Host discovery or Gate A.** Nothing was invoked as `/agent-harness:doctor`. Whether
  the host resolves the Skills, and whether the invocation policy actually suppresses
  implicit selection, is untested.
- **Real delegation.** `orchestrate`'s subagent path was not exercised.

### What it can produce, and did

**Contract defects** — places where following the instruction literally leads to a gap, a
contradiction, or an impossible step. Four found, two of them structural.

## Target repository

A disposable Python project: `src/calc.py`, `src/test_calc.py` (4 tests, all passing),
`pyproject.toml` with `[tool.pytest.ini_options]`, a README, and a Git repository. Chosen
so detection has real signals and the verification gate has something true to report.

---

## D-01 — the seven Skills do not connect end to end

**Kind: C (contract defect). Severity: highest.**

`refine-harness` requires, per its own Input section: *"Each source run needs its
`plan.md`, `evidence.md` and `result.md`."*

**No Skill in M2 writes `evidence.md` or `result.md`.** Both `orchestrate` and
`verify-work` declare `evidence_persistence: response-only`, and the run-state runtime is
deferred by design.

Therefore `refine-harness` has **no possible input in this milestone**, and
`apply-refinement` — which consumes what `refine-harness` produces — has nothing to apply.
**Two of the seven Skills are structurally unreachable.**

Each deferral was individually defensible. Their composition was never checked, because
every Skill was validated in isolation: 624 tests, and **not one asserts that the pipeline
connects**. This is the "union of verified facts is not a verified architecture" failure
mode the PRD names for manifests — appearing here at the workflow level.

**Options** (a decision, not a fix to apply silently):

1. Have `verify-work` and `orchestrate` write `evidence.md`/`result.md` — reverses a
   deliberate M2 deferral.
2. Let `refine-harness` accept a response-only transcript — weakens the evidence-reference
   contract that makes proposals auditable.
3. Accept it and state plainly that the refinement half of the product needs the run-state
   runtime. Honest, and it makes M5 a hard prerequisite rather than a later nicety.

Recommendation: **3 now, 1 in M5.** Documenting the gap costs nothing and stops someone
discovering it mid-pilot; reversing a deferral to close it would be the tail wagging the
dog.

---

## D-02 — the proposed Python gate reports a false failure

**Kind: C (proposed default) + U (unenforceable by classification). Severity: high.**

PRD §15.2 and `init-project`'s `config-template.yaml` both propose:

    command: ["python", "-m", "pytest", "-q"]

On the dry-run machine — Windows, project in a virtualenv — `python` resolves to a stub
that prints one word, runs nothing, and exits 1.

Observed, with all four tests genuinely passing:

| Path | Result |
| :--- | :--- |
| the venv interpreter | 4 passed |
| the proposed gate command | exit 1, no tests run |
| `verify-work` classification | **`fail`** — correct per §15.4: the process ran and exited non-zero |
| overall | `verification_status: failed` on a project whose tests pass |

**No classification can catch this.** `error` means the executable was not found or could
not execute; here it *was* found and *did* execute — it simply is not Python. A stub that
exits non-zero is indistinguishable from a test suite that fails.

**And `doctor` reports the executable as fine.** Its EXE-01 check asks whether the gate's
executable appears available; `python` is on `PATH`, so the answer is `ok`. The two Skills
disagree in the worst direction: verification says the work is broken, diagnosis says the
setup is healthy, and neither is wrong under its own contract.

**Options:**

1. Propose `[sys.executable, "-m", "pytest", "-q"]`-equivalent detection — i.e. resolve
   the interpreter that owns the project rather than the name `python`.
2. Have `init-project` warn when the proposed interpreter is not the one running the
   project's tooling.
3. Add a `doctor` check that the gate interpreter is a *plausible* interpreter, not merely
   a file on `PATH`.

This one is worth fixing before the pilot: it will fire on any Windows contributor, and
its symptom — "verification says my passing tests failed" — is the most alarming possible
first impression.

---

## D-03 — `doctor` has no vocabulary for "not applicable"

**Kind: C. Severity: medium.**

`doctor` defines exactly four statuses — `ok`, `warn`, `fail`, `unknown` — and a fixed
report with sections for Configuration, Memory, Verification executables and Host
instructions. Its diagnostic matrix carries an **Applies** column.

Nothing connects the two. Run `doctor` on an uninitialized repository — the first thing
anyone will do, and the flow the Skill itself describes — and Configuration, Memory and
Verification have nothing applicable. The four statuses offer no way to say so:

- `unknown` is wrong — we know precisely why they do not apply.
- Omitting the sections contradicts the fixed report shape.
- `n/a` is not one of the four.

The phrase "not applicable" appears once in the whole Skill, in a different context
(unimplemented Skills being absent), so a reader has no rule to follow.

**Option:** state that a check whose **Applies** condition is unmet is reported as *not
applicable* with its reason, and that not-applicable never affects the overall result.
That is a wording change, not a new status.

---

## D-04 — `init-project` never says what goes in the memory files

**Kind: C. Severity: medium.**

`init-project` creates `.agent-harness/memory/facts.md`, `decisions.md` and `patterns.md`,
described only as "durable project facts", "decisions and their rationale", "reusable
procedures".

**It never says what to write in them.** Meanwhile `plugins/agent-harness/templates/`
contains `memory-facts.md`, `memory-decisions.md` and `memory-patterns.md`, and the plugin
README says templates are "files init-project will copy" — but the Skill **never mentions
`templates/`**.

So three of the seven files it creates have undefined content. A model will invent
headings, and a different model will invent different ones. That does not break the
idempotency test as written — a second run by the *same* model produces no diff — but it
means the files' structure is not actually specified by anything, while a specification
sits unused one directory away.

**Option:** have `init-project` reference the template files as the content source. That
also gives the templates directory a consumer, which it currently lacks.

---

## D-05 — project-type detection pulls two ways

**Kind: C/A? Severity: low.**

The target repository is unambiguously Python: `pyproject.toml` with
`[tool.pytest.ini_options]`, `src/*.py`, `test_*.py`. The schema allows `python`.

Following the instructions, the first config produced said `type: [generic]` — because
`init-project` says *"Infer project type **conservatively**"* and the shipped template
carries `type: [generic]` with the comment *"Use [generic] when unsure"*, while the
detection table in the same file lists the exact Python signals present.

Recorded as **C/A?** deliberately: it may be my own adherence slip rather than a contract
defect, and **this exercise is structurally bad at telling those apart** — I wrote both
documents. The pilot should watch this specific field.

---

## Summary

| Skill | Reached | Outcome |
| :--- | :--- | :--- |
| `doctor` | yes, statically | D-03 |
| `init-project` | yes, files created and schema-validated | D-04, D-05 |
| `plan-work` | not exercised | needs a model |
| `verify-work` | yes, gates executed | **D-02** |
| `orchestrate` | not exercised | needs delegation |
| `refine-harness` | **cannot be reached** | **D-01** |
| `apply-refinement` | **cannot be reached** | **D-01** |

| | Count |
| :--- | ---: |
| Contract defects (**C**) | 4 |
| Unenforceable (**U**) | 1 (D-02's classification half) |
| Unclassified (**C/A?**) | 1 |
| Adherence failures (**A**) | **0 — this exercise cannot detect them** |

Per the M1.2 protocol: recorded, not patched. Every option above is a decision to make,
not a change already applied.

## What this changes about the pilot

The pilot plan asked for five deliberate breaks. Two of them can no longer be run as
written — `refine-harness` and `apply-refinement` have no reachable input until D-01 is
resolved. **Fix D-01 and D-02 first, then run the pilot**; otherwise the session will
spend its most expensive resource, a real model on a real host, rediscovering two defects
already known.

Config schema validation held throughout: every `config.yaml` produced by following the
instructions validated against `config.schema.json` on the first attempt.


---

## Resolution

D-01 and D-02 were fixed; the rest remain open.

### D-01 — resolved by stating the prerequisite, not by reversing a deferral

`refine-harness` now opens with a **Prerequisite** section: it reads run artifacts it does
not create, the run-state runtime that writes them is deferred, so in this milestone there
are usually no source runs and the correct output is *no proposal* naming what is missing.

The section also forbids each tempting workaround by name — accepting a transcript in place
of `evidence.md`, reconstructing evidence from a response, relaxing the evidence-reference
requirement. Any of those would produce a proposal citing evidence nobody wrote down,
which is the unauditable artifact the evidence rule exists to prevent.

Options 1 and 2 from the original finding were rejected. Reversing a deliberate M2 deferral
to close a documentation gap is the tail wagging the dog, and weakening the evidence
contract trades the property that makes proposals reviewable for the appearance of a
working pipeline.

A test asserts the fact D-01 rests on — both producers still declare
`evidence_persistence: response-only` — so a future change that starts persisting evidence
fails until this note is updated to match.

### D-02 — resolved at the source, plus a diagnosis that no longer disagrees

- `init-project` now requires proposing **the interpreter that owns the project** — its
  virtualenv, its version manager — never the bare name, and saying so in the proposal when
  no project interpreter can be identified.
- `config-template.yaml` no longer ships `["python", "-m", "pytest", "-q"]`. It shows
  `["<interpreter>", …]` with a preference order and names the Windows stub explicitly.
- `doctor`'s EXE-01 now reports **`warn`**, not `ok`, for a bare interpreter name when the
  project carries its own. Previously diagnosis called the environment healthy while
  verification called the work broken, and both were right under their own contracts.

**This diverges from PRD §15.2**, whose table proposes `["python", …]`. That table
introduces itself as candidates `init-project` *proposes*, not a fixed requirement, so
refining a candidate stays inside the contract. Recorded here rather than changing the PRD.

### D-06 — `doctor` still expected three Skills to be missing

**Kind: C. Found while fixing D-02.**

`doctor` listed the implemented set as four Skills and stated that `orchestrate`,
`refine-harness` and `apply-refinement` are *"not yet implemented — their absence is
expected and is never a fail"*. All seven shipped in M2, so a correct installation would
have been diagnosed against a stale expectation.

Fixed: PKG-04 now expects all seven, and PKG-06 — which existed only to say three were
expected absent — was repurposed to guard the other direction, an unrecognised Skill
directory in the installable root.

Worth noting how it survived: the doctor tests asserted the *old* sentence, so completing
M2 made the product wrong and the suite still green. The replacement test derives the
expected set from `PLANNED_PRODUCTION_SKILLS` instead of restating it.

### Still open

D-03 (no *not applicable* vocabulary), D-04 (memory file content undefined, `templates/`
unreferenced), D-05 (project-type detection pulls two ways). Each is a decision, and none
blocks the pilot.
