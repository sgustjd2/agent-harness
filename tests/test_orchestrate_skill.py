"""Contract tests for the orchestrate Skill (M2 slice 5).

orchestrate has the widest WRITE authority in the product -- it writes source and may
delegate -- while executing no commands in this milestone. These tests concentrate on the
boundaries: planned paths only and repository-contained, harness state read-only, scope
enforced in both directions, conflicts never auto-merged, and completion not something
this Skill may declare.

Nothing here spawns an agent or runs an orchestration command. The portable contract is
validated statically.
"""

from __future__ import annotations

import pytest
import yaml

from conftest import REPO_ROOT
from _common import FORBIDDEN_PRODUCTION_SKILLS
from test_plan_work_skill import _frontmatter, _run

pytestmark = pytest.mark.deterministic

SKILLS = REPO_ROOT / "plugins" / "agent-harness" / "skills"
ORCH = SKILLS / "orchestrate"
SKILL_MD = ORCH / "SKILL.md"
CONTRACT = ORCH / "references" / "orchestration-contract.md"
HANDOFF = ORCH / "references" / "handoff-contract.md"
CONFLICT = ORCH / "references" / "conflict-policy.md"


def _declared() -> dict:
    from _common import extract_policy_marker

    return yaml.safe_load(extract_policy_marker(SKILL_MD.read_text(encoding="utf-8")))


def _flat(path) -> str:
    """Lowercased, whitespace-collapsed: line wrapping is formatting, not content."""
    return " ".join(path.read_text(encoding="utf-8").lower().split())


# ---------------------------------------------------------------- 1-3. structure

def test_orchestrate_validates_as_shipped():
    """1."""
    import validate_skills

    status, codes = _run(validate_skills.check, REPO_ROOT / "plugins" / "agent-harness")
    assert status == 0, f"validate_skills failed with {codes}"
    assert codes == [], codes


def test_frontmatter_is_exactly_name_and_description():
    """2."""
    front = _frontmatter(SKILL_MD)
    assert set(front) == {"name", "description"}, sorted(front)
    assert front["name"] == ORCH.name == "orchestrate"


@pytest.mark.parametrize("trigger", [
    "execute this plan", "coordinate these tasks", "delegate", "dependency order",
])
def test_description_covers_the_triggers(trigger):
    assert trigger in _frontmatter(SKILL_MD)["description"].lower()


