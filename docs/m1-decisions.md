# M1 decisions

_Updated M1.3, 2026-08-08. DEF-001 remediated and host-revalidated._

Decision status after the M1.1 pass. The PRD is the source of truth for what these
decisions mean; this file records only their current state and the evidence behind it.

---

## DEC-P13 - dual-manifest co-location

**Status: Proposed.** Advanced substantially in M1.2, but not Confirmed.

Confirmation requires BOTH hosts to accept **and load** a plugin root containing the
other host's manifest directory.

| Half | M1.2 result | Evidence |
| :--- | :--- | :--- |
| Codex accepts a root containing `.claude-plugin/` | **Passed - installed** | `codex plugin add` installed from a root holding both manifests. The install cache preserved `.claude-plugin/`, `.codex-plugin/`, `skills/` and `agents/openai.yaml`. Codex 0.146.0-alpha.9.2 |
| Claude accepts a root containing `.codex-plugin/` | **Validator only** | `claude plugin validate --strict` -> exit 0 with `.codex-plugin/` present. Claude Code 2.1.195 |
| Claude **loads** such a root | **Not Run** | needs an interactive session; not started automatically |

**Why still Proposed.** Claude strict validation proves *validator tolerance*, not
loading. Codex installation is stronger evidence - the host copied and enabled the plugin
- but "loads in both hosts" needs the Claude runtime half, which remains unexercised.

Neither host rejected the foreign manifest directory, so the generated-distribution
fallback has **not** been triggered.

## DEC-P14 - marketplace catalog strategy

**Status: Proposed.** Candidate C is no longer merely untested - on the Codex surface it
**failed**.

| Candidate | Deterministic | Claude validator | Codex CLI | ChatGPT Desktop | Selected? |
| :--- | :--- | :--- | :--- | :--- | :---: |
| A - two hand-edited catalogs | valid | not tested | not tested | not tested | no - violates no-duplication |
| B - one Claude-path catalog | valid in isolation | not tested | not tested | not tested | **no** |
| C - canonical source, generated | valid, byte-deterministic | **Passed** | **Passed (M1.3, after DEF-001 fix)** | not tested | **no - desktop surface untested** |

**DEF-001 is closed.** M1.3 removed the invented `policy.install` and the invalid
`authentication: "none"`, and the corrected catalog was accepted by
`codex plugin marketplace add` on codex-cli 0.146.0-alpha.9.2 (isolated, registration
only). Details: [`m1-defects.md`](m1-defects.md).

Candidate C is now the **provisional implementation strategy with two verified host
surfaces** - Claude strict validator and Codex marketplace registration. It still cannot
be **selected**: the ChatGPT Desktop surface is untested for every candidate, and
Candidates A and B have no Codex or Desktop evidence at all.

Candidate B still cannot be selected: it has no positive evidence on any mandatory
surface. Candidate A remains a baseline experiment, never the long-term design.

**Candidate B is not disqualified by source shape (M1.3.1).** A hand-written or
legacy-path catalog may legitimately use the plain string `source` form; both local forms
are officially documented. The open question for Candidate B remains the one the PRD
names - whether required policy metadata survives on both hosts - not which of two
documented spellings it uses.

## DEC-C25 — canonical Skill frontmatter minimum set

**Status: Confirmed and enforced.**

Canonical `SKILL.md` frontmatter is `name` + `description` only (optional: `license`,
`metadata`). `validate_skills.py` fails on any other key, including Claude-only fields
such as `disable-model-invocation`, because Codex behaviour on unknown keys is
unverified. Covered by NS-17.

---

## DEC-C26 — two independent approval gates for the mutating Skill

**Status: Confirmed. Enforcement deferred with the Skill itself.**

Gate A (host invocation policy) is demonstrated on the discovery fixture, which ships
`agents/openai.yaml` with `allow_implicit_invocation: false`. `validate_skills.py`
enforces the value; covered by NS-18.

Gate B (mutation approval) belongs to `apply-refinement`, which does not exist in M1 —
its enforcement returns in M6 alongside the Skill.

---

## DEC-C27 — registration is not installation

**Status: Confirmed and enforced.**

Marketplace registration and plugin installation are separate lifecycle steps. No
undocumented plugin-install CLI subcommand appears anywhere a reader could copy one;
`check_no_install_command.py` blocks affirmative or executable occurrences while
permitting sentences that record the command's non-existence. Covered by NS-22/NS-22b.

**M1.2 empirical confirmation.** `codex plugin list` reported the plugin as
`not installed` immediately after `codex plugin marketplace add` succeeded, and only
after `codex plugin add` did it become `installed, enabled`. The two steps are distinct
on the real host, not merely in our documentation.

---

## DEC-C28 — hook path variables are not Skill path variables

**Status: Confirmed and enforced.**

`PLUGIN_ROOT` and `PLUGIN_DATA` are documented for plugin **hook** commands. Whether
they are inherited by commands a Skill starts is undocumented, so the canonical layer
must not assume it. `check_path_portability.py` fails on any `PLUGIN_ROOT` reference in
the canonical layer.

Both experiments are defined and separated. Neither has been executed.

---

## M1.1 implementation decisions

Choices made during this pass, recorded so they are reviewable rather than implicit.

| Decision | Rationale |
| :--- | :--- |
| Development tooling uses PyYAML, jsonschema and pytest | An approximation of a published standard can disagree with the real host while still reporting success. Replacing the hand-written parsers immediately exposed three defects they had hidden |
| Plugin runtime keeps zero dependencies | Unchanged, and asserted in CI |
| `preflight.py` retained, labeled non-authoritative | Gives a contributor without the virtual environment a fast answer. Its scope cannot overlap the authoritative validators, so it cannot silently disagree with them |
| Seven production Skill placeholders removed | A shipped `SKILL.md` is host-discoverable regardless of body text, so a placeholder in the installable root is a product surface |
| State schemas kept but relocated | PRD M1 deliverable #4 requires them; separating them prevents their being counted as packaging evidence for E3/E4 |
| `check_invocation_policy.py` removed | Its Gate A check moved into `validate_skills.py`; two scripts asserting the same thing would inflate the check count |
| Diagnostic codes introduced | Tests assert stable codes, not prose, so an upstream rewording cannot weaken the negative suite |

