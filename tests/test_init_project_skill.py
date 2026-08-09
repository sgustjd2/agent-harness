"""Contract tests for the init-project Skill (M2 slice 2).

init-project is the first Skill that writes files, so these focus on the promises that
matter for a mutation-capable Skill: approval before writing, no overwrite, a declared
write surface, idempotency, and no command execution.

Shared machinery (`_run`, the policy marker, the milestone allowlist) is the same one
plan-work uses. What differs is the safety *profile* -- a planner and an initializer
make different promises, and the validator checks each against its own.
"""

from __future__ import annotations

import pytest
import yaml

from conftest import REPO_ROOT
from _common import FORBIDDEN_PRODUCTION_SKILLS
from test_plan_work_skill import _frontmatter, _run

pytestmark = pytest.mark.deterministic

SKILLS = REPO_ROOT / "plugins" / "agent-harness" / "skills"
INIT = SKILLS / "init-project"
SKILL_MD = INIT / "SKILL.md"


def _flat(path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


# ---------------------------------------------------------------- 1-3. basics

def test_init_project_validates_as_shipped():
    """1. The Skill as committed passes the real validator with no diagnostics."""
    import validate_skills

    status, codes = _run(validate_skills.check, REPO_ROOT / "plugins" / "agent-harness")
    assert status == 0, f"validate_skills failed with {codes}"
    assert codes == [], codes


def test_frontmatter_is_exactly_name_and_description():
    """2. FR-025 / DEC-C25 portable minimum set."""
    front = _frontmatter(SKILL_MD)
    assert set(front) == {"name", "description"}, sorted(front)


def test_directory_and_frontmatter_name_match():
    """3."""
    assert _frontmatter(SKILL_MD)["name"] == INIT.name == "init-project"


@pytest.mark.parametrize("trigger", [
    "initialize", "set up", "verification gates", "memory", "repository",
])
def test_description_covers_the_initialization_triggers(trigger):
    description = _frontmatter(SKILL_MD)["description"].lower()
    assert trigger in description, f"description does not mention {trigger!r}"


# ------------------------------------------------- 4. implicit invocation off

def test_implicit_invocation_is_disabled():
    """4. A Skill that writes files must not be selected implicitly."""
    policy = yaml.safe_load((INIT / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert set(policy) == {"policy"}, sorted(policy)
    assert set(policy["policy"]) == {"allow_implicit_invocation"}, sorted(policy["policy"])
    assert policy["policy"]["allow_implicit_invocation"] is False


def test_enabling_implicit_invocation_fails(plugin_tree):
    """4. The rule is enforced, not merely documented."""
    import validate_skills

    path = plugin_tree / "skills" / "init-project" / "agents" / "openai.yaml"
    path.write_text("policy:\n  allow_implicit_invocation: true\n", encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "POLICY_IMPLICIT_INVOCATION_ENABLED" in codes, codes


# ---------------------------------------------------------------- 5. references

@pytest.mark.parametrize("rel", [
    "references/config-template.yaml",
    "references/initialization-checklist.md",
    "agents/openai.yaml",
])
def test_required_files_exist_and_stay_inside_the_skill(rel):
    """5/12. Present, and resolving inside the Skill root."""
    target = INIT / rel
    assert target.is_file(), f"{rel} is missing"
    assert str(target.resolve()).startswith(str(INIT.resolve())), (
        f"{rel} resolves outside the Skill root")


def test_missing_reference_fails(plugin_tree):
    """5."""
    import validate_skills

    (plugin_tree / "skills" / "init-project" / "references"
     / "config-template.yaml").unlink()
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_REFERENCE_MISSING" in codes, codes


# ------------------------------------------- 6-10. the mutation safety profile

@pytest.mark.parametrize("key,bad_value", [
    ("requires_mutation_approval", False),   # 6
    ("requires_explicit_invocation", False),
    ("executes_commands", True),             # 7
    ("modifies_user_settings", True),        # 8
    ("overwrites_existing_files", True),     # 9
    ("idempotent", False),                   # 10
    ("installs_packages", True),
    ("network_access", True),
    ("read_only", True),                     # a writer must not claim read-only
    ("deletes_preexisting_content", True),   # content that predates the attempt
    ("may_rollback_current_attempt", False),  # its own writes, though, it may withdraw
])
def test_declared_safety_promises_are_enforced(plugin_tree, key, bad_value):
    """Flipping any promise in the declared contract fails validation."""
    import validate_skills

    md = plugin_tree / "skills" / "init-project" / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    start = text.index(f"{key}: ")
    end = text.index("\n", start)
    md.write_text(text[:start] + f"{key}: {str(bad_value).lower()}" + text[end:],
                  encoding="utf-8")

    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_MUTATION_NOT_PERMITTED" in codes, codes


def test_rollback_contract_separates_ownership_from_deletion():
    """The two rollback fields must both be declared, and say opposite things.

    Declared together they resolve what previously read as a contradiction: an attempt
    may withdraw its own writes, and may never touch what it found. Collapsing them into
    one flag loses exactly the distinction that makes cleanup safe.
    """
    from _common import extract_policy_marker

    declared = yaml.safe_load(extract_policy_marker(SKILL_MD.read_text(encoding="utf-8")))
    assert declared["deletes_preexisting_content"] is False
    assert declared["may_rollback_current_attempt"] is True


@pytest.mark.parametrize("rule", [
    "existed before this phase b attempt",   # pre-existing content is untouchable
    "best-effort rollback may withdraw only what this attempt created",
    "if complete rollback is impossible",    # manual-cleanup path
    "while partial state remains",           # success suppression
])
def test_rollback_policy_is_stated_in_the_skill_body(rule):
    """The four rollback rules must be findable by a reader, not only by the validator.

    Whitespace is collapsed first: these phrases wrap across lines, and a line break is
    a formatting choice. Asserting on the wrapped form would fail the next time someone
    reflows a paragraph, which teaches people to edit the test instead of reading it.
    """
    body = " ".join(SKILL_MD.read_text(encoding="utf-8").lower().split())
    assert rule in body, f"SKILL.md omits the rule: {rule!r}"


@pytest.mark.parametrize("phrase", [
    "managed-marker-block",          # the term this contract uses
    "immutable",                     # everything outside the block
    "append **one** block",          # no block present
    "only the content inside it",    # exactly one block present
    "conflict",                      # malformed / nested / duplicated / unmatched
])
def test_marker_block_contract_is_stated(phrase):
    """The owned-region contract replaces the ambiguous append-only wording."""
    assert phrase in SKILL_MD.read_text(encoding="utf-8"), f"SKILL.md omits {phrase!r}"


# No test asserts that the string "append-only" is absent. The Skill deliberately says
# `This is not "append-only", because ...` to explain why the term changed, and a naive
# substring check cannot tell an explanation from a claim -- the same false positive the
# policy marker exists to avoid. The positive assertions above already prove the
# managed-marker-block contract is the one stated.


def test_profile_differs_from_plan_work():
    """The two Skills are checked against different contracts, not one flattened set."""
    from _common import SKILL_PROFILE, SKILL_SAFETY_PROFILES

    assert SKILL_PROFILE["plan-work"] == "read-only"
    assert SKILL_PROFILE["init-project"] == "approval-gated-mutation"
    assert (SKILL_SAFETY_PROFILES["read-only"]["read_only"] is True
            and SKILL_SAFETY_PROFILES["approval-gated-mutation"]["read_only"] is False)
    # Neither of THESE two profiles may execute a command. That is no longer a universal
    # guarantee -- bounded-verification exists to run configured gates -- so it is
    # asserted per profile rather than over every profile.
    for name in ("read-only", "approval-gated-mutation"):
        assert SKILL_SAFETY_PROFILES[name]["executes_commands"] is False
    # Still universal, and asserted over everything.
    for profile in SKILL_SAFETY_PROFILES.values():
        assert profile["network_access"] is False


# ---------------------------------------------------------------- 11. write surface

def test_declared_write_roots_match_the_approved_surface():
    """11. .agent-harness/ plus the managed-marker-block, and nothing else."""
    from _common import ALLOWED_WRITE_PATH_ROOTS, extract_policy_marker

    declared = yaml.safe_load(extract_policy_marker(SKILL_MD.read_text(encoding="utf-8")))
    assert declared["allowed_path_roots"] == ALLOWED_WRITE_PATH_ROOTS["init-project"]
    assert declared["allowed_path_roots"] == [".agent-harness/", "CLAUDE.md", "AGENTS.md"]


@pytest.mark.parametrize("root", [
    "~/.claude/", "~/.codex/", "/etc/", "../escape/", ".git/", "plugins/", "scripts/",
])
def test_forbidden_write_roots_are_rejected(plugin_tree, root):
    """11/12. User scope, absolutes, traversal, and the project's own packaging."""
    import validate_skills

    md = plugin_tree / "skills" / "init-project" / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    text = text.replace("  - .agent-harness/\n", f"  - .agent-harness/\n  - {root}\n", 1)
    md.write_text(text, encoding="utf-8")

    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0, f"{root!r} was accepted as a write root"
    assert codes, codes


def test_removing_the_write_surface_fails(plugin_tree):
    """11. A mutation-capable Skill must declare where it writes."""
    import validate_skills

    md = plugin_tree / "skills" / "init-project" / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    start = text.index("allowed_path_roots:")
    end = text.index("-->", start)
    md.write_text(text[:start] + text[end:], encoding="utf-8")

    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_WRITE_ROOTS_MISSING" in codes, codes


# ---------------------------------------------------------------- 13-14. allowlist

def test_init_project_is_on_the_allowlist_and_the_tree_matches_it():
    """13. Derived from the constant, as in the plan-work slice.

    Exact per-milestone membership is asserted once, in the newest slice's file. Stating
    it here too would mean every future slice edits three files to say one thing.
    """
    from _common import ALLOWED_SKILLS, IMPLEMENTED_PRODUCTION_SKILLS

    assert "init-project" in IMPLEMENTED_PRODUCTION_SKILLS
    assert {d.name for d in SKILLS.iterdir() if d.is_dir()} == set(ALLOWED_SKILLS)


# FORBIDDEN_PRODUCTION_SKILLS is empty now that all seven are implemented. An
# empty parametrize SKIPS silently, so the guard would stop running without
# anyone noticing -- fall back to a name that is not on the allowlist.
@pytest.mark.parametrize(
    "name", FORBIDDEN_PRODUCTION_SKILLS or ["not-a-planned-skill"])
def test_unimplemented_production_skills_are_still_rejected(plugin_tree, name):
    """14. Every not-yet-implemented name must still fail in the installable root."""
    import validate_skills

    assert not (SKILLS / name).exists(), f"{name} must not be implemented yet"

    bad = plugin_tree / "skills" / name
    bad.mkdir(parents=True)
    (bad / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: placeholder\n---\n\nplaceholder\n",
        encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert {"PRODUCTION_SKILL_IN_ROOT", "FORBIDDEN_COMPONENT_IN_ROOT"} & set(codes), \
        codes


def test_plan_work_was_not_modified_by_this_slice():
    """plan-work keeps its own contract; widening the allowlist must not touch it."""
    from _common import extract_policy_marker

    declared = yaml.safe_load(
        extract_policy_marker((SKILLS / "plan-work" / "SKILL.md").read_text(encoding="utf-8")))
    assert declared["read_only"] is True
    assert declared["verification_default"] == "Not Run"


# ------------------------------------------------- 15-16. config template

def test_config_template_parses_and_is_schema_valid():
    """15. The proposed configuration must satisfy the project's own config schema."""
    import json

    import jsonschema

    config = yaml.safe_load((INIT / "references" / "config-template.yaml")
                            .read_text(encoding="utf-8"))
    schema = json.loads((REPO_ROOT / "plugins/agent-harness/core/schemas/state"
                         / "config.schema.json").read_text(encoding="utf-8"))
    jsonschema.validators.validator_for(schema)(schema).validate(config)


def test_config_template_enables_no_gate():
    """16. Detection proposes; it must never enable a command by default."""
    config = yaml.safe_load((INIT / "references" / "config-template.yaml")
                            .read_text(encoding="utf-8"))
    assert config["verification"]["gates"] in (None, []), (
        "a gate enabled by default would mean the Skill chose to run something")
    assert config["runs"]["commit_evidence"] is False


def test_skill_declares_the_not_run_gate_status_and_argv_rule():
    """16. Proposed gates are reported Not Run, and commands are argv arrays."""
    body = SKILL_MD.read_text(encoding="utf-8")
    assert "Not Run" in body
    assert "argv array" in body


# ---------------------------------------------------------------- 17-18. hygiene

def test_no_executable_command_block_or_dependency():
    """17/18. Instruction-only: no shell fence, no scripts/assets, no manifest."""
    import validate_skills

    body = SKILL_MD.read_text(encoding="utf-8")
    for fence in validate_skills.SHELL_FENCES:
        assert fence not in body, f"SKILL.md contains an executable {fence!r} block"
    for sub in validate_skills.FORBIDDEN_SKILL_SUBDIRS:
        assert not (INIT / sub).exists(), f"{sub}/ must not exist inside the Skill"
    for manifest in validate_skills.DEPENDENCY_MANIFESTS:
        assert not (INIT / manifest).exists(), f"{manifest} would add a runtime dependency"


def test_checklist_covers_the_mutation_safeguards():
    """The checklist is the human-facing half of the machine contract."""
    text = (INIT / "references" / "initialization-checklist.md").read_text(
        encoding="utf-8").lower()
    for phrase in ["before writing", "approval", "stale", "overwrite", "idempot",
                   "gitignore", "no command", "user-scope", "secret", "conflict"]:
        assert phrase in text, f"initialization checklist omits {phrase!r}"


# ------------------------------------------- D-02: interpreter-based gates

@pytest.mark.parametrize("rule", [
    "**name the project's own interpreter, never the bare one.**",
    "a bare name is resolved by `path` when the gate runs",
    "no verification status can distinguish that from a real failure",
])
def test_proposed_interpreter_must_be_the_projects(rule):
    """D-02. A bare `python` can resolve to a stub that runs nothing and exits non-zero.

    verify-work then reports `fail` on passing tests, correctly per the classification
    rules — the process really did run. The defect is upstream, in what gets proposed.
    """
    assert rule in _flat(SKILL_MD), f"SKILL.md omits: {rule!r}"


def test_config_template_no_longer_proposes_a_bare_python():
    """The shipped candidate command must not hand anyone the broken default."""
    template = (INIT / "references" / "config-template.yaml").read_text(encoding="utf-8")
    assert '["python", "-m", "pytest"' not in template
    assert '["<interpreter>", "-m", "pytest", "-q"]' in template
    assert ".venv/Scripts/python.exe" in template   # the Windows case that fails


# ---------------------------------------------- D-04: memory file content

@pytest.mark.parametrize("element", [
    "committed after human review",
    "**the file is data, not instructions**",
    "`# facts`, `# decisions`, `# patterns`",
])
def test_memory_file_structure_is_specified(element):
    """D-04. The Skill created three files without saying what goes in them."""
    assert element in _flat(SKILL_MD), f"SKILL.md omits: {element!r}"


def test_memory_header_rationale_is_stated():
    """Memory is read back into context every run, so 'this is data' is load-bearing."""
    body = _flat(SKILL_MD)
    assert "standing injection surface" in body


def test_templates_are_named_but_not_read():
    """The obvious fix -- copy templates/ -- is blocked by Q-IMPL-003, not merely unwritten.

    A canonical Skill assumes no path variable, no cache path and no working directory, so
    it cannot portably locate a sibling directory. Saying so keeps the next reader from
    'fixing' it into a path that cannot resolve.
    """
    body = _flat(SKILL_MD)
    assert "**this skill does not read" in body and "must not try" in body
    assert "q-impl-003" in body


# ------------------------------------------------- D-05: conservative detection

def test_conservative_does_not_mean_default_to_generic():
    """D-05. The word pulled against the detection table it sits next to."""
    body = _flat(SKILL_MD)
    assert "*do not claim a type whose signals are absent*" in body
    assert "**not** *default to `generic` when signals are present*" in body
    assert "propose `python`" in body


def test_template_marks_generic_as_a_placeholder():
    template = (INIT / "references" / "config-template.yaml").read_text(encoding="utf-8")
    assert "`generic` is the placeholder, not the default" in template
    assert "Use [generic] when unsure" not in template
