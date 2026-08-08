"""Contract tests for the plan-work Skill (M2 slice 1).

These assert the *static contract*: the frontmatter policy, the declared safety
marker, the required references, and the milestone allowlist. They deliberately do not
snapshot the Skill's prose. A golden-text test over instruction wording breaks on every
edit that improves the wording, which trains people to regenerate the golden file
without reading it -- so it stops catching anything.
"""

from __future__ import annotations

import pathlib

import pytest
import yaml

from conftest import REPO_ROOT

pytestmark = pytest.mark.deterministic

SKILLS = REPO_ROOT / "plugins" / "agent-harness" / "skills"
PLAN_WORK = SKILLS / "plan-work"
SKILL_MD = PLAN_WORK / "SKILL.md"


def _run(check, root):
    """Run a validator against a tree and return (status, diagnostic codes)."""
    import _common

    codes: list[str] = []
    original = _common.Report.fail

    def capture(self, code, path, message):
        codes.append(code)
        return original(self, code, path, message)

    _common.Report.fail = capture
    try:
        status = check(root)
    finally:
        _common.Report.fail = original
    return status, codes


def _frontmatter(path: pathlib.Path) -> dict:
    from _authoritative import load_frontmatter

    front, _ = load_frontmatter(path)
    return front


# ---------------------------------------------------------------- 1. valid Skill

def test_plan_work_validates_as_shipped():
    """The Skill as committed passes the real validator with no diagnostics."""
    import validate_skills

    status, codes = _run(validate_skills.check,
                         REPO_ROOT / "plugins" / "agent-harness")
    assert status == 0, f"validate_skills failed with {codes}"
    assert codes == [], codes


# ------------------------------------------------- 2-3. frontmatter and parity

def test_frontmatter_is_exactly_name_and_description():
    """FR-025 / DEC-C25: the portable minimum set, and nothing host-specific."""
    front = _frontmatter(SKILL_MD)
    assert set(front) == {"name", "description"}, (
        f"canonical frontmatter must be exactly name+description, got {sorted(front)}")


def test_directory_and_frontmatter_name_match():
    assert _frontmatter(SKILL_MD)["name"] == PLAN_WORK.name == "plan-work"


@pytest.mark.parametrize("trigger", [
    "plan", "acceptance criteria", "risk", "depend", "verification", "step",
])
def test_description_covers_the_planning_triggers(trigger):
    """The description is the discovery surface; a vague one makes the Skill unreachable."""
    description = _frontmatter(SKILL_MD)["description"].lower()
    assert description.strip()
    assert trigger in description, f"description does not mention {trigger!r}"


# ---------------------------------------------------------------- 4. references

@pytest.mark.parametrize("rel", [
    "references/plan-template.md",
    "references/quality-checklist.md",
    "agents/openai.yaml",
])
def test_required_files_exist_and_stay_inside_the_skill(rel):
    target = PLAN_WORK / rel
    assert target.is_file(), f"{rel} is missing"
    assert str(target.resolve()).startswith(str(PLAN_WORK.resolve())), (
        f"{rel} resolves outside the Skill root")


# ------------------------------------------------- 5-9. negative contract cases

def test_missing_reference_fails(plugin_tree):
    """5. A required reference is deleted."""
    import validate_skills

    (plugin_tree / "skills" / "plan-work" / "references" / "plan-template.md").unlink()
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_REFERENCE_MISSING" in codes, codes


def test_executable_directory_fails(plugin_tree):
    """6/13. A scripts/ directory would make the Skill executable and dependent."""
    import validate_skills

    (plugin_tree / "skills" / "plan-work" / "scripts").mkdir()
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_EXECUTABLE_DIR_PRESENT" in codes, codes


