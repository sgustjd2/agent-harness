# M4 manual host runbook — Codex and the OpenAI surfaces

M4's exit criteria are **ATS-002**, **ATS-019**, **MET-003 parity**, a documented answer
for **Q-IMPL-002/003/004**, and a real test of **Gate A recognition** on this host.

This page is both the procedure and the record. **Fill it in as you go.**

Do not paste tokens, credentials, whole config files, or full logs. Capture only the
fields each step names.

> **There is no free non-interactive step here.** On the Claude side, `plugin details`
> gave a component inventory for nothing — no session, no model, no state. Codex has no
> equivalent read-only inventory command, and the commands that exist read or write real
> `CODEX_HOME` state. So unlike `docs/m3-host-runbook.md`, nothing below is pre-filled,
> and every step needs a person who has decided to run it.

## Session

| | |
| :--- | :--- |
| Date | |
| Surface | Codex CLI / IDE / ChatGPT desktop |
| Host version | e.g. codex-cli 0.146.0-alpha.9.2 |
| `CODEX_HOME` isolated? | **yes / no** — say which |
| Target repository | **disposable copy?** yes / no |
| `.codex/agents/` before | file list, or empty |
| `~/.codex/agents/` before | file list, or empty |

Record both agent directories **before you start**. ATS-019 is verified by comparing
those lists across every step, and a list captured afterwards is not a before.

## How to classify a failure

| Code | Meaning | Where the fix goes |
| :--- | :--- | :--- |
| **C** | contract defect — the file says the wrong thing, or says nothing | the `SKILL.md`, template, or adapter |
| **A** | adherence failure — the file is right, the model did not follow it | clearer or more prominent wording |
| **U** | unenforceable by instruction — no wording would reliably hold | a validator, schema field, or host policy |

---

## RB-M4-01 — ATS-002, the whole workflow with zero custom agents

**Needs:** a Codex environment with agent-harness never installed and **both agent
directories empty**. Costs several model calls.

Follow `install-codex.md`. Then run `plan-work` → `orchestrate` → `verify-work` on a small
real task.

| Check | Result | Notes |
| :--- | :--- | :--- |
| marketplace registration succeeded | | |
| installation succeeded | | which surface? |
| 7 Skills recognized under `$` invocation | | **this is E6** |
| the three-Skill workflow completed | | with **no** custom agent installed |
| project files unchanged by installation | | |
| both agent directories still empty | | |

**Row 3 is the one that has never been observed.** Registration and cache preservation
show the files arrive; nothing yet shows the host offers them. A failure here is E6
answering, not a mistake in the procedure.

**Row 4 is the requirement the whole design rests on.** Working without templates is the
baseline, not a degraded mode — if it fails, the optional templates have quietly become
mandatory and FR-021's premise is wrong.

---

## RB-M4-02 — ATS-019 (a), no unauthorized installation

**Needs:** the state RB-M4-01 left behind.

Nothing to do beyond looking. After a complete ordinary run:

| Check | Result |
| :--- | :--- |
| `.codex/agents/` still exactly as recorded before | |
| `~/.codex/agents/` still exactly as recorded before | |

**This is the Must-priority half of FR-021**, and it should be impossible to fail:
`.codex/` and `.claude/` are forbidden write roots, so no Skill can declare the path, let
alone write it. A failure here means a Skill acquired a write surface nobody granted — a
finding well beyond ATS-019.

---

## RB-M4-03 — ATS-019 (b), (c), (d): **not testable as written**

Read this before recording anything for those three scenarios.

They describe a Skill that **offers** template installation: presents the file list and
target, stops when the user does not approve, validates and copies when they do.

**No such Skill exists, and none can be built yet.** A canonical Skill cannot locate
`adapters/codex/agent-templates/` — no path variable, no cache path, no working
directory — which is **Q-IMPL-003**, open since M1. It is the same blocker that stopped
`init-project` reading `templates/` (dry-run finding D-04).

So the approval flow was not deferred out of convenience. **It was replaced by a manual
procedure**, which satisfies the same requirements by a different route:

| FR-021 rule | Scenario | How it is met now |
| :--- | :--- | :--- |
| 3 — approval before installation | (b), (d) | the user performs the copy; there is no agent to approve |
| 4 — project scope default | (b) | `install-codex.md` documents `.codex/agents/` and says why user scope hides the change |
| 5 — validate before copying | (d) | `validate_agent_templates.py` in CI, plus a read-it-first step in the guide |
| 6 — never silently | (a) | no Skill can write the path at all |
| 7 — documented removal | (e) | RB-M4-04 |

