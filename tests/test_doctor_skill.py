"""Contract tests for the doctor Skill (M2 slice 4).

doctor diagnoses the harness; verify-work verifies project code. These tests concentrate
on that boundary and on the diagnostic model — the four statuses, the overall calculation,
and the rule that a diagnostic never repairs and never executes.

Generic Skill hygiene is already covered by the shared validator and the earlier slices.
No test here runs a diagnostic; they assert the static contract and the matrix.
"""

from __future__ import annotations

import pytest
import yaml

from conftest import REPO_ROOT
from _common import FORBIDDEN_PRODUCTION_SKILLS
from test_plan_work_skill import _frontmatter, _run

pytestmark = pytest.mark.deterministic

SKILLS = REPO_ROOT / "plugins" / "agent-harness" / "skills"
DOCTOR = SKILLS / "doctor"
SKILL_MD = DOCTOR / "SKILL.md"
MATRIX = DOCTOR / "references" / "diagnostic-matrix.md"
GUIDE = DOCTOR / "references" / "remediation-guide.md"


def _declared() -> dict:
    from _common import extract_policy_marker

    return yaml.safe_load(extract_policy_marker(SKILL_MD.read_text(encoding="utf-8")))


def _flat(path) -> str:
    """Lowercased, whitespace-collapsed text: line wrapping is formatting, not content."""
    return " ".join(path.read_text(encoding="utf-8").lower().split())


# ---------------------------------------------------------------- 1-5. structure

def test_doctor_validates_as_shipped():
    """1. The whole plugin, including doctor, passes the real validator."""
    import validate_skills

    status, codes = _run(validate_skills.check, REPO_ROOT / "plugins" / "agent-harness")
    assert status == 0, f"validate_skills failed with {codes}"
    assert codes == [], codes


def test_frontmatter_is_exactly_name_and_description():
    """2."""
    front = _frontmatter(SKILL_MD)
    assert set(front) == {"name", "description"}, sorted(front)
    assert front["name"] == DOCTOR.name == "doctor"


@pytest.mark.parametrize("trigger", [
    "installation", "diagnose", "configuration", "memory", "health",
])
def test_description_covers_the_diagnostic_triggers(trigger):
    assert trigger in _frontmatter(SKILL_MD)["description"].lower()


def test_read_only_profile_is_reused_unchanged():
    """3/4. doctor takes the existing profile; no new profile, no widening."""
    from _common import (PROFILES_PERMITTING_EXECUTION, SKILL_PROFILE,
                         SKILL_SAFETY_PROFILES)

    assert SKILL_PROFILE["doctor"] == "read-only"
    # The exact profile roster belongs to the newest slice's test file; what matters
    # here is that doctor's own profile still forbids execution.
    assert "read-only" not in PROFILES_PERMITTING_EXECUTION
    assert SKILL_SAFETY_PROFILES["read-only"]["executes_commands"] is False


@pytest.mark.parametrize("key,expected", [
    ("read_only", True),
    ("executes_commands", False),      # 4
    ("modifies_source", False),
    ("modifies_config", False),
    ("spawns_agents", False),
    ("network_access", False),
    ("verification_default", "Not Run"),
    ("persistence", "on-request-only"),
])
def test_declared_contract(key, expected):
    assert _declared()[key] == expected


def test_doctor_has_no_write_surface():
    """5. The shared profile's persistence field grants no write permission."""
    from _common import ALLOWED_WRITE_PATH_ROOTS, PROFILES_REQUIRING_PATH_ROOTS

    assert "doctor" not in ALLOWED_WRITE_PATH_ROOTS
    assert "read-only" not in PROFILES_REQUIRING_PATH_ROOTS
    assert "allowed_path_roots" not in _declared()
    # This slice persists nothing at all, doctor.md included.
    body = _flat(SKILL_MD)
    assert "this milestone persists nothing at all" in body
    assert "doctor.md" in body  # named explicitly as not created


# ------------------------------------------------- 6-10. the diagnostic model

@pytest.mark.parametrize("status,definition", [
    ("ok", "| `ok` | the observed state satisfies the expected contract |"),
    ("warn", "| `warn` | usable, but risky, degraded, near a limit, or off the "
             "recommended policy |"),
    ("fail", "| `fail` | a required harness condition is observably broken |"),
    ("unknown", "| `unknown` | the state cannot be determined safely with read-only "
                "capability |"),
])
def test_four_statuses_are_defined(status, definition):
    """6. Exactly four, each with its meaning."""
    assert definition in _flat(SKILL_MD), f"SKILL.md does not define {status!r}"


@pytest.mark.parametrize("overall,rule", [
    # 7 broken
    ("broken", "| `broken` | one or more `fail` |"),
    # 8 degraded
    ("degraded", "| `degraded` | zero `fail`, one or more `warn` |"),
    # 9 unknown
    ("unknown", "| `unknown` | zero `fail`, zero `warn`, one or more `unknown` |"),
    # 10 healthy
    ("healthy", "| `healthy` | every applicable required check is `ok`, with no `warn`, "
                "`fail` or `unknown` |"),
])
def test_overall_calculation(overall, rule):
    assert rule in _flat(SKILL_MD), f"SKILL.md omits the {overall!r} rule"