def test_runtime_dependency_manifest_fails(plugin_tree):
    """13. A dependency manifest inside the Skill."""
    import validate_skills

    (plugin_tree / "skills" / "plan-work" / "requirements.txt").write_text(
        "requests\n", encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_RUNTIME_DEPENDENCY" in codes, codes


@pytest.mark.parametrize("key,bad_value,expected", [
    ("modifies_source", True, "SKILL_MUTATION_NOT_PERMITTED"),
    ("modifies_config", True, "SKILL_MUTATION_NOT_PERMITTED"),
    ("executes_commands", True, "SKILL_MUTATION_NOT_PERMITTED"),
    ("spawns_agents", True, "SKILL_MUTATION_NOT_PERMITTED"),
    ("network_access", True, "SKILL_MUTATION_NOT_PERMITTED"),
    ("read_only", False, "SKILL_MUTATION_NOT_PERMITTED"),
    ("verification_default", "Passed", "SKILL_VERIFICATION_DEFAULT_INVALID"),
])
def test_declared_policy_must_stay_read_only(plugin_tree, key, bad_value, expected):
    """7/8/9. Flipping any safety claim in the declared marker fails."""
    import validate_skills

    md = plugin_tree / "skills" / "plan-work" / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    old = f"{key}: "
    line_start = text.index(old)
    line_end = text.index("\n", line_start)
    replacement = str(bad_value).lower() if isinstance(bad_value, bool) else bad_value
    md.write_text(text[:line_start] + f"{key}: {replacement}" + text[line_end:],
                  encoding="utf-8")

    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert expected in codes, codes


def test_policy_marker_removal_fails(plugin_tree):
    """7. The safety contract cannot simply be dropped."""
    import validate_skills

    md = plugin_tree / "skills" / "plan-work" / "SKILL.md"
    text = md.read_text(encoding="utf-8")
    start = text.index("<!-- agent-harness:policy")
    end = text.index("-->", start) + 3
    md.write_text(text[:start] + text[end:], encoding="utf-8")

    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_POLICY_MARKER_MISSING" in codes, codes


@pytest.mark.parametrize("fence", ["```bash", "```sh", "```powershell"])
def test_executable_command_block_fails(plugin_tree, fence):
    """8. A copyable shell block in a read-only Skill."""
    import validate_skills

    md = plugin_tree / "skills" / "plan-work" / "SKILL.md"
    md.write_text(md.read_text(encoding="utf-8")
                  + f"\n\n{fence}\nnpm install\n```\n", encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_COMMAND_BLOCK_PRESENT" in codes, codes


def test_prose_about_commands_is_not_a_violation(plugin_tree):
    """The check must not fire on a sentence that merely discusses commands.

    This is the false positive the marker design exists to avoid: a read-only Skill's
    body has every reason to say what it will not run.
    """
    import validate_skills

    md = plugin_tree / "skills" / "plan-work" / "SKILL.md"
    md.write_text(md.read_text(encoding="utf-8")
                  + "\n\nNever run `npm install`, and do not execute the test suite.\n",
                  encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status == 0, f"explanatory prose was misread as a violation: {codes}"


# ------------------------------------------------- 10-11. milestone allowlist

def test_current_allowlist_is_fixture_plus_plan_work():
    from _common import ALLOWED_SKILLS, IMPLEMENTED_PRODUCTION_SKILLS

    assert IMPLEMENTED_PRODUCTION_SKILLS == ["plan-work"]
    assert set(ALLOWED_SKILLS) == {"m1-discovery-fixture", "plan-work"}
    assert {d.name for d in SKILLS.iterdir() if d.is_dir()} == set(ALLOWED_SKILLS)


@pytest.mark.parametrize("name", [
    "init-project", "orchestrate", "verify-work",
    "refine-harness", "apply-refinement", "doctor",
])
def test_unimplemented_production_skills_are_still_rejected(plugin_tree, name):
    """11. Each of the six remaining names must still fail in the installable root."""
    import validate_skills
    from _common import FORBIDDEN_PRODUCTION_SKILLS

    assert name in FORBIDDEN_PRODUCTION_SKILLS
    assert not (SKILLS / name).exists(), f"{name} must not be implemented in this slice"

    bad = plugin_tree / "skills" / name
    bad.mkdir(parents=True)
    (bad / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: placeholder\n---\n\nplaceholder\n",
        encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "PRODUCTION_SKILL_IN_ROOT" in codes, codes


def test_discovery_fixture_is_untouched():
    """The M1 fixture must survive this slice unrenamed and unmodified."""
    fixture = SKILLS / "m1-discovery-fixture"
    assert fixture.is_dir()
    assert _frontmatter(fixture / "SKILL.md")["name"] == "m1-discovery-fixture"


# ------------------------------------------------- 12/14. OpenAI metadata

def test_openai_policy_parses_and_grants_nothing():
    """12/14. Documented invocation field only -- no tools, connectors or network."""
    policy = yaml.safe_load((PLAN_WORK / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert isinstance(policy, dict)
    assert set(policy) == {"policy"}, f"unexpected top-level keys: {sorted(policy)}"
    assert set(policy["policy"]) == {"allow_implicit_invocation"}, (
        f"unexpected policy keys: {sorted(policy['policy'])}")
    # Read-only, so implicit selection is affordable -- it costs a document, not a change.
    assert policy["policy"]["allow_implicit_invocation"] is True


def test_permission_grants_in_the_policy_file_are_rejected(plugin_tree):
    """14. The invocation file must not become a permission grant."""
    import validate_skills

    path = plugin_tree / "skills" / "plan-work" / "agents" / "openai.yaml"
    path.write_text("policy:\n  allow_implicit_invocation: true\n  tools:\n    - Bash\n",
                    encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "POLICY_GRANT_NOT_PERMITTED" in codes, codes


# ------------------------------------------------- 15. output template contract

@pytest.mark.parametrize("section", [
    "Plan metadata", "Objective", "Current context", "Assumptions", "Scope",
    "Non-goals", "Constraints", "Work breakdown", "Dependency order",
    "Parallelization opportunities", "Acceptance criteria", "Verification plan",
    "Risks and mitigations", "Blockers and decisions needed",
    "Rollback or recovery", "Recommended next action",
])
def test_template_declares_every_required_section(section):
    text = (PLAN_WORK / "references" / "plan-template.md").read_text(encoding="utf-8")
    assert section in text, f"plan template omits the {section!r} section"


@pytest.mark.parametrize("token", ["T-01", "AC-01", "V-01", "R-01", "Not Run"])
def test_template_declares_the_id_and_status_conventions(token):
    text = (PLAN_WORK / "references" / "plan-template.md").read_text(encoding="utf-8")
    assert token in text, f"plan template omits {token!r}"


def test_checklist_covers_the_completion_checks():
    text = (PLAN_WORK / "references" / "quality-checklist.md").read_text(encoding="utf-8").lower()
    for phrase in ["completion condition", "non-goal", "assumption", "cycle",
                   "parallel", "testable", "not run", "mitigation", "blocker"]:
        assert phrase in text, f"quality checklist omits {phrase!r}"


def test_no_reference_contains_a_shell_fence():
    """A reference is read, not run: no copyable shell block in either file."""
    import validate_skills

    for rel in ["references/plan-template.md", "references/quality-checklist.md"]:
        text = (PLAN_WORK / rel).read_text(encoding="utf-8")
        for fence in validate_skills.SHELL_FENCES:
            assert fence not in text, f"{rel} contains an executable {fence!r} block"
