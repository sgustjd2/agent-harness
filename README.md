# agent-harness

A vendor-neutral agent workflow layer for **Claude Code** and **OpenAI Codex**,
distributed from one GitHub repository.

It provides no model and no runtime. It provides a procedure: decompose work into roles,
delegate through the host's own subagents, record plan / evidence / result as files in
your repository, refuse to claim completion until your verification gates pass, and turn
accumulated evidence into reviewable proposals that apply only when you say so.

> **한국어 안내** — 용도, 설치, 세팅, 사용 흐름은 [한국어 안내](#한국어-안내)를 보세요.

---

## Status: M2 complete — all seven production Skills, host verification still pending

**M2 is complete.** M1 built the repository skeleton and the validation pipeline, and
verified the packaging contract against real hosts. M2 added all seven production Skills,
one vertical slice at a time.

**`plan-work` is the first production Skill.** It is **read-only by default**: it
produces plans, and it does not implement them. It writes no source, changes no
configuration, runs no command, and creates a file only when you explicitly ask it to
save a plan.

**`init-project` is the second production Skill.** It initializes portable project state
— `.agent-harness/` with configuration, memory files, and run and proposal directories —
and links it to `CLAUDE.md` or `AGENTS.md`. It is **approval-gated**: it inspects the
repository, shows every path it would write, and applies nothing until you approve that
specific proposal. It **does not execute the verification commands it detects**; it
proposes them and leaves them disabled until you say otherwise.

**`verify-work` is the third production Skill.** It **executes the verification gates
already configured** in `.agent-harness/config.yaml` -- and only those. It **never guesses
a command**, requires **explicit approval of the exact gate set** before running anything,
installs no packages, and edits no source or configuration. Commands are argv arrays with
a required timeout, run sequentially. A command that exists is not a command that passed:
it reports `Passed` only on an observed exit code of 0.

**`doctor` is the fourth production Skill.** It diagnoses **agent-harness itself** --
installation, environment, config and memory integrity -- and reports `ok` / `warn` /
`fail` / `unknown` per check with a suggested fix. **`verify-work` verifies your project
code; `doctor` diagnoses the harness.** In this M2 slice `doctor` is **read-only and
executes no commands at all** -- not even `--version` or a PATH lookup -- and it repairs
nothing.

**`orchestrate` is the fifth production Skill.** It **consumes a ready plan** and
carries it out: walking the dependency graph, delegating independent tasks in parallel
when the host and the plan's write scopes allow it and running sequentially otherwise.
**It delegates only within the plan's boundaries** -- planned paths, repository-contained,
with `.agent-harness/**` read-only -- and **real source changes may occur**. It **executes
no commands** in this milestone; `verify-work` remains the only Skill that runs configured
commands. It never declares the work complete; `verify-work`
owns that. **Automatic run-state persistence remains deferred**: no `evidence.md` or
`result.md` is written in this milestone.

**`refine-harness` is the sixth production Skill.** It **analyzes run evidence** --
`plan.md`, `evidence.md`, `result.md` from completed or failed runs -- and **writes one
local proposal** at `.agent-harness/proposals/<id>.md`. **It does not apply it**: every
item cites real evidence, conflicts are preserved rather than resolved, and the proposal
stays at `status: proposed` until a human reviews it — `apply-refinement` is what applies
one, and only after its own approval gate.

**`apply-refinement` is the seventh and final production Skill.** It applies **one**
approved proposal, only to the paths that proposal names, only after approval bound to
that specific proposal -- then verifies and records how to undo it. It **refuses to modify
the plugin's own Skills**, and **reverts everything if verification fails**.

**This is not a stable release.** Remaining M1 host verification is still a release
blocker -- Codex Skill discovery, the ChatGPT Desktop surfaces, and the hook and
helper-script runtime experiments are unfinished. Treat all seven Skills as
experimental.

| Milestone | Content | State |
| :--- | :--- | :--- |
| M0 / M0.1 / M0.2 | PRD, corrections, decisions | done — [`docs/PRD.md`](docs/PRD.md) |
| M1 | repository + validation scaffold | done |
| M1.1 | scaffold correction and scope audit | done |
| M1.2 | real-host verification | done |
| M1.3 / M1.3.1 | OpenAI marketplace contract remediation and evidence correction | done |
| M1.4A | Claude non-interactive load and component discovery | done |
| M1.4B | Codex Skill discovery, ChatGPT Desktop, hooks, helper execution | **not started** |
| **M2** | **shared Skill bodies — all seven implemented** | **done** |
| **M3** | **Claude Code adapter — role subagents, adapter layer, manifest, host runbook** | **built** — exit criteria need a host session |
| **M4** | **Codex adapter — role templates, adapter layer, install guide, host runbook** | **built** — exit criteria need a host session |
| **M5** | **portable memory and verification — run state, gates, examples** | **in progress** — 3 of 4 slices |
| M6–M8 | refinement, pilot, release | not started |

**Exit criteria: 14 of 17 met.** The three unmet criteria all need host access that this
phase deliberately did not take — see [`docs/m1-traceability.md`](docs/m1-traceability.md).

The installable plugin root contains the compatibility fixture and **all seven**
production Skills. The workflow they form:

`init-project` → `plan-work` → `orchestrate` → `verify-work`, with `doctor` diagnosing the
harness and `refine-harness` → `apply-refinement` turning what a run learned into a
reviewed change.

---

## Repository layout

```
marketplace/marketplace.source.json   canonical catalog source -- the only hand-edited catalog
.claude-plugin/marketplace.json       GENERATED Claude catalog
.agents/plugins/marketplace.json      GENERATED OpenAI catalog

plugins/agent-harness/                the installable plugin. Self-contained.
  .claude-plugin/plugin.json            Claude manifest
  .codex-plugin/plugin.json             Codex manifest, "skills": "./skills/"
  skills/m1-discovery-fixture/          compatibility fixture, inert by design
  skills/plan-work/                     production Skill, read-only
  skills/init-project/                  production Skill, approval-gated
  skills/verify-work/                   production Skill, bounded execution
  skills/doctor/                        production Skill, read-only diagnostics
  skills/orchestrate/                   production Skill, plan-bounded delegation
  skills/refine-harness/                production Skill, proposal-only
  skills/apply-refinement/              production Skill, approved application
  core/schemas/                         five packaging schemas
  core/schemas/state/                   state schemas -- NOT packaging evidence
  adapters/{claude,codex}/              host integration + experiment records

scripts/                              development and CI only, never installed
tests/                                pytest suite + host-test fixtures
docs/                                 PRD, M1 records, compatibility
```

Nothing under `plugins/agent-harness/` may reference anything outside it, and that is
enforced rather than intended.

---

## Dependencies

**The plugin runtime has no required third-party dependency, and must keep none.** CI
asserts the plugin root declares no manifest or lockfile.

**Development validation uses established libraries**, because an approximation of a
published standard can disagree with the real host while still reporting success:

| Concern | Library |
| :--- | :--- |
| YAML parsing | **PyYAML** (`yaml.safe_load`) |
| JSON Schema validation | **jsonschema** (draft taken from each schema's `$schema`) |
| Test running | **pytest** |

---

## Running the checks

```bash
python -m venv .venv
```

```bash
.venv/bin/pip install -r requirements-dev.txt
```

```bash
python scripts/validate_all.py
```

`validate_all.py` runs the 12 deterministic validators once each, then pytest. It
orchestrates; it does not replace pytest. Manual host tests are never run by it.

```bash
python -m pytest -q
```

```bash
python scripts/m1_status.py
```

---

## Three things worth knowing

**Registering a marketplace is not installing a plugin.** On the OpenAI side the Codex
CLI registers a *source*; installation happens in the ChatGPT desktop app. Whether the
CLI alone can install is unverified, so nothing here depends on it.

**Claude validation and OpenAI validation are different things.** `claude plugin
validate` is a real host validator and it passes. The Codex artifacts are checked
against *local compatibility schemas*, because no official Codex validator was found.
The two are never conflated.

**Claude loads the co-located plugin root and discovers the fixture Skill.** Verified
non-interactively on Claude Code 2.1.195: `claude --plugin-dir ./plugins/agent-harness
plugin list --json` loads it as a session-scoped plugin with no installed record, and
`plugin details` reports `Skills (1) m1-discovery-fixture` with zero agents, hooks, MCP and
LSP servers. Loading and discovery are recorded as **separate** facts, and **Skill
invocation is still Not Run** — that needs a model.

**Two architecture decisions remain Proposed.** Whether both manifests can share one
plugin root, and which marketplace catalog strategy to adopt. Candidate C is
implemented *provisionally* so catalogs are generated rather than hand-maintained —
that is an implementation choice, not a decision. Co-location now has runtime evidence on
both hosts, but promoting that decision needs all seven ATS-018 checks and a PRD revision,
so it stays Proposed.

**The OpenAI marketplace contract is now evidence-backed.** M1.1 invented
`policy.install` and `authentication: "none"`; a real host rejected them. Both were
removed in M1.3 with no compatibility alias, and the corrected catalog
(`installation: AVAILABLE`, `authentication: ON_INSTALL`, `category: Productivity`) was
revalidated on the host. Local schemas remain *local compatibility schemas*, not official
vendor schemas — and host acceptance of an unknown field never makes that field valid.

**Both OpenAI local `source` shapes are officially supported.** A local marketplace entry
may use the object `{"source": "local", "path": "./plugins/agent-harness"}` **or** a plain
string path `"./plugins/agent-harness"`. The generator emits the object form by choice,
not by requirement; a plain string is not a defect. The local schema accepts both — where
it is deliberately narrower than a vendor contract, it says so in a `$comment`.

**Required plugin identifiers are kebab-case; `category` is not.** Marketplace and plugin
`name` fields are documented kebab-case identifiers on both hosts. `category`,
`displayName`, descriptions and owner names are free-form labels. M1.3 removed the
identifier patterns in error; M1.3.1 restored them.

**M2's Skill set is complete.** All seven are implemented and validated. What remains
before a release is host verification, not Skills — see the exit criteria above. A shipped `SKILL.md` is host-discoverable whatever
its body says, so an empty placeholder would be a product surface with nothing behind
it.

---

---

## 한국어 안내

### 이게 뭔가요

**agent-harness는 모델도 런타임도 제공하지 않습니다. 절차를 제공합니다.**

Claude Code와 OpenAI Codex 양쪽에서 **같은 작업 절차**를 쓰게 해 주는 얇은 계층입니다.
일을 역할로 나누고, 호스트가 이미 가진 subagent로 위임하고, plan/evidence/result를
저장소 안 파일로 남기고, 검증 게이트가 통과하기 전에는 완료를 선언하지 않습니다.

구체적으로 **7개의 Skill**이 하나의 흐름을 이룹니다.

| Skill | 하는 일 | 권한 |
| :--- | :--- | :--- |
| `init-project` | 저장소에 `.agent-harness/` 구조를 만들고 지침 파일과 연결 | 승인 후 파일 생성 |
| `plan-work` | 목표를 작업으로 분해 — 완료 조건·의존성·수용 기준·검증 계획 | **읽기 전용** |
| `orchestrate` | 준비된 plan을 의존성 순서대로 수행, 독립 작업은 위임 | 계획된 경로만 수정 |
| `verify-work` | `config.yaml`에 **설정된** 검증 게이트만 실행하고 근거 수집 | 설정된 명령만 실행 |
| `doctor` | agent-harness 자체(설치·설정·상태)를 진단 | **읽기 전용** |
| `refine-harness` | run 근거에서 재사용 가능한 개선안을 뽑아 proposal 1개 작성 | proposal만 생성 |
| `apply-refinement` | 승인된 proposal을 적용 → 검증 → 되돌리기 정보 기록 | 승인 후 적용 |

**`doctor`와 `verify-work`를 헷갈리기 쉽습니다.** "내 테스트 통과해?"는 `verify-work`,
"이거 왜 아예 안 돌지?"는 `doctor`입니다. 전자는 프로젝트 코드를, 후자는 harness 자체를
봅니다.

### 설치

#### Claude Code — 검증된 방법

세션 범위 로딩입니다. **설치 기록을 남기지 않으므로 되돌릴 것도 없습니다.**
M1.4A에서 Claude Code 2.1.195로 실제 확인했습니다.

```bash
claude --plugin-dir /path/to/agent-harness/plugins/agent-harness
```

Skill이 보이는지 확인:

```bash
claude --plugin-dir ./plugins/agent-harness plugin details agent-harness@inline
```

`Skills (8)`, `Agents (6)`이 나오면 정상입니다 — fixture 1개 + production Skill 7개,
그리고 M3에서 추가된 role subagent 6개입니다. Agents가 6보다 작으면 role 정의가
로드되지 않은 것이고, 모델 호출 없이 확인되는 유일한 점검입니다.

#### marketplace 설치 — 아직 검증 안 됨

`.claude-plugin/marketplace.json`과 `.agents/plugins/marketplace.json`이 생성되어 있고
`claude plugin validate --strict`를 통과하지만, **실제 설치는 해 본 적이 없습니다.**
Codex CLI의 marketplace 등록만 격리 환경에서 확인했습니다. 자세한 절차는
[`docs/install-claude-code.md`](docs/install-claude-code.md)를 보세요 — M3에서 작성됐고,
어떤 단계가 실제로 실행됐고 어떤 단계가 문서상 근거뿐인지 맨 위 표에 구분해뒀습니다.
[`docs/install-codex.md`](docs/install-codex.md)도 M4에서 작성됐고, 같은 방식으로
실행된 단계와 문서상 근거뿐인 단계를 구분해뒀습니다 — Codex 쪽은 Skill 탐색 자체가
아직 미실행(E6)이라 구분해야 할 게 더 많습니다.

**marketplace 등록은 플러그인 설치가 아닙니다.** 등록은 "이런 플러그인이 있다"를
호스트에 알리는 것이고, 설치·활성화는 별개 단계입니다.

### 프로젝트 세팅

플러그인을 로드한 뒤 **대상 저장소에서** 진행합니다.

**1단계 — 진단 (선택)**

`doctor`를 호출하면 초기화 전 상태를 보여 줍니다. `.agent-harness/`가 없으므로
`fail` + "`init-project`를 실행하세요"가 나오는 게 정상입니다.

**2단계 — 초기화**

`init-project`를 명시적으로 호출합니다. 두 단계로 동작합니다.

- **Phase A**: 만들 파일을 전부 먼저 보여 주고 **아무것도 쓰지 않습니다**
- **Phase B**: 그 제안에 대한 승인을 받은 뒤에만 생성

생성되는 것:

```
.agent-harness/
  config.yaml              프로젝트 설정, 검증 게이트
  memory/facts.md          재사용 가능한 프로젝트 사실
  memory/decisions.md      결정과 근거
  memory/patterns.md       재사용 가능한 절차
  runs/                    실행 기록 (기본 로컬 전용)
  proposals/               개선 제안 (로컬 전용)
  .gitignore               runs/, proposals/ 등 4줄
```

`CLAUDE.md` 또는 `AGENTS.md`에는 `<!-- BEGIN agent-harness -->` … `<!-- END agent-harness -->`
마커 블록만 추가되고, **블록 바깥은 절대 건드리지 않습니다.**

**3단계 — 검증 게이트 설정**

`init-project`가 프로젝트를 보고 후보 명령을 **제안**하지만 **활성화하지는 않습니다.**
직접 `config.yaml`에 적어야 실행 대상이 됩니다.

```yaml
verification:
  gates:
    - id: py-test
      kind: test
      command: ["python", "-m", "pytest", "-q"]   # 배열입니다. 셸 문자열 금지
      required: true
      timeout_seconds: 600
```

`command`는 **반드시 배열**입니다. 셸 문자열은 스키마가 거부합니다 — `&&`나 `|` 같은
연산자가 끼어들 여지를 없애기 위해서입니다.

### 사용 흐름

```
init-project  →  plan-work  →  orchestrate  →  verify-work
                                  ↑                  │
                                  └──────────────────┘
                     refine-harness  →  apply-refinement
                          (doctor는 언제든)
```

1. **`plan-work`** — "이 기능 계획 세워줘". 작업 분해·완료 조건·의존성·수용 기준·검증
   계획을 돌려줍니다. 기본은 응답만, 저장은 명시적으로 요청할 때만.
2. **`orchestrate`** — 준비된 plan을 수행합니다. **이 마일스톤에서는 명령을 실행하지
   않습니다** (구조화된 command 표현이 아직 없어서). 명령이 필요한 작업은 `blocked`로
   보고합니다.
3. **`verify-work`** — 설정된 게이트만 실행합니다. 게이트가 없으면 추측하지 않고
   `Blocked`. 실행 전 게이트 목록을 보여 주고 **승인을 받습니다.**
4. **`refine-harness`** — 끝난 run의 근거에서 재사용할 만한 것을 뽑아 proposal 1개를
   씁니다. **적용하지 않습니다.**
5. **`apply-refinement`** — 승인된 proposal을 적용하고, 검증하고, 되돌리는 법을
   기록합니다. 검증에 실패하면 **전부 되돌립니다.**

### 안전 설계 — 알아두면 좋은 것

- **승인은 단계마다 다릅니다.** Skill을 호출한 것과 변경을 승인한 것은 별개입니다.
  `apply-refinement`는 파일 목록과 diff를 보여 준 뒤 그 proposal에 묶인 승인을 요구하고,
  쓰기 직전에 한 번 더 확인합니다.
- **명령은 설정된 것만.** `package.json`이나 Makefile을 읽고 추측해서 실행하는 일은
  없습니다.
- **플러그인은 자기 자신을 수정하지 않습니다.** `skill` 변경 제안은 사람이 PR로만
  적용합니다.
- **되돌릴 수 없는 변경은 만들지 않습니다.** rollback 정보 없이는 적용하지 않고,
  git 명령은 제시만 하고 직접 실행하지 않습니다.

### 지금 상태 — 솔직하게

**이건 아직 정식 릴리스가 아닙니다.**

- 7개 Skill은 **구조적으로만 검증**되었습니다. 624개 테스트와 12개 validator가 계약·쓰기
  범위·스키마를 고정하지만, **모델이 실제로 그 지시를 따르는지는 아직 확인되지
  않았습니다.** 첫 실전 검증 계획은 [`docs/m2-pilot-plan.md`](docs/m2-pilot-plan.md)에
  있습니다.
- M1 호스트 검증 3건이 릴리스 블로커로 남아 있습니다 — Codex Skill 발견(E6),
  ChatGPT Desktop marketplace(E12), hook·helper 런타임(E13). 17개 중 14개 통과입니다.
- `orchestrate`의 명령 실행과 run 상태 영속화(`evidence.md`/`result.md`)는 다음
  마일스톤으로 **의도적으로 유예**했습니다.

실험적으로 쓰기에는 충분하지만, 중요한 저장소에 적용하기 전에는 **일회용 사본에서 먼저
돌려 보시길** 권합니다.

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

Apache-2.0. See [`LICENSE`](LICENSE).