@pytest.mark.parametrize("rule", [
    "never turn `unknown` into `fail`",
    "never turn `warn` into `fail`",
    "never hide an `unknown` to reach `healthy`",
    "`doctor` never stops",
])
def test_status_integrity_rules(rule):
    """The rules that stop a diagnostic from flattering itself."""
    assert rule in _flat(SKILL_MD), f"SKILL.md omits: {rule!r}"


# ------------------------------------------- 11-14. state and config diagnostics

def test_missing_agent_harness_is_fail_with_init_project_remediation():
    """11."""
    body = _flat(SKILL_MD)
    assert "if `.agent-harness/` does not exist: `fail`**, with the remediation " \
           "\"run `init-project`\"" in body
    assert "do not create it" in body
    assert "**absent — run `init-project`**" in _flat(MATRIX)


@pytest.mark.parametrize("rule", [
    "never repair.** do not regenerate config, do not delete corrupt memory",
    "a corrupt file is a finding, not permission to fix it",
])
def test_malformed_state_is_never_auto_repaired(rule):
    """12."""
    assert rule in _flat(SKILL_MD), f"SKILL.md omits: {rule!r}"


def test_unsupported_schema_version_is_fail_and_never_auto_migrated():
    """13."""
    body = _flat(SKILL_MD)
    assert "| valid but unsupported version, migration needed | `fail` |" in body
    assert "| config cannot be parsed | `fail` |" in body
    assert "**never auto-migrate.**" in body
    assert "the current supported `schema_version` is **1**" in body


def test_memory_files_are_diagnosed_independently():
    """14. Three IDs, so one corrupt file does not hide the other two."""
    matrix = _flat(MATRIX)
    for mem_id, filename in [("mem-01", "facts.md"), ("mem-02", "decisions.md"),
                             ("mem-03", "patterns.md")]:
        assert f"| {mem_id} | `{filename}` integrity" in matrix
    body = _flat(SKILL_MD)
    assert "one corrupt file must not make the other two unreadable" in body
    assert "do not rewrite entries, do not merge duplicates, do not prune" in body


# --------------------------------------- 15-17. the execution boundary

@pytest.mark.parametrize("forbidden", [
    "--version", "command -v", "which", "where", "get-command",
])
def test_executable_check_forbids_every_process_spawning_lookup(forbidden):
    """15. The boundary that keeps `executes_commands: false` true."""
    assert forbidden in _flat(SKILL_MD), f"SKILL.md does not forbid {forbidden!r}"


def test_undeterminable_executable_is_unknown_not_fail():
    """16."""
    body = _flat(SKILL_MD)
    assert "**`unknown`**, stating that availability could not be established without " \
           "executing a lookup" in body
    assert "an `unknown` executable is never a `fail`" in body


def test_doctor_never_executes_a_verification_gate():
    """17. The doctor / verify-work boundary, stated in both directions."""
    body = _flat(SKILL_MD)
    assert "it must **never run it**" in body
    assert "running the gate, running a \"harmless subset\" of the gate" in body
    assert "`doctor` diagnoses the harness. `verify-work` verifies your code.**" in body
    assert "and only that; `doctor` never runs a gate" in _flat(GUIDE)


def test_no_bundled_helper_or_executable_directory():
    """21. Q-IMPL-003 is unresolved, so nothing executable ships."""
    import validate_skills

    for sub in ("scripts", "assets", "bin"):
        assert not (DOCTOR / sub).exists(), f"{sub}/ must not exist inside doctor"
    for manifest in validate_skills.DEPENDENCY_MANIFESTS:
        assert not (DOCTOR / manifest).exists()
    body = _flat(SKILL_MD)
    assert "report `ok` — \"no helper required by the current implemented skill set\"" in body
    assert "do not claim the question is settled" in body


# ------------------------------------- 18-20, 22. findings and informational checks

def test_malformed_managed_marker_is_fail():
    """18."""
    body = _flat(SKILL_MD)
    assert "| unmatched, duplicated, or nested markers | **`fail`** — ownership is " \
           "ambiguous |" in body
    assert "**never repair either file.**" in body


@pytest.mark.parametrize("check,expectation", [
    # 19 optional custom agents absent is not a failure
    ("cmp-03", "present and readable, or absent"),
    # Agent Teams is not a dependency
    ("cmp-02", "informational"),
    # 21 helper absence in this milestone is ok
    ("cmp-05", "**`ok` — no helper required by the current skill set**"),
])
def test_optional_checks_never_fail(check, expectation):
    """19/21. Optional and informational checks have no fail column entry."""
    matrix = _flat(MATRIX)
    row = next(line for line in matrix.split("|") if check in line)
    assert row, f"matrix has no {check} row"
    assert expectation in matrix, f"{check} expectation missing"