---

## Q-IMPL-011 - can the Codex CLI alone install a plugin?

**Status: Host-verified on codex-cli 0.146.0-alpha.9.2; cross-version and
stable-documentation status remains Open.**

Three claims, deliberately kept apart:

| Claim | Status |
| :--- | :--- |
| the install-class subcommand appeared in actual help output | **Host-Observed**, 0.146.0-alpha.9.2 |
| CLI installation succeeded on that alpha build | **Host-Observed**, isolated, **PROC-001** |
| current public documentation defines it as the stable general installation path | **No** |

The published packaging documentation covers `marketplace add / list / upgrade / remove`
and ChatGPT Desktop installation. It does not establish the install-class subcommand as a
stable cross-version contract. An alpha build demonstrating a capability is real evidence
about that build and nothing more, so this repository does not describe the command as
universally supported and puts no executable example of it in user-facing instructions.

The M1.2 evidence is retained. **M1.3 ran no install-class command.**

---

## DEF-001 - schema fiction exposed by a real host

**Status: Open. Remediation scoped to M1.3.**

M1.1 invented `policy.install: "manual"` and `policy.authentication: "none"` and encoded
them as host facts in two schemas. The real host rejects `"none"` (it expects
`ON_INSTALL` or `ON_USE`) and does not validate `install` at all.

The lesson is narrower than "we made a mistake": a local compatibility schema can assert
a constraint the host does not have, and CI will then enforce a fiction indefinitely.
M1.3 should audit every enum in the compatibility schemas for values that were reasoned
rather than observed.


---

## DEF-001 - CLOSED in M1.3

The invented `policy.install` and the invalid `authentication: "none"` were removed and
replaced with the documented contract: `installation: AVAILABLE`,
`authentication: ON_INSTALL`, `category: Productivity`. `source` is emitted in the object
form. Revalidated on the real host, registration only.

**No compatibility alias was kept for `policy.install`.** A misspelling must fail
validation, not be silently repaired - a silent repair would hide exactly the class of
error that produced the defect.

**DEF-001 covers three things only:** the invented `policy.install`, the invalid
`authentication: "none"`, and the circular local-schema validation that recorded our own
invention as host evidence. The plain string `source` form is **not** one of them - it is
a documented local representation and was never a defect. M1.3 associated the two; M1.3.1
separates them.

### What the schema layer learned

Every enum in the compatibility schemas now carries a `$comment` naming its evidence
level, and the full field-by-field tables live in [`m1-defects.md`](m1-defects.md).

A local compatibility schema can assert a constraint the host does not have, and CI will
then enforce that fiction indefinitely. The disclaimer "host behaviour remains
authoritative" does not prevent this; only evidence-per-field does.

**M1.3.1 found the mirror image of that failure.** While removing invented constraints,
M1.3 also removed *real* ones: kebab-case on the Claude marketplace `name` and
`plugins[].name`. Both are documented by the vendor. For the interval between M1.3 and
M1.3.1 the schemas accepted `"Agent Harness"` - a value the Claude validator rejects - as
an identifier. Only the `category` pattern was genuinely an M1.1 invention, and it stays
removed.

So an evidence audit cuts both ways. Deleting a constraint needs the same proof as adding
one: "I could not find where this came from" is a reason to go and check the source, not a
finding. The corrective rule is now in [`CONTRIBUTING.md`](../CONTRIBUTING.md) - a
constraint may be removed only with a citation showing the vendor does not require it, and
a test that fails without it.


---

## DEC-P13 after M1.4A — runtime co-location verified, decision still Proposed

**Status: Proposed.** Unchanged, deliberately.

Co-location now has real runtime evidence on both hosts:

| Host | Evidence | Version scope |
| :--- | :--- | :--- |
| Claude Code | loaded the co-located root with `--plugin-dir`, `scope: session`, and listed the fixture Skill in its component inventory | **2.1.195** |
| Codex CLI | installed from the co-located root; both manifests and `skills/` survived in the isolated cache | **0.146.0-alpha.9.2**, PROC-001 protocol-deviating |

So why is the decision not promoted?

**Because the PRD says what promotion costs, and this phase cannot pay it.** §22 ATS-018
states that on success DEC-P13 is promoted to Confirmed and FR-001's `[C]` becomes `[V]`
— *"(PRD 개정 필요)"*, requiring a PRD revision. M1.4A forbids modifying `docs/PRD.md`.
§1.1 defines **Confirmed** as an already-settled architecture direction the PRD is
premised on, changed only by PRD revision, and **Proposed** as changed by review approval
or rejection. Neither transition is something an evidence-gathering phase performs on its
own.

The substantive reason is stronger than the procedural one: E5's promotion clause requires
**all seven** ATS-018 checks. Three pass. 018-4 (Codex Skill discovery), 018-5 (neither
host parsing the other's manifest) and the runtime halves of 018-6 and 018-7 have no
evidence. Two hosts loading a directory is not yet proof that each ignores the other's
manifest.

**Recorded instead:** runtime co-location is **Verified for Claude Code 2.1.195 and
codex-cli 0.146.0-alpha.9.2**. Future host versions remain subject to regression testing;
nothing here claims cross-version compatibility. The PROC-001 qualifier on the Codex half
stands and is not concealed.
