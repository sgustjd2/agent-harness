# M1 traceability

Maps each M1 exit criterion to its evidence, and each required negative scenario to the
validator that enforces it. Counts are produced by `scripts/m1_status.py`, not written
by hand -- the previous report's "12 of 17" against an 11-item list is exactly the
failure mode that guards against.

Regenerate with:

```bash
python scripts/m1_status.py --markdown
```

---

## Exit criteria

_Regenerated M1.4A, 2026-08-08 -- counts and evidence come from `scripts/m1_status.py`, never hand-written._

| ID | Criterion | Status | Evidence |
| :--- | :--- | :--- | :--- |
| E1 | Valid Claude plugin fixture passes `claude plugin validate` | **Passed** | `claude plugin validate ./plugins/agent-harness --strict` -> exit 0, 'Validation passed'. Claude Code 2.1.195. |
| E2 | Valid Claude marketplace fixture passes Claude validation | **Passed** | `claude plugin validate . --strict` -> exit 0, 'Validation passed'. Claude Code 2.1.195. |
| E3 | Codex plugin manifest validated by official mechanism, else a documented local schema | **Passed** | M1.2 correction: Codex CLI IS available (codex-cli 0.146.0-alpha.9.2, bundled with ChatGPT Desktop). Its help exposes no `validate` subcommand, so no official manifest validator exists. `.codex-plugin/plugin.json` validated by `codex-plugin.schema.json` via jsonschema Draft 2020-12. INDIRECT HOST EVIDENCE: `codex plugin add` accepted and installed the plugin from this manifest, so the real host parsed it successfully. |
| E4 | Codex marketplace validated by official mechanism, else a documented local schema | **Passed** | M1.3: DEF-001 remediated and REVALIDATED ON THE REAL HOST. The corrected catalog (policy.installation=AVAILABLE, policy.authentication=ON_INSTALL, category=Productivity, object source) was accepted by `codex plugin marketplace add` on codex-cli 0.146.0-alpha.9.2, in an isolated CODEX_HOME, registration only -- no plugin installed. Also validated by openai-marketplace.schema.json via jsonschema, whose enums now trace to the contract evidence table. 16 regression scenarios (NS-29..NS-45, less the withdrawn NS-42) lock the fix. M1.3.1: evidence classification corrected -- the schema now accepts BOTH documented local source forms (the object form is a local generation choice, not a vendor requirement) and the officially documented kebab-case identifier patterns were restored after an incorrect M1.3 removal. Deterministic revalidation only; the M1.3 host evidence above is retained and was NOT re-run. |
| E5 | The same plugin root works in both hosts, or the generated-distribution fallback decision is triggered | **Passed** | M1.4A: BOTH HOSTS NOW LOAD THE SAME CO-LOCATED ROOT. Claude half RESOLVED -- `claude --plugin-dir ./plugins/agent-harness plugin list --json` returned agent-harness@inline, scope=session, enabled=true, version 0.0.1, loaded from the root containing .codex-plugin/. This is RUNTIME LOADING, not validator tolerance. No installed record was created: a bare `claude plugin list` omits it and the plugin cache digest was byte-identical before and after. Codex half (M1.2): installed from a root containing .claude-plugin/, both manifests and skills/ preserved in the isolated cache -- version-scoped and PROC-001 protocol-deviating, retained but not re-run. VERSION-SCOPED: Claude Code 2.1.195 and codex-cli 0.146.0-alpha.9.2 only; future versions remain subject to regression testing. ATS-018-1/2/3 pass; 018-4/5/6/7 are not yet all recorded, so DEC-P13 is NOT promoted -- the PRD conditions promotion on all seven checks AND a PRD revision. |
| E6 | Both hosts discover the same minimal canonical Skill | Manual Required | CLAUDE HALF PASSED (M1.4A, ATS-018-3): `claude --plugin-dir <root> plugin details agent-harness@inline` returned a component inventory listing Skills (1) m1-discovery-fixture, with Agents/Hooks/MCP/LSP all 0 and no production Skill name present. Non-interactive, no model invoked. This is DISCOVERY, not invocation -- the fixture was never run and the marker was neither expected nor claimed. CODEX HALF NOT RUN (ATS-018-4): no `skill` subcommand exists and `codex exec` would invoke a paid model. Cache-file presence is explicitly NOT accepted as discovery evidence. E6 requires BOTH halves, so it stays non-Passed. |
| E7 | Codex manifest `skills` format is no longer an unknown | **Passed** | Documented format `"skills": "./skills/"` encoded in codex-plugin.schema.json as a string with a path-shape pattern; an array is rejected (NS-06). |
| E8 | All valid fixtures pass | **Passed** | 12/12 deterministic validators pass; pytest 103 passed, 1 skipped (M1.3.1). All five baseline documents validate cleanly (test_baselines_are_valid), and both documented OpenAI local source forms validate. |
| E9 | Each invalid fixture fails for its intended reason | **Passed** | 52 schema-mutation scenarios plus filesystem/boundary scenarios, each asserting one stable diagnostic code rather than prose. M1.3.1 withdrew NS-42 (it asserted an evidence-incorrect contract) and added NS-46..NS-64 covering source shapes and restored kebab-case identifiers. See the coverage table in docs/m1-remediation.md. |
| E10 | Validation runs without network access where possible | **Passed** | Offline CI job blocks sockets and runs validate_all.py. Dependency installation is a separate, prior step and is not a validator network dependency. |
| E11 | No paid model invocation is required in normal CI | **Passed** | Neither workflow configures a model API key or invokes a model. Model-requiring tests are marked `manual` and excluded by marker. |
| E12 | Marketplace Candidates A, B and C each recorded, selection evidence-backed | Blocked | M1.3: Candidate C now PASSES Codex marketplace registration after the DEF-001 fix, and passes Claude strict validation. Still missing: ChatGPT Desktop surface for all three candidates, and Codex/desktop evidence for A and B. Candidate B cannot be selected without positive evidence on every mandatory surface. DEC-P14 stays Proposed. |
| E13 | Hook-root behaviour tested separately from Skill-script behaviour | Manual Required | Separation IMPLEMENTED and still enforced. M1.2: Codex CLI IS available, but firing a hook or executing a Skill both require a session that invokes a paid model, which M1.2 forbids automatically. Neither experiment EXECUTED. Static fixture validation remains Passed; runtime remains Manual Required. |
| E14 | Manual host tests are clearly separated from deterministic CI tests | **Passed** | pytest markers deterministic / host_cli / manual with --strict-markers; CI runs `-m 'not manual and not host_cli'`; validate_all.py states it excludes manual tests; docs/m1-experiments.md records them as pending. |
| E15 | No production implementation of the seven planned Skills exists | **Passed** | All seven placeholder directories removed from the installable root. validate_skills fails on any of the seven names (NS-20). Zero .py files under the plugin root. |
| E16 | No user-level configuration was changed | **Passed** | No CONFIGURATION changed: real ~/.codex/config.toml contains only pre-existing openai-bundled/openai-primary-runtime marketplaces -- no agent-harness entry. No plugin installed to the real cache. All M1.2 marketplace/plugin state landed in an isolated CODEX_HOME. DISCLOSED: every codex invocation incidentally writes ~/.codex/logs_2.sqlite-wal, models_cache.json and 3 ~/.codex/tmp helper files; CODEX_HOME does not redirect those. Logs/cache/temp are not configuration. |
| E17 | No secret or complete environment dump is stored in artifacts | **Passed** | Hook probe reports booleans only, by construction. redact() strips home paths and credential shapes from every captured output before recording. |