def test_implicit_invocation_is_disabled():
    """3."""
    from _common import IMPLICIT_INVOCATION_MUST_BE_OFF

    assert "orchestrate" in IMPLICIT_INVOCATION_MUST_BE_OFF
    policy = yaml.safe_load((ORCH / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert set(policy) == {"policy"}
    assert set(policy["policy"]) == {"allow_implicit_invocation"}
    assert policy["policy"]["allow_implicit_invocation"] is False


# ------------------------------------------------------------- 4-7, 26-27. profile

def test_plan_bounded_orchestration_profile_is_selected():
    """4."""
    from _common import SKILL_PROFILE, SKILL_SAFETY_PROFILES

    assert SKILL_PROFILE["orchestrate"] == "plan-bounded-orchestration"
    # The exact profile roster belongs to the newest slice's test file; what matters here
    # is that orchestrate's own profile still exists and still carries its grants.
    assert "plan-bounded-orchestration" in SKILL_SAFETY_PROFILES


@pytest.mark.parametrize("key,expected", [
    ("executes_commands", False),                  # deferred (hardening)
    ("spawns_agents", True),                       # 6
    ("modifies_source", True),                     # 7
    ("requires_ready_plan", True),                 # 8
    ("executes_planned_commands_only", True),      # 9
    ("modifies_planned_paths_only", True),         # 10
    ("destructive_actions_require_approval", True),  # 11
    ("respects_dependency_graph", True),           # 12
    ("max_parallel_from_config", True),            # 13
    ("auto_merge_conflicts", False),               # 21
    ("requires_repository_contained_paths", True),
    ("rejects_symlink_escape", True),
    ("modifies_harness_state", False),
    ("requires_explicit_invocation", True),
    ("network_access", False),
    ("modifies_user_settings", False),
    ("evidence_persistence", "response-only"),     # 26
    ("run_state_runtime", "deferred"),             # 27
])
def test_declared_contract(key, expected):
    assert _declared()[key] == expected


@pytest.mark.parametrize("key,bad", [
    ("executes_planned_commands_only", False),
    ("modifies_planned_paths_only", False),
    ("destructive_actions_require_approval", False),
    ("respects_dependency_graph", False),
    ("auto_merge_conflicts", True),
    ("requires_ready_plan", False),
    ("network_access", True),
    ("executes_commands", True),                    # must stay deferred
    ("requires_repository_contained_paths", False),
    ("rejects_symlink_escape", False),
    ("modifies_harness_state", True),
])
def test_flipping_a_boundary_fails_validation(plugin_tree, key, bad):
    """Each limit on the widest profile is enforced, not merely written down."""
    import validate_skills

    md = plugin_tree / "skills" / "orchestrate" / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    start = text.index(f"{key}: ")
    end = text.index("\n", start)
    md.write_text(text[:start] + f"{key}: {str(bad).lower()}" + text[end:], encoding="utf-8")

    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_MUTATION_NOT_PERMITTED" in codes, codes


def test_execution_and_spawning_are_separately_gated():
    """5/6. verify-work runs commands but must never delegate."""
    from _common import (PROFILES_PERMITTING_AGENT_SPAWN, PROFILES_PERMITTING_EXECUTION,
                         SKILL_SAFETY_PROFILES, UNIVERSAL_SKILL_POLICY)

    # orchestrate does NOT execute in this milestone; verify-work is the only one that may.
    assert PROFILES_PERMITTING_EXECUTION == ["bounded-verification"]
    assert "plan-bounded-orchestration" not in PROFILES_PERMITTING_EXECUTION
    assert PROFILES_PERMITTING_AGENT_SPAWN == ["plan-bounded-orchestration"]
    assert SKILL_SAFETY_PROFILES["bounded-verification"]["spawns_agents"] is False
    assert SKILL_SAFETY_PROFILES["bounded-verification"]["executes_commands"] is True
    # executes_commands must not creep back into the universal set.
    assert "executes_commands" not in UNIVERSAL_SKILL_POLICY
    assert UNIVERSAL_SKILL_POLICY["network_access"] is False

    executing = [n for n, p in SKILL_SAFETY_PROFILES.items() if p["executes_commands"]]
    spawning = [n for n, p in SKILL_SAFETY_PROFILES.items() if p.get("spawns_agents")]
    assert sorted(executing) == sorted(PROFILES_PERMITTING_EXECUTION)
    assert spawning == PROFILES_PERMITTING_AGENT_SPAWN


def test_orchestrate_has_no_declared_write_path_roots():
    """Scope comes from the plan's writes[], not from a static root list."""
    from _common import ALLOWED_WRITE_PATH_ROOTS, PROFILES_REQUIRING_PATH_ROOTS

    assert "plan-bounded-orchestration" not in PROFILES_REQUIRING_PATH_ROOTS
    assert "orchestrate" not in ALLOWED_WRITE_PATH_ROOTS


# ------------------------------------------------- 8-11. plan authority and approval

@pytest.mark.parametrize("rule", [
    "no ready plan → `blocked`**, recommending `plan-work`",
    "never synthesize a plan",
    "several ready runs and the target is unclear → ask which one.** never pick silently",
    "reject a cyclic graph. never repair a malformed plan",
])
def test_ready_plan_is_required(rule):
    """8."""
    assert rule in _flat(SKILL_MD), f"SKILL.md omits: {rule!r}"


@pytest.mark.parametrize("field", [
    "task_id", "role", "completion_criteria", "depends_on", "reads", "writes",
])
def test_required_plan_task_fields_are_named(field):
    """8."""
    assert field in _flat(SKILL_MD), f"SKILL.md omits the plan field {field!r}"


@pytest.mark.parametrize("rule", [
    "**`orchestrate` executes no commands in this milestone.**",
    "**do not extract command-looking prose from `plan.md` and run it.**",
    "**do not execute verification gates.** `verify-work` remains the only production",
    "never infer a command from `package.json`",
])
def test_orchestrate_executes_no_commands(rule):
    """Command execution is deferred until a validated representation exists."""
    assert rule in _flat(SKILL_MD), f"SKILL.md omits: {rule!r}"


def test_command_dependent_task_becomes_blocked():
    """A task needing a command is blocked; unrelated work continues."""
    body = _flat(SKILL_MD)
    assert "mark it **`blocked`**, state" in body
    assert "continue unrelated tasks that can safely proceed" in body


def test_command_execution_is_deferred_not_abandoned():
    """The reason is a missing representation, stated so it can be lifted later."""
    body = _flat(SKILL_MD)
    assert "no structured, validated command representation" in body
    assert "no argv\narray, no working directory, no timeout".replace("\n", " ") in body


def test_verify_work_execution_is_not_weakened():
    """verify-work keeps its execution grant intact."""
    from _common import SKILL_PROFILE, SKILL_SAFETY_PROFILES, extract_policy_marker

    assert SKILL_PROFILE["verify-work"] == "bounded-verification"
    vw = SKILL_SAFETY_PROFILES["bounded-verification"]
    assert vw["executes_commands"] is True
    assert vw["executes_configured_gates_only"] is True
    declared = yaml.safe_load(extract_policy_marker(
        (SKILLS / "verify-work" / "SKILL.md").read_text(encoding="utf-8")))
    assert declared["executes_commands"] is True


# ------------------------------------------- repository containment (SEC-05/06)

@pytest.mark.parametrize("rule", [
    "**being listed in `writes[]` is not permission to leave the repository.**",
    "interpret it relative to the **repository root**",
    "**normalize** it before any comparison",
    "reject **path traversal** that escapes the repository",
    "reject **absolute paths** outside the repository",
    "reject a path whose **symlink resolution** escapes the repository",
])
def test_planned_paths_must_be_repository_contained(rule):
    """Traversal escape, absolute-outside, and symlink escape each rejected."""
    assert rule in _flat(SKILL_MD), f"SKILL.md omits: {rule!r}"


def test_comparisons_use_normalized_contained_paths():
    """Raw-string comparison would let two spellings of one path miss each other."""
    body = _flat(SKILL_MD)
    assert "**normalized, repository-contained** form" in body
    assert "disagree about whether they collide" in body


def test_unsafe_planned_path_blocks_without_repairing_the_plan():
    body = _flat(SKILL_MD)
    assert "**do not delegate that task**, disposition **`blocked`**" in body
    assert "**never repair or rewrite the plan**" in body


# ------------------------------------------------- harness-state protection

def test_agent_harness_state_is_read_only():
    """config.yaml and plan.md may be read; no .agent-harness path may be written."""
    body = _flat(SKILL_MD)
    assert "**harness state is read-only here.**" in body
    assert "may write **no** `.agent-harness` path at all" in body
    assert "a task whose `writes[]` targets `.agent-harness/**` is **blocked**" in body


@pytest.mark.parametrize("owner", [
    "apply-refinement", "proposal", "deferred run-state",
])
def test_harness_state_owners_are_named(owner):
    """Each protected path has an owner; writing here would route around all three."""
    assert owner in _flat(SKILL_MD)


def test_managed_marker_block_is_not_modified_by_orchestrate():
    body = _flat(SKILL_MD)
    assert "do not modify the managed marker block" in body
    assert "belongs to `init-project`" in body


@pytest.mark.parametrize("action", [
    "force push", "destructive file-tree deletion", "migration execution",
    "rewriting remote history", "weakening a permission or sandbox",
])
def test_destructive_actions_require_approval(action):
    """11. Each destructive class named, with the blocked-task consequence."""
    body = _flat(SKILL_MD)
    assert action in body, f"SKILL.md omits the destructive action {action!r}"
    assert "mark that task **blocked**, and continue independent safe tasks" in body


def test_ordinary_planned_work_needs_no_second_approval():
    """11. Re-approving every task would make the gate a formality."""
    body = _flat(SKILL_MD)
    assert "explicit invocation is sufficient" in body
    assert "turns a safety gate into a rubber stamp nobody reads" in body


def test_authorization_is_ready_plan_plus_explicit_invocation():
    """The PRD defines no separate plan-approval gate, so do not claim one."""
    body = _flat(SKILL_MD)
    assert "**a ready plan defines the allowed scope; explicit invocation authorizes " \
           "the work.**" in body
    assert "work outside the plan is unauthorized however the skill was" in body
    # The withdrawn claim must not survive anywhere in the Skill or its references.
    for path in (SKILL_MD, CONTRACT, CONFLICT, HANDOFF):
        assert "a human approved that plan" not in _flat(path), f"{path.name} still claims it"


# ------------------------------------------- 12-17. frontier, parallelism, degradation

def test_dependency_graph_is_respected():
    """12/15."""
    body = _flat(SKILL_MD)
    assert "a task is ready when every `depends_on` is `done`" in body
    assert "a failed dependency skips its dependents; unrelated tasks continue" in body


def test_parallel_cap_comes_from_config_and_schema():
    """13. Both bounds, and the schema's own cap."""
    import json

    contract = _flat(CONTRACT)
    assert "`orchestration.max_parallel_agents` | 3 | **5** |" in contract
    assert "`orchestration.max_delegation_depth` | 1 | **2** |" in contract
    assert "never exceed the configured value" in _flat(SKILL_MD)

    schema = json.loads((REPO_ROOT / "plugins/agent-harness/core/schemas/state"
                         / "config.schema.json").read_text(encoding="utf-8"))
    orch = schema["properties"]["orchestration"]["properties"]
    assert orch["max_parallel_agents"]["maximum"] == 5
    assert orch["max_delegation_depth"]["maximum"] == 2


def test_overlapping_writes_force_sequential():
    """14."""
    assert "any overlap means those tasks are reclassified to sequential execution" \
        in _flat(CONFLICT)
    assert "its planned writes do not overlap another simultaneously selected task" \
        in _flat(SKILL_MD)


def test_degradation_must_record_a_reason():
    """16."""
    body = _flat(SKILL_MD)
    assert "never degrade silently" in body
    assert "`orchestration_mode: sequential` with a non-empty `degraded_reason`" in body


def test_agent_teams_is_not_a_dependency():
    """17."""
    assert "**agent teams is not required**" in _flat(SKILL_MD)
    assert "**agent teams is not a dependency.**" in _flat(CONTRACT)


def test_no_production_agent_definitions_or_bundled_helper():
    """18/28. No host-specific agents, no runtime helper, no state engine."""
    import validate_skills

    for sub in ("scripts", "assets", "bin"):
        assert not (ORCH / sub).exists(), f"{sub}/ must not exist inside orchestrate"
    for manifest in validate_skills.DEPENDENCY_MANIFESTS:
        assert not (ORCH / manifest).exists()
    # No plugin-root agents/ directory, and no run-state runtime modules.
    assert not (REPO_ROOT / "plugins/agent-harness/agents").exists()
    assert not (REPO_ROOT / "scripts/ah.py").exists()
    assert not (REPO_ROOT / "scripts/lib").exists()


# ------------------------------------------------- 19-22. handoff and conflicts

@pytest.mark.parametrize("field", [
    "task_id", "role", "status", "summary", "changed_files", "artifacts",
    "open_questions", "commands_executed", "blockers", "completion_criteria",
])
def test_structured_handoff_fields(field):
    """19."""
    assert field in _flat(HANDOFF), f"handoff contract omits {field!r}"


def test_worker_result_is_recorded_not_paraphrased():
    """19. Paraphrase-first loses the facts evidence exists to keep."""
    handoff = _flat(HANDOFF)
    assert "do not rewrite a worker result into fresh prose before recording it" in handoff
    assert "a summary of a summary" in handoff


def test_only_three_things_are_forwarded():
    """20."""
    handoff = _flat(HANDOFF)
    assert "never forward the whole conversation history" in handoff
    for item in ("summary", "artifacts", "open_questions", "memory excerpt"):
        assert item in handoff


def test_post_run_collision_is_held_never_merged():
    """21."""
    conflict = _flat(CONFLICT)
    assert "do not merge them automatically" in conflict
    assert "hold the later result" in conflict
    assert "there is no automatic conflict merge in this milestone" in conflict


def test_out_of_scope_change_is_a_violation():
    """22."""
    conflict = _flat(CONFLICT)
    assert "the task is **not** `done` — report a **scope violation**" in conflict
    assert "never expand the plan to justify the file that appeared" in conflict
    assert "do not silently keep" in conflict


# --------------------------------------- 23-25. statuses, completion, verify boundary

@pytest.mark.parametrize("status,meaning", [
    ("done", "returned successfully, changes stayed inside `writes[]`"),
    ("failed", "executed, could not satisfy its completion criteria"),
    ("skipped", "deliberately not executed"),
])
def test_terminal_task_statuses(status, meaning):
    """23."""
    contract = _flat(CONTRACT)
    assert f"| `{status}` |" in contract
    assert meaning in contract


def test_blocked_is_not_a_terminal_success_status():
    """23. blocked is a worker disposition that forces the RUN to blocked."""
    body = _flat(SKILL_MD)
    assert "terminal: **`done`**, **`failed`**, **`skipped`**" in body
    assert "it is not terminal, and it forces the run to report `blocked`" in body
    assert "a worker saying \"done\" is not enough by itself" in body


def test_orchestrate_never_declares_completed():
    """24."""
    body = _flat(SKILL_MD)
    assert "**`orchestrate` must never declare `completed`.**" in body
    assert "never present partial success as completion" in body


def test_verify_work_remains_the_verification_owner():
    """25."""
    body = _flat(SKILL_MD)
    assert "`verify-work` owns gate outcomes" in body
    assert "recommended_next_action: verify-work" in body
    assert "do not call it automatically" in body


def test_run_state_runtime_is_deferred():
    """26/27."""
    body = _flat(SKILL_MD)
    assert "no run-state runtime in this milestone" in body
    assert "no `evidence.md`, no `result.md`, no queue, no resume engine" in body


# ---------------------------------------------- 29-30. milestone and no regression

def test_milestone_allowlist_includes_orchestrate():
    """Derived from the constant; exact membership lives in the newest slice's file."""
    from _common import ALLOWED_SKILLS, IMPLEMENTED_PRODUCTION_SKILLS

    assert "orchestrate" in IMPLEMENTED_PRODUCTION_SKILLS
    assert {d.name for d in SKILLS.iterdir() if d.is_dir()} == set(ALLOWED_SKILLS)


@pytest.mark.parametrize("name", FORBIDDEN_PRODUCTION_SKILLS)
def test_remaining_production_skills_are_still_rejected(plugin_tree, name):
    """30. apply-refinement."""
    import validate_skills

    assert not (SKILLS / name).exists()

    bad = plugin_tree / "skills" / name
    bad.mkdir(parents=True)
    (bad / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: placeholder\n---\n\nplaceholder\n",
        encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "PRODUCTION_SKILL_IN_ROOT" in codes, codes


@pytest.mark.parametrize("skill,profile,executes,spawns", [
    ("plan-work", "read-only", False, False),
    ("init-project", "approval-gated-mutation", False, False),
    ("verify-work", "bounded-verification", True, False),
    ("doctor", "read-only", False, False),
])
def test_existing_skills_keep_their_contracts(skill, profile, executes, spawns):
    """29. Adding the widest profile changed no earlier Skill's effective policy."""
    from _common import SKILL_PROFILE, SKILL_SAFETY_PROFILES, extract_policy_marker

    assert SKILL_PROFILE[skill] == profile
    p = SKILL_SAFETY_PROFILES[profile]
    assert p["executes_commands"] is executes
    assert p.get("spawns_agents", False) is spawns
    declared = yaml.safe_load(
        extract_policy_marker((SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")))
    assert declared["executes_commands"] is executes