**Record these three as `not applicable — no offering Skill exists (Q-IMPL-003)`.** Do not
mark them passed. Nothing was tested, and a pass here would claim an approval flow was
verified when there is no flow to verify.

This is the same shape as ATS-005 in `m3-host-runbook.md`: an acceptance test whose
subject a milestone deferred. Both are recorded rather than quietly satisfied.

---

## RB-M4-04 — ATS-019 (e), manual install and removal

**Needs:** a git repository, so the copy is visible in a diff.

```bash
mkdir -p .codex/agents
cp plugins/agent-harness/adapters/codex/agent-templates/researcher.toml .codex/agents/
git status --short
```

| Check | Result | Notes |
| :--- | :--- | :--- |
| the copy appears in `git status` | | the visibility the mitigation depends on |
| `~/.codex/agents/` untouched | | project scope only |
| `$doctor` reports it as **`info`**, not `ok` | | observation, not endorsement |
| the host recognizes the agent | | or does not — record which |
| after `git rm`, the workflow still runs | | ATS-019 (e), and FR-021 AC-7 |

Row 3 is worth attention. `ok` would mean `doctor` approved of the installation, and it
never evaluated it.

---

## RB-M4-05 — Gate A on this host (M4 exit criterion 5)

**Needs:** a session, and a prompt that would plausibly select a mutation Skill on its own.

`apply-refinement` carries `agents/openai.yaml` with
`policy.allow_implicit_invocation: false`.

| Check | Result |
| :--- | :--- |
| a prompt that *describes* applying a refinement does **not** auto-select it | |
| explicit `$apply-refinement` still works | |
| the same holds for `init-project`, `verify-work`, `orchestrate`, `refine-harness` | |

**Both rows matter equally.** A policy that blocked implicit selection *and* explicit
invocation would look like a pass on the first row while having broken the Skill.

**Gate A is not Gate B.** Gate B — approval bound to a shown proposal — must hold even if
this whole step fails, because Claude Code has no Gate A at all. If a failure here looks
like it also weakens Gate B, that is a separate and more serious finding.

---

## RB-M4-06 — MET-003, cross-host parity

**Needs:** RB-M4-01's output, and the same task run on Claude Code.

| Check | Result |
| :--- | :--- |
| both hosts expose the same 7 Skill names | |
| both hosts offer the same 6 roles | |
| output structures match, ignoring timestamps and run ids | |
| any difference that is **not** invocation syntax | |

Row 4 is the real question. Invocation differs by host and always will; anything else
differing is drift, and parity is what this project claims to provide.

---

## Q-IMPL status after M4

Exit criterion 4 asks for **documented answers**, not resolved questions.

| ID | Question | Status | What settles it |
| :--- | :--- | :--- | :--- |
| **Q-IMPL-002** | Does Codex ignore or reject unknown `SKILL.md` frontmatter keys? | **Open — and nothing depends on it** | add one unknown key to a fixture Skill and load it |
| **Q-IMPL-003** | How does a canonical Skill locate a bundled script? | **Open — designed around** | `ATS-020`, both hosts |
| **Q-IMPL-004** | Private-repository authentication | **Open — out of the MVP path** | a private repository and a real registration |

**Q-IMPL-002 is answered in the sense that matters:** the canonical frontmatter is
`name` + `description` only, which is the documented intersection of both hosts. That was
chosen *because* the answer was unknown, so the design is safe under either. Testing it
would let a future Skill carry a host-specific key — that is a widening, not a fix, and it
is why this stays open rather than urgent.

**Q-IMPL-003 shapes three decisions already**: no bundled helper execution, no Skill
reading `templates/` (D-04), no Skill copying agent templates (RB-M4-03). Each is recorded
where it bites rather than in one place nobody reads.

**Q-IMPL-004** matters only for private-repository installation, which no milestone
depends on.

---

## After the run

1. this file — every row, including the ones that failed
2. `plugins/agent-harness/adapters/codex/capability-notes.md` — anything moving between
   *Documented*, *Observed* and *Open*
3. `docs/compatibility.md` — E6 and the Q-IMPL table
4. `docs/m1-traceability.md` — exit criteria this closes

**A negative result is a valid outcome. An unrecorded result is not.**