**Total criteria: 17**

| Status | Count |
| :--- | ---: |
| Passed | 14 |
| Failed | 0 |
| Blocked | 1 |
| Not Available | 0 |
| Manual Required | 2 |
| **Sum** | **17** |

**Met (Passed only): 14 of 17**

**Phase: M1 scaffold complete, host verification pending**

---

## Status meanings

| Status | Meaning |
| :--- | :--- |
| **Passed** | Fully satisfied, with evidence. The only status that counts as met |
| Failed | Attempted and did not succeed |
| Blocked | Cannot proceed -- a prerequisite is unavailable |
| Not Available | The mechanism does not exist on this machine or in the documentation |
| Manual Required | Needs a human, a live host session, or a model invocation |

Partially implemented is not Passed. Where a criterion has both a static and a
host-runtime part, the evidence is split but the overall status stays non-Passed until
every mandatory part is satisfied -- E5 and E13 are both in that position.

---

## Negative scenario to validator map

| Scenario | Validator | Stable code |
| :--- | :--- | :--- |
| NS-01, NS-02, NS-03 | `validate_manifests` (claude-plugin schema) | `PLUGIN_NAME_MISSING`, `PLUGIN_NAME_NOT_KEBAB`, `VERSION_NOT_SEMVER` |
| NS-04 | `validate_manifests` (cross-file) | `VERSION_MISMATCH` |
| NS-05 ... NS-08, NS-23 ... NS-26 | `validate_manifests` (codex-plugin schema) | `CODEX_SKILLS_*`, `PATH_*` |
| NS-09, NS-10 | `validate_marketplaces` (claude-marketplace schema) | `MARKETPLACE_EMPTY`, `CLAUDE_SOURCE_INVALID` |
| NS-11 ... NS-13 | `validate_marketplaces` (openai-marketplace schema) | `OPENAI_SOURCE_INVALID`, `OPENAI_POLICY_*` |
| NS-14 | `generate_marketplaces --check` | `CATALOG_DRIFT` |
| NS-15 | `validate_marketplaces` (canonical schema) | `CANONICAL_FIELD_MISSING` |
| NS-16 ... NS-18, NS-20, NS-21 | `validate_skills` | `SKILL_*`, `POLICY_*`, `PRODUCTION_*` |
| NS-19 | `check_path_containment` | `SYMLINK_ESCAPE` |
| NS-22, NS-22b | `check_no_install_command` | `UNDOCUMENTED_INSTALL_COMMAND` |
| NS-28 (M1.3) | `validate_marketplaces` | `OPENAI_POLICY_AUTH_INVALID` — must reject `"none"`, see DEF-001 |
| NS-27 | `validate_manifests` under a spaced path | *(must pass)* |
| NS-29 ... NS-41, NS-43 ... NS-45 (M1.3) | `validate_marketplaces` | `OPENAI_POLICY_*`, `OPENAI_CATEGORY_MISSING`, `CANONICAL_FIELD_MISSING` — the DEF-001 regression set |
| ~~NS-42~~ | **withdrawn in M1.3.1** | asserted that a plain string `source` is invalid; the vendor documents that form, so the assertion was evidence-incorrect |
| NS-46 ... NS-54 (M1.3.1) | `validate_marketplaces` (openai-marketplace schema) | `OPENAI_SOURCE_TYPE_MISSING`, `OPENAI_SOURCE_PATH_MISSING`, `OPENAI_SOURCE_PATH_INVALID`, `OPENAI_SOURCE_UNKNOWN_FIELD`, `OPENAI_SOURCE_INVALID`, `PATH_*` — shapes matching **neither** documented local form |
| NS-55 ... NS-60 (M1.3.1) | `validate_marketplaces` (both marketplace schemas) | `PLUGIN_NAME_NOT_KEBAB` — the officially documented identifier rule, restored after an incorrect M1.3 removal |
| NS-61 ... NS-64 (M1.3.1) | `validate_manifests` | `PLUGIN_NAME_NOT_KEBAB` — leading/trailing/repeated hyphens are a Local-M1-Policy refinement |

