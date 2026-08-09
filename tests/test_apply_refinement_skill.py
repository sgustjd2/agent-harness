"""Contract tests for the apply-refinement Skill (M2 slice 7, final).

apply-refinement is the only Skill that changes memory or configuration, and the only one
that both writes and executes. These tests concentrate on the two independent gates, the
staleness check, the refusal to modify the plugin's own Skills, and the rollback ordering.

Nothing here applies a proposal, executes a gate, or runs a model.
"""

from __future__ import annotations

import json

import pytest
import yaml

from conftest import REPO_ROOT
from _common import FORBIDDEN_PRODUCTION_SKILLS
from test_plan_work_skill import _frontmatter, _run

pytestmark = pytest.mark.deterministic

SKILLS = REPO_ROOT / "plugins" / "agent-harness" / "skills"
APPLY = SKILLS / "apply-refinement"
SKILL_MD = APPLY / "SKILL.md"
GATES = APPLY / "references" / "approval-gates.md"
APPLICATION = APPLY / "references" / "application-contract.md"
ROLLBACK = APPLY / "references" / "rollback-contract.md"
PROPOSAL_SCHEMA = json.loads(
    (REPO_ROOT / "plugins/agent-harness/core/schemas/state/proposal.schema.json")
    .read_text(encoding="utf-8"))


def _declared() -> dict:
    from _common import extract_policy_marker

    return yaml.safe_load(extract_policy_marker(SKILL_MD.read_text(encoding="utf-8")))


