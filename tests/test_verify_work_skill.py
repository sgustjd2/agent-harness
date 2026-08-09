"""Contract tests for the verify-work Skill (M2 slice 3).

verify-work is the first production Skill that intentionally runs subprocesses, so these
concentrate on the limits around that power: configured gates only, approval before
execution, argv arrays, and status arithmetic that cannot round a non-pass up to Passed.

Generic Skill hygiene (frontmatter shape, references containment, no bundled scripts) is
already covered by the shared validator and the two earlier slices; it is not repeated
here beyond one end-to-end validation.
"""

from __future__ import annotations

import json

import jsonschema
import pytest
import yaml

from conftest import REPO_ROOT
from _common import FORBIDDEN_PRODUCTION_SKILLS
from test_plan_work_skill import _frontmatter, _run

pytestmark = pytest.mark.deterministic

SKILLS = REPO_ROOT / "plugins" / "agent-harness" / "skills"
VERIFY = SKILLS / "verify-work"
SKILL_MD = VERIFY / "SKILL.md"
CONFIG_SCHEMA = json.loads(
    (REPO_ROOT / "plugins/agent-harness/core/schemas/state/config.schema.json")
    .read_text(encoding="utf-8"))


def _declared() -> dict:
    from _common import extract_policy_marker

    return yaml.safe_load(extract_policy_marker(SKILL_MD.read_text(encoding="utf-8")))


def _body() -> str:
    return " ".join(SKILL_MD.read_text(encoding="utf-8").lower().split())


def _validate_config(config: dict) -> None:
    jsonschema.validators.validator_for(CONFIG_SCHEMA)(CONFIG_SCHEMA).validate(config)


def _config_with(gate: dict) -> dict:
    return {
        "schema_version": 1,
        "project": {"name": "x", "type": ["generic"]},
        "orchestration": {"max_parallel_agents": 1, "max_delegation_depth": 1},
        "verification": {"gates": [gate]},
    }


GOOD_GATE = {"id": "py-test", "kind": "test", "command": ["python", "-m", "pytest", "-q"],
             "required": True, "timeout_seconds": 600}


# ---------------------------------------------------------------- 1-3. structure

def test_verify_work_validates_as_shipped():
    """1. The whole plugin, including verify-work, passes the real validator."""
    import validate_skills

    status, codes = _run(validate_skills.check, REPO_ROOT / "plugins" / "agent-harness")
    assert status == 0, f"validate_skills failed with {codes}"
    assert codes == [], codes


def test_frontmatter_is_exactly_name_and_description():
    """2."""
    front = _frontmatter(SKILL_MD)
    assert set(front) == {"name", "description"}, sorted(front)
    assert front["name"] == VERIFY.name == "verify-work"


