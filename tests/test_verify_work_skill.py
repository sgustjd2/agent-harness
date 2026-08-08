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
    ("evidence_persistence", "response-only"),
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


def test_verify_work_has_no_write_surface():
    """`read_only: false` is about subprocesses, not about editing anything."""
    from _common import ALLOWED_WRITE_PATH_ROOTS, PROFILES_REQUIRING_PATH_ROOTS

    assert "bounded-verification" not in PROFILES_REQUIRING_PATH_ROOTS
    assert "verify-work" not in ALLOWED_WRITE_PATH_ROOTS
    assert "allowed_path_roots" not in _declared()


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


# ---------------------------------------------- 12-17. status and result rules

@pytest.mark.parametrize("rule", [
    # 13 required-gate Passed
    "`passed` | every required gate ran **and** every one `passed`",
    # 14 required-gate Failed
    "`failed` | at least one required gate `failed`",
    # 15 required-gate Blocked
    "`blocked` | no required gate `failed`, and at least one is `blocked`",
    "`not run` | no required gate started",
    # 16 optional failures stay visible
    "optional failures present",
    # 17 nothing configured
    "if no gate is configured, stop and report `blocked`",
    # no false success
    "a command that exists is not a command that passed",
])
def test_result_rules_are_stated(rule):
    assert rule in _body(), f"SKILL.md omits the rule: {rule!r}"


def test_timeout_counts_as_failed_not_blocked():
    """12. A gate that started and timed out ran; it did not fail to start."""
    body = _body()
    assert "started and exited non-zero, **or** started and timed out" in body
    assert "`blocked` | could not safely start" in body


def test_evidence_template_shows_no_passing_example():
    """A template with a worked `Passed` example is a sentence someone can copy."""
    text = (VERIFY / "references" / "evidence-template.md").read_text(encoding="utf-8")
    assert "Overall: Not Run" in text
    assert "Status: Passed" not in text
    assert "illustrative" in text.lower()


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
    """21."""
    from _common import ALLOWED_SKILLS, IMPLEMENTED_PRODUCTION_SKILLS

    assert IMPLEMENTED_PRODUCTION_SKILLS == ["plan-work", "init-project", "verify-work"]
    assert set(ALLOWED_SKILLS) == {"m1-discovery-fixture", "plan-work", "init-project",
                                   "verify-work"}
    assert {d.name for d in SKILLS.iterdir() if d.is_dir()} == set(ALLOWED_SKILLS)


@pytest.mark.parametrize("name", [
    "orchestrate", "refine-harness", "apply-refinement", "doctor",
])
def test_remaining_production_skills_are_still_rejected(plugin_tree, name):
    """22."""
    import validate_skills
    from _common import FORBIDDEN_PRODUCTION_SKILLS

    assert name in FORBIDDEN_PRODUCTION_SKILLS
    assert not (SKILLS / name).exists()

    bad = plugin_tree / "skills" / name
    bad.mkdir(parents=True)
    (bad / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: placeholder\n---\n\nplaceholder\n",
        encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "PRODUCTION_SKILL_IN_ROOT" in codes, codes


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


def test_only_one_profile_may_execute():
    """Execution is granted deliberately, never acquired by inheritance."""
    from _common import (PROFILES_PERMITTING_EXECUTION, SKILL_SAFETY_PROFILES,
                         UNIVERSAL_SKILL_POLICY)

    assert "executes_commands" not in UNIVERSAL_SKILL_POLICY, (
        "executes_commands stopped being universal when verify-work existed")
    assert UNIVERSAL_SKILL_POLICY["network_access"] is False
    executing = [n for n, p in SKILL_SAFETY_PROFILES.items() if p["executes_commands"]]
    assert executing == PROFILES_PERMITTING_EXECUTION == ["bounded-verification"]