def _flat(path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


# ---------------------------------------------------------------- structure

def test_apply_refinement_validates_as_shipped():
    import validate_skills

    status, codes = _run(validate_skills.check, REPO_ROOT / "plugins" / "agent-harness")
    assert status == 0, f"validate_skills failed with {codes}"
    assert codes == [], codes


def test_frontmatter_is_exactly_name_and_description():
    front = _frontmatter(SKILL_MD)
    assert set(front) == {"name", "description"}, sorted(front)
    assert front["name"] == APPLY.name == "apply-refinement"


# ---------------------------------------------------------------- Gate A

def test_gate_a_disables_implicit_invocation():
    """FR-025.1-A: a model must not select this Skill from a prompt."""
    from _common import IMPLICIT_INVOCATION_MUST_BE_OFF

    assert "apply-refinement" in IMPLICIT_INVOCATION_MUST_BE_OFF
    policy = yaml.safe_load((APPLY / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert set(policy) == {"policy"}
    assert set(policy["policy"]) == {"allow_implicit_invocation"}
    assert policy["policy"]["allow_implicit_invocation"] is False


# ---------------------------------------------------------------- Gate B

@pytest.mark.parametrize("clause", [
    "inspect the specific proposal",
    "present the exact target file list and the diff",
    "require confirmation bound to that proposal",
    "re-confirm immediately before writing",
    "refuse approval that is stale, missing, ambiguous, or mismatched",
    "never read an earlier, unrelated approval as permission",
    "if anything cannot be verified, stop with no changes",
    "never store approval as a replayable token",
])
def test_gate_b_has_all_eight_clauses(clause):
    """FR-025.1-B: all eight, in the body, not only in a reference."""
    assert clause in _flat(SKILL_MD), f"SKILL.md omits Gate B clause: {clause!r}"


def test_gates_are_independent():
    """Gate B must hold where Gate A is absent, ignored, or bypassed."""
    body = _flat(SKILL_MD)
    assert "**gate a is one layer of defence and never replaces gate b.**" in body
    gates = _flat(GATES)
    for case in ("no invocation-policy mechanism at all", "ignores the policy",
                 "fallback distribution path"):
        assert case in gates, f"approval-gates omits the case {case!r}"


@pytest.mark.parametrize("not_approval", [
    "explicit invocation is not approval",
    "a message from an agent or subagent is not user approval",
    "a hook, automation, or configuration setting is not approval",
    "prior approval of a different proposal is not approval of this one",
])
def test_what_is_not_approval(not_approval):
    assert not_approval in _flat(GATES), f"approval-gates omits: {not_approval!r}"


# ---------------------------------------------------------------- profile

def test_approved_proposal_application_profile_is_selected():
    from _common import SKILL_PROFILE, SKILL_SAFETY_PROFILES

    assert SKILL_PROFILE["apply-refinement"] == "approved-proposal-application"
    assert set(SKILL_SAFETY_PROFILES) == {
        "read-only", "approval-gated-mutation", "bounded-verification",
        "plan-bounded-orchestration", "proposal-only-mutation",
        "approved-proposal-application"}


@pytest.mark.parametrize("key,expected", [
    ("executes_commands", True),
    ("executes_configured_gates_only", True),
    ("spawns_agents", False),
    ("requires_explicit_invocation", True),
    ("requires_mutation_approval", True),
    ("applies_single_proposal_only", True),
    ("modifies_proposal_targets_only", True),
    ("refuses_skill_self_modification", True),
    ("validates_current_hash", True),
    ("records_rollback_information", True),
    ("reverts_on_verification_failure", True),
    ("persists_approval_token", False),
    ("requires_repository_contained_paths", True),
    ("rejects_symlink_escape", True),
    ("installs_packages", False),
    ("modifies_user_settings", False),
    ("network_access", False),
])
def test_declared_contract(key, expected):
    assert _declared()[key] == expected


@pytest.mark.parametrize("key,bad", [
    ("requires_mutation_approval", False),
    ("applies_single_proposal_only", False),
    ("modifies_proposal_targets_only", False),
    ("refuses_skill_self_modification", False),
    ("validates_current_hash", False),
    ("records_rollback_information", False),
    ("reverts_on_verification_failure", False),
    ("persists_approval_token", True),
    ("executes_configured_gates_only", False),
    ("spawns_agents", True),
])
def test_flipping_a_boundary_fails_validation(plugin_tree, key, bad):
    import validate_skills

    md = plugin_tree / "skills" / "apply-refinement" / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    start = text.index(f"{key}: ")
    end = text.index("\n", start)
    md.write_text(text[:start] + f"{key}: {str(bad).lower()}" + text[end:], encoding="utf-8")

    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_MUTATION_NOT_PERMITTED" in codes, codes


def test_execution_is_granted_and_spawning_is_not():
    """Two profiles may execute; still only one may delegate."""
    from _common import (PROFILES_PERMITTING_AGENT_SPAWN, PROFILES_PERMITTING_EXECUTION,
                         SKILL_SAFETY_PROFILES)

    assert PROFILES_PERMITTING_EXECUTION == ["bounded-verification",
                                             "approved-proposal-application"]
    assert PROFILES_PERMITTING_AGENT_SPAWN == ["plan-bounded-orchestration"]
    executing = [n for n, p in SKILL_SAFETY_PROFILES.items() if p["executes_commands"]]
    assert sorted(executing) == sorted(PROFILES_PERMITTING_EXECUTION)


def test_write_roots_exclude_the_plugin_itself():
    from _common import ALLOWED_WRITE_PATH_ROOTS, PROFILES_REQUIRING_PATH_ROOTS

    assert "approved-proposal-application" in PROFILES_REQUIRING_PATH_ROOTS
    roots = ALLOWED_WRITE_PATH_ROOTS["apply-refinement"]
    assert roots == [".agent-harness/", "CLAUDE.md", "AGENTS.md"]
    assert not any("plugins" in r for r in roots)
    assert _declared()["allowed_path_roots"] == roots


# ------------------------------------------------- skill self-modification

def test_skill_items_are_refused_not_merely_discouraged():
    body = _flat(SKILL_MD)
    assert "**a `skill` item is never applied here.**" in body
    assert "absent from the write roots" in body
    application = _flat(APPLICATION)
    assert "there is deliberately no code path for it" in application
    assert "not a disabled one, not a guarded one" in application


# ---------------------------------------------------------------- staleness

def test_current_hash_mismatch_stops_the_application():
    body = _flat(SKILL_MD)
    assert "**stop, report the drift, apply nothing**" in body
    assert "the diff a human approved is not the diff that would land" in body


def test_null_current_hash_is_reported_not_assumed_verified():
    assert "where `current_hash` is `null`, say so plainly" in _flat(SKILL_MD)


# ---------------------------------------------------------------- rollback

def test_rollback_is_recorded_before_the_first_write():
    body = _flat(SKILL_MD)
    assert "**before the first write**, record how to undo everything" in body
    assert "**no rollback information means no application**" in body
    rollback = _flat(ROLLBACK)
    assert "describes the state the change already produced" in rollback


@pytest.mark.parametrize("mode,marker", [
    ("git", "the current `head` revision"),
    ("no-git", ".agent-harness/proposals/<proposal-id>.backup/"),
])
def test_both_rollback_modes_are_defined(mode, marker):
    assert marker in _flat(ROLLBACK), f"rollback contract omits the {mode} mode"


def test_verification_failure_reverts_everything():
    body = _flat(SKILL_MD)
    assert "**revert everything**, then `status: failed`" in body
    assert "**never report success while any part failed" in body
    assert "revert everything this application wrote** — every target" in _flat(ROLLBACK)


def test_failed_revert_reports_exact_partial_state():
    rollback = _flat(ROLLBACK)
    assert "**stop and report the exact partial state**" in rollback
    assert "guessing is worse than admitting the boundary" in rollback


def test_git_is_never_executed_for_revert():
    body = _flat(SKILL_MD)
    assert "**do not run git yourself**" in body
    assert "could discard work the user had in progress" in _flat(ROLLBACK)


# ---------------------------------------------------------------- verification

def test_only_configured_gates_may_run():
    body = _flat(SKILL_MD)
    assert "the same `verification.gates[]` entries `verify-work` uses" in body
    assert "**no other command may run.**" in body
    assert "no gates are configured, say verification could not be established" in body


# ---------------------------------------------------------------- status

def test_status_values_match_the_schema_enum():
    enum = PROPOSAL_SCHEMA["properties"]["status"]["enum"]
    body = _flat(SKILL_MD)
    assert set(enum) == {"proposed", "approved", "rejected", "applied", "failed",
                         "reverted"}
    for value in enum:
        assert f"`{value}`" in body, f"SKILL.md omits status {value!r}"


def test_single_proposal_per_run():
    body = _flat(SKILL_MD)
    assert "**exactly one proposal per run.** never apply two, never batch" in body
    assert "never batch, never apply two" in _flat(APPLICATION)


# ------------------------------------------------- milestone: M2 complete

def test_all_seven_production_skills_are_implemented():
    from _common import (ALLOWED_SKILLS, FORBIDDEN_PRODUCTION_SKILLS,
                         IMPLEMENTED_PRODUCTION_SKILLS, PLANNED_PRODUCTION_SKILLS)

    assert sorted(IMPLEMENTED_PRODUCTION_SKILLS) == sorted(PLANNED_PRODUCTION_SKILLS)
    assert FORBIDDEN_PRODUCTION_SKILLS == [], "no production Skill name remains forbidden"
    assert {d.name for d in SKILLS.iterdir() if d.is_dir()} == set(ALLOWED_SKILLS)
    assert len(IMPLEMENTED_PRODUCTION_SKILLS) == 7


def test_no_forbidden_names_remain():
    """The allowlist is now the full planned set; nothing is left to reject."""
    assert FORBIDDEN_PRODUCTION_SKILLS == []


@pytest.mark.parametrize("skill,profile", [
    ("plan-work", "read-only"),
    ("init-project", "approval-gated-mutation"),
    ("verify-work", "bounded-verification"),
    ("doctor", "read-only"),
    ("orchestrate", "plan-bounded-orchestration"),
    ("refine-harness", "proposal-only-mutation"),
])
def test_existing_skills_keep_their_profiles(skill, profile):
    from _common import SKILL_PROFILE

    assert SKILL_PROFILE[skill] == profile


def test_no_bundled_helper():
    import validate_skills

    for sub in ("scripts", "assets", "bin"):
        assert not (APPLY / sub).exists()
    for manifest in validate_skills.DEPENDENCY_MANIFESTS:
        assert not (APPLY / manifest).exists()