def test_implicit_invocation_is_disabled():
    """3. A Skill that runs commands must not be selected implicitly."""
    policy = yaml.safe_load((VERIFY / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert set(policy) == {"policy"}
    assert set(policy["policy"]) == {"allow_implicit_invocation"}
    assert policy["policy"]["allow_implicit_invocation"] is False


# ---------------------------------------------------------- 4-8, 20. the profile

def test_bounded_verification_profile_is_selected():
    """4."""
    from _common import SKILL_PROFILE

    assert SKILL_PROFILE["verify-work"] == "bounded-verification"


@pytest.mark.parametrize("key,expected", [
    ("executes_commands", True),                 # 5
    ("executes_configured_gates_only", True),    # 6
    ("requires_execution_approval", True),       # 7
    ("requires_explicit_invocation", True),
    ("command_definition", "argv-array"),        # 8
    ("verification_default", "Not Run"),         # 12
    ("network_access", False),                   # 20
    ("installs_packages", False),                # 20
    ("modifies_source", False),
    ("modifies_config", False),
    ("modifies_user_settings", False),
    ("spawns_agents", False),
    ("evidence_persistence", "run-artifacts"),
    ("writes_run_artifacts", True),
])
def test_declared_contract(key, expected):
    assert _declared()[key] == expected


@pytest.mark.parametrize("key,bad", [
    ("executes_configured_gates_only", False),
    ("requires_execution_approval", False),
    ("modifies_source", True),
    ("network_access", True),
    ("installs_packages", True),
])
def test_flipping_a_bounded_promise_fails_validation(plugin_tree, key, bad):
    """Each limit on execution is enforced, not merely written down."""
    import validate_skills

    md = plugin_tree / "skills" / "verify-work" / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    start = text.index(f"{key}: ")
    end = text.index("\n", start)
    md.write_text(text[:start] + f"{key}: {str(bad).lower()}" + text[end:], encoding="utf-8")

    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_MUTATION_NOT_PERMITTED" in codes, codes


def test_verify_works_write_surface_is_one_run_directory():
    """M5 gave it a write surface. It is exactly one directory and no more.

    Before M5 this asserted there was none at all. The narrower claim that replaced it is
    the one that matters: a verifier has no business touching config or memory, so this
    root is deliberately narrower than init-project's `.agent-harness/`.
    """
    from _common import (ALLOWED_WRITE_PATH_ROOTS, PROFILES_REQUIRING_PATH_ROOTS,
                         RUN_ARTIFACT_ROOT)

    assert "bounded-verification" in PROFILES_REQUIRING_PATH_ROOTS
    assert ALLOWED_WRITE_PATH_ROOTS["verify-work"] == [RUN_ARTIFACT_ROOT]
    assert _declared()["allowed_path_roots"] == [RUN_ARTIFACT_ROOT]
    assert _declared()["modifies_source"] is False
    assert _declared()["modifies_config"] is False


def test_the_evidence_write_needs_no_separate_approval():
    """Execution approval covers the record the execution produces.

    A verifier that ran the gates but could not write down what happened would be asking
    the user to take its word for it -- which is what evidence exists to prevent.
    """
    body = _body()
    assert "needs no separate approval, and grants nothing further" in body
    assert "does not extend one path beyond" in body


def test_an_uninitialized_project_still_gets_its_results():
    """Verification you can read beats verification that refused over paperwork."""
    body = _body()
    assert "do not create `.agent-harness/` to hold the file" in body
    assert "could not be persisted" in body


# ------------------------------------------------- 9-11. gate config contract

def test_shell_string_command_is_rejected_by_the_state_schema():
    """9. A gate whose command is a shell string must not validate."""
    bad = dict(GOOD_GATE, command="python -m pytest -q && ruff check .")
    with pytest.raises(jsonschema.ValidationError):
        _validate_config(_config_with(bad))


@pytest.mark.parametrize("gate,reason", [
    (dict(GOOD_GATE, command=[]), "empty argv"),
    ({k: v for k, v in GOOD_GATE.items() if k != "timeout_seconds"}, "missing timeout"),
    (dict(GOOD_GATE, timeout_seconds=0), "non-positive timeout"),
    ({k: v for k, v in GOOD_GATE.items() if k != "id"}, "missing id"),
    (dict(GOOD_GATE, kind="deploy"), "unsupported kind"),
    (dict(GOOD_GATE, required="yes"), "non-boolean required"),
])
def test_malformed_gates_are_rejected(gate, reason):
    """10. Preflight requirements the schema already enforces."""
    with pytest.raises(jsonschema.ValidationError):
        _validate_config(_config_with(gate))


def test_a_well_formed_gate_validates():
    _validate_config(_config_with(GOOD_GATE))


@pytest.mark.parametrize("phrase", [
    "working_dir` contained in the repository",   # 11
    "no traversal",
])
def test_working_directory_must_be_repository_contained(phrase):
    """11. Stated in the Skill; the runtime check belongs to the host call."""
    assert phrase.lower() in _body(), f"SKILL.md omits {phrase!r}"


# ------------------------- classification model (PRD §15.4) and verification_status

CLASSIFICATIONS = ["pass", "fail", "error", "timeout", "skipped", "flaky"]


@pytest.mark.parametrize("classification,definition", [
    # 1 exit 0 => pass
    ("pass", "| `pass` | process started, exit code 0 |"),
    # 2 non-zero => fail
    ("fail", "| `fail` | process started normally, exit code non-zero |"),
    # 3/4 missing executable or permission denial => error, NOT Blocked
    ("error", "| `error` | executable not found, permission denied, or the process "
              "could not execute for another environment or runtime reason |"),
    # 5 timeout => timeout, not generic Failed
    ("timeout", "| `timeout` | process started, exceeded its timeout, and was "
                "terminated because of it |"),
    # 6 budget exhaustion => skipped
    ("skipped", "| `skipped` | the gate was selected but deliberately not run by "
                "execution control flow — budget exhaustion, or a prd-defined skip "
                "condition |"),
    # 8 disagreeing rerun => flaky
    ("flaky", "| `flaky` | `flaky_policy: rerun-once`, the first classification was "
              "`fail`, and the rerun disagreed |"),
])
def test_each_prd_classification_is_defined(classification, definition):
    """The six PRD classifications, each with the condition that produces it."""
    assert definition in _body(), f"SKILL.md does not define {classification!r} correctly"


@pytest.mark.parametrize("distinction", [
    # 3/4 error must not collapse into the pre-execution category
    "**`error` is not `blocked`.**",
    # 5 timeout must not collapse into fail
    "**`timeout` is not `fail`.**",
    # 6 skipped must not collapse into never-run
    '**`skipped` is not "never run".**',
])
def test_classifications_are_not_collapsed(distinction):
    """The three collisions the earlier four-status model caused, stated explicitly."""
    assert distinction in _body(), f"SKILL.md omits the distinction: {distinction!r}"


def test_blocked_stays_a_pre_execution_concept():
    """`Blocked` describes never reaching a launch; it is not a process outcome."""
    body = _body()
    assert "a `blocked` gate never reaches a process launch, so it has no process " \
           "outcome to classify" in body
    for pre_exec in ["no configured gates at all", "stale execution approval",
                     "an unsafe repository path"]:
        assert pre_exec in body, f"SKILL.md omits the pre-execution case {pre_exec!r}"


@pytest.mark.parametrize("rule", [
    # 9 required fail/error/timeout => failed
    "| `failed` | any required gate is `fail`, `error`, or `timeout` |",
    # 10 required skipped/flaky/blocked/never-ran => unverified
    "| `unverified` | any required gate is `skipped` or `flaky`, was `blocked` before "
    "execution, or never ran |",
    "| `passed` | every required gate is classified `pass` |",
])
def test_verification_status_rules_are_stated(rule):
    """verification_status is computed from required gates only."""
    assert rule in _body(), f"SKILL.md omits the rule: {rule!r}"


def test_failed_and_unverified_are_distinguished():
    """Conflating them would report 'nothing was established' as 'something is wrong'."""
    body = _body()
    assert "`failed` means the checks ran and something is wrong with the work; " \
           "`unverified` means the checks did not establish anything" in body


@pytest.mark.parametrize("rule", [
    # 7 rerun applies only to fail
    "only `flaky_policy: rerun-once` produces a retry, and only for classification "
    "**`fail`**",
    "**never rerun `error`.**",
    "**never rerun `timeout`.**",
    "rerun **exactly once** — never a loop",
    # flaky never becomes pass
    "**`flaky` is never promoted to `pass`**",
    "record **both attempts** separately",
])
def test_flaky_rules_are_stated(rule):
    """7/8. rerun-once is narrow, and its result is never rounded up."""
    assert rule in _body(), f"SKILL.md omits the flaky rule: {rule!r}"


def test_budget_exhaustion_is_skipped_not_not_run():
    """6. Gates the run reached and passed over are `skipped`, not 'never started'."""
    body = _body()
    assert "every remaining gate is classified **`skipped`**" in body
    assert "`verification_status` becomes `unverified`" in body


@pytest.mark.parametrize("rule", [
    "optional failures present",                                # optional stay visible
    "if no gate is configured, stop and report `blocked`",      # nothing configured
    "a command that exists is not a command that passed",       # no false success
])
def test_reporting_rules_are_stated(rule):
    assert rule in _body(), f"SKILL.md omits the rule: {rule!r}"


@pytest.mark.parametrize("field", [
    "gate id", "kind", "required", "command[]",
    "repository-relative working directory", "started or not started",
    "exit code when available", "duration when available", "classification",
    "timeout information", "bounded output excerpt",
])
def test_evidence_fields_are_required(field):
    """Every field the evidence contract owes per gate."""
    assert field in _body(), f"SKILL.md omits the evidence field {field!r}"


def test_evidence_template_uses_the_classification_vocabulary():
    """The template must carry both layers, and no fabricated success."""
    text = (VERIFY / "references" / "evidence-template.md").read_text(encoding="utf-8")
    assert "Classification: <pass|fail|error|timeout|skipped|flaky>" in text
    assert "Verification status: <passed|failed|unverified>" in text
    # Illustrative example must never show a run that succeeded.
    assert "Verification status: unverified" in text
    assert "Classification: pass" not in text
    assert "illustrative" in text.lower()


def test_execution_contract_reference_agrees_with_the_skill():
    """The reference must not drift into the withdrawn four-status vocabulary."""
    contract = " ".join((VERIFY / "references" / "execution-contract.md")
                        .read_text(encoding="utf-8").lower().split())
    for value in CLASSIFICATIONS:
        assert f"`{value}`" in contract, f"execution contract omits {value!r}"
    assert "any required gate is `fail`, `error`, or `timeout`" in contract
    assert "`error` is **not** `blocked`" in contract


# ------------------------------------------------- 18-19. references and hygiene

@pytest.mark.parametrize("rel", [
    "references/execution-contract.md",
    "references/evidence-template.md",
    "agents/openai.yaml",
])
def test_required_files_exist_inside_the_skill(rel):
    """18."""
    target = VERIFY / rel
    assert target.is_file(), f"{rel} is missing"
    assert str(target.resolve()).startswith(str(VERIFY.resolve()))


def test_no_bundled_helper_of_any_kind():
    """19. Q-IMPL-003 is unresolved, so this slice ships nothing executable."""
    import validate_skills

    for sub in ("scripts", "assets", "bin"):
        assert not (VERIFY / sub).exists(), f"{sub}/ must not exist inside verify-work"
    for manifest in validate_skills.DEPENDENCY_MANIFESTS:
        assert not (VERIFY / manifest).exists()
    for fence in validate_skills.SHELL_FENCES:
        assert fence not in SKILL_MD.read_text(encoding="utf-8")


@pytest.mark.parametrize("forbidden", [
    "package install", "plugin install", "marketplace registration", "git mutation",
])
def test_forbidden_command_classes_are_named(forbidden):
    contract = " ".join((VERIFY / "references" / "execution-contract.md")
                        .read_text(encoding="utf-8").lower().split())
    assert forbidden in contract, f"execution contract omits {forbidden!r}"


# ------------------------------------------- 21-24. allowlist and no regression

def test_milestone_allowlist_includes_verify_work():
    """21. Derived from the constant; exact membership lives in the newest slice's file."""
    from _common import ALLOWED_SKILLS, IMPLEMENTED_PRODUCTION_SKILLS

    assert "verify-work" in IMPLEMENTED_PRODUCTION_SKILLS
    assert {d.name for d in SKILLS.iterdir() if d.is_dir()} == set(ALLOWED_SKILLS)


# FORBIDDEN_PRODUCTION_SKILLS is empty now that all seven are implemented. An
# empty parametrize SKIPS silently, so the guard would stop running without
# anyone noticing -- fall back to a name that is not on the allowlist.
@pytest.mark.parametrize(
    "name", FORBIDDEN_PRODUCTION_SKILLS or ["not-a-planned-skill"])
def test_remaining_production_skills_are_still_rejected(plugin_tree, name):
    """22. Every not-yet-implemented name, derived from the constant."""
    import validate_skills

    assert not (SKILLS / name).exists()

    bad = plugin_tree / "skills" / name
    bad.mkdir(parents=True)
    (bad / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: placeholder\n---\n\nplaceholder\n",
        encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert {"PRODUCTION_SKILL_IN_ROOT", "FORBIDDEN_COMPONENT_IN_ROOT"} & set(codes), \
        codes


@pytest.mark.parametrize("skill,profile", [
    ("plan-work", "read-only"),            # 23
    ("init-project", "approval-gated-mutation"),   # 24
])
def test_earlier_skills_still_forbid_execution_after_the_refactor(skill, profile):
    """23/24. Moving `executes_commands` out of the universal set changed nothing here.

    This is the regression the refactor could plausibly have caused: a field that used to
    be inherited now has to be restated per profile, and a profile that forgot to
    restate it would silently gain the right to run commands.
    """
    from _common import SKILL_PROFILE, SKILL_SAFETY_PROFILES, extract_policy_marker

    assert SKILL_PROFILE[skill] == profile
    assert SKILL_SAFETY_PROFILES[profile]["executes_commands"] is False
    declared = yaml.safe_load(
        extract_policy_marker((SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")))
    assert declared["executes_commands"] is False


def test_execution_is_an_explicit_grant_never_inherited():
    """Execution is granted deliberately, never acquired by inheritance.

    The assertion is against the explicit grant list rather than a count: a second
    executing profile (plan-bounded-orchestration) is legitimate, a profile that executes
    WITHOUT appearing on the list is not.
    """
    from _common import (PROFILES_PERMITTING_EXECUTION, SKILL_SAFETY_PROFILES,
                         UNIVERSAL_SKILL_POLICY)

    assert "executes_commands" not in UNIVERSAL_SKILL_POLICY, (
        "executes_commands stopped being universal when verify-work existed")
    assert UNIVERSAL_SKILL_POLICY["network_access"] is False
    assert "bounded-verification" in PROFILES_PERMITTING_EXECUTION
    executing = [n for n, p in SKILL_SAFETY_PROFILES.items() if p["executes_commands"]]
    assert sorted(executing) == sorted(PROFILES_PERMITTING_EXECUTION), (
        f"a profile executes without being granted execution: {executing}")