def test_doctor_expects_all_seven_production_skills():
    """19. Was "unimplemented Skills may be absent" until every planned Skill shipped.

    The old assertion outlived its subject: doctor still told readers that three Skills
    were expected to be missing, which would have had it report a healthy installation as
    incomplete-by-design. Found by the M2 contract dry-run.
    """
    from _common import PLANNED_PRODUCTION_SKILLS

    body = _flat(SKILL_MD)
    assert "**all seven** production skills are present" in body
    for name in PLANNED_PRODUCTION_SKILLS:
        assert f"`{name}`" in body, f"doctor omits {name!r} from the expected set"
    assert "any one of them missing is a `fail`" in body
    # PKG-06 now guards the other direction: an unrecognised Skill directory.
    assert "| pkg-06 | no unexpected skill directory | always |" in _flat(MATRIX)


def test_commit_evidence_true_is_a_warn():
    """20."""
    body = _flat(SKILL_MD)
    assert "**`runs.commit_evidence: true` is a `warn`**" in body
    assert "do not change the value and do not edit `.gitignore`" in body
    assert "| cfg-05 | `runs.commit_evidence` | initialized | `false` | **`true`** |" \
        in _flat(MATRIX)


@pytest.mark.parametrize("field", [
    "finding id", "affected path or component", "expected state",
    "proposed remediation", "automatic_remediation", "argv array",
])
def test_every_fail_carries_remediation_guidance(field):
    """22."""
    assert field in _flat(SKILL_MD), f"SKILL.md omits the finding field {field!r}"


def test_remediation_is_never_executed_and_never_destructive():
    """22. The guide's own limits."""
    guide = _flat(GUIDE)
    assert "`doctor` never executes it" in guide
    assert "do not invent a command when manual inspection is the correct action" in guide
    assert "never suggest a destructive fix by default" in guide
    assert "never suggest modifying user scope" in guide


# ---------------------------------------------- 23-25. milestone and no regression

def test_milestone_allowlist_includes_doctor():
    """23. Derived from the constant; exact membership lives in the newest slice's file."""
    from _common import ALLOWED_SKILLS, IMPLEMENTED_PRODUCTION_SKILLS

    assert "doctor" in IMPLEMENTED_PRODUCTION_SKILLS
    assert {d.name for d in SKILLS.iterdir() if d.is_dir()} == set(ALLOWED_SKILLS)


# FORBIDDEN_PRODUCTION_SKILLS is empty now that all seven are implemented. An
# empty parametrize SKIPS silently, so the guard would stop running without
# anyone noticing -- fall back to a name that is not on the allowlist.
@pytest.mark.parametrize(
    "name", FORBIDDEN_PRODUCTION_SKILLS or ["not-a-planned-skill"])
def test_names_outside_the_allowlist_are_rejected(plugin_tree, name):
    """24. Every planned Skill is implemented now, so this exercises the same boundary
    with a name that is not on the allowlist."""
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


@pytest.mark.parametrize("skill,profile,executes", [
    ("plan-work", "read-only", False),
    ("init-project", "approval-gated-mutation", False),
    ("verify-work", "bounded-verification", True),
])
def test_existing_skills_keep_their_contracts(skill, profile, executes):
    """25. Adding doctor changed no other Skill's effective policy."""
    from _common import SKILL_PROFILE, SKILL_SAFETY_PROFILES, extract_policy_marker

    assert SKILL_PROFILE[skill] == profile
    assert SKILL_SAFETY_PROFILES[profile]["executes_commands"] is executes
    declared = yaml.safe_load(
        extract_policy_marker((SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")))
    assert declared["executes_commands"] is executes


def test_implicit_invocation_is_enabled_for_a_read_only_diagnostic():
    """doctor writes nothing and runs nothing, so it may be reached implicitly."""
    from _common import IMPLICIT_INVOCATION_MUST_BE_OFF

    assert "doctor" not in IMPLICIT_INVOCATION_MUST_BE_OFF
    policy = yaml.safe_load((DOCTOR / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    assert set(policy) == {"policy"}
    assert set(policy["policy"]) == {"allow_implicit_invocation"}
    assert policy["policy"]["allow_implicit_invocation"] is True


# ------------------------------------------------- D-03: not-applicable checks

@pytest.mark.parametrize("rule", [
    "a check whose **applies** condition in the diagnostic matrix is unmet is reported",
    "`not applicable` is **not a fifth status**",
    "**`not applicable` never affects the overall result**",
    "**do not report it as `unknown`.**",
    "**do not omit the section.**",
])
def test_not_applicable_is_defined(rule):
    """D-03. Four statuses, a fixed report, and an Applies column with nothing joining them.

    The first run anyone performs -- doctor on an uninitialized repo -- leaves three
    sections with nothing in scope and, before this, no vocabulary to say so.
    """
    assert rule in _flat(SKILL_MD), f"SKILL.md omits: {rule!r}"


def test_not_applicable_is_distinguished_from_unknown():
    """The two are opposites: one knows why it is out of scope, the other knows nothing."""
    body = _flat(SKILL_MD)
    assert "`unknown` means the state could not be determined; here it is known precisely" \
        in body
    assert "the `applies` column is load-bearing" in _flat(MATRIX)