Full coverage table with results: `docs/m1-remediation.md` section 8.

---

## PRD deliverable coverage

| PRD M1 deliverable | State |
| :--- | :--- |
| 1. repository scaffold | done |
| 2. marketplace catalogs | done -- generated from canonical source (Candidate C provisional) |
| 3. both plugin manifest placeholders | done, both validated |
| 4. five state schemas | done, relocated to `core/schemas/state/`, excluded from packaging evidence |
| 5. validation scripts | done, with renames recorded in `docs/m1-remediation.md` section 6 |
| 6. CI (`validate.yml`, `test.yml`) | done. `release.yml` removed as an M8 deliverable |
| 7. fixtures | done -- 52 schema-mutation scenarios plus filesystem/boundary scenarios |
| 8. minimal fixture Skill + hook fixture | done -- one discovery fixture in the installable root, experiment fixtures under `tests/fixtures/host-tests/` |
| 9. ATS-018 result | partial -- 3 of 7 checks recorded (see below) |
| 10. ATS-022 result | partial -- deterministic only |

---

## ATS-018 checks (co-location) — status after M1.4A

E5's promotion clause requires **all seven**. Three are recorded.

| Check | Status | Evidence |
| :--- | :--- | :--- |
| 018-1 Claude accepts a root containing `.codex-plugin/` | **Passed** | `claude plugin validate --strict` exit 0, **and** runtime load via `--plugin-dir` (M1.4A) |
| 018-2 Codex accepts a root containing `.claude-plugin/` | **Passed** | installed from the co-located root; version-scoped, **PROC-001** |
| 018-3 Claude discovers the shared `skills/` | **Passed (M1.4A)** | `plugin details` → `Skills (1) m1-discovery-fixture` |
| 018-4 Codex discovers the same `skills/` | **Not Run** | no `skill` subcommand; `codex exec` would invoke a paid model |
| 018-5 neither host parses the other's manifest | **Not Run** | needs a deliberately broken manifest fixture per host |
| 018-6 cache copy preserves both manifests | **Codex half only** | Claude half would require an installation, which is forbidden |
| 018-7 runtime paths stay inside the plugin root | **Static only** | `check_path_containment.py` passes; runtime confirmation Not Run |

This is why DEC-P13 stays Proposed even though E5 is Passed: E5 asks whether the root
*works* in both hosts, which it demonstrably does. ATS-018 asks a stricter question —
whether co-location is safe in every respect — and four of its checks have no evidence.
| 11. ATS-028 result | not run |
| 12. ATS-020 result | not run |
| 13. adapter records | done |
| 14. README, CONTRIBUTING, compatibility | done |
