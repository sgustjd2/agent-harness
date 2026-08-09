"""M4 slice 3 — the Codex install guide, final catalog, and doctor's template reporting.

Two things are pinned here that no other test covers.

The guide is the only place a user is told to copy a file into `.codex/agents/` by hand.
If it drifts — wrong scope default, missing pre-copy check, no removal step — the failure
lands in their repository as an agent definition they did not review.

And `info` is a new reporting category in `doctor`, added one milestone after D-03 fixed
`not applicable` by insisting it was *not* a fifth status. The tests keep the two straight,
because "we added a fifth status after saying we would not" is exactly how a contract
erodes.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _common import IMPLEMENTED_PRODUCTION_SKILLS, PLUGIN_AGENT_ROLES  # noqa: E402

PLUGIN = REPO_ROOT / "plugins" / "agent-harness"
GUIDE = REPO_ROOT / "docs" / "install-codex.md"
CATALOG = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"
DOCTOR = PLUGIN / "skills" / "doctor" / "SKILL.md"
MATRIX = PLUGIN / "skills" / "doctor" / "references" / "diagnostic-matrix.md"
CODEX_BLOCK = PLUGIN / "adapters" / "codex" / "agents-md-block.md"


def _flat(path: pathlib.Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


# --------------------------------------------------------- 1-5. the guide is honest

def test_the_guide_is_no_longer_a_draft():
    flat = _flat(GUIDE)
    for stale in ["m1 placeholder", "written in m4", "still a draft"]:
        assert stale not in flat


def test_the_guide_leads_with_what_was_actually_run():
    flat = _flat(GUIDE)
    assert "documented, not exercised" in flat
    assert "0.146.0-alpha.9.2" in flat


def test_registration_and_installation_stay_separate():
    """The one thing a real host confirmed empirically, and the thing users conflate."""
    flat = _flat(GUIDE)
    assert "registering a marketplace is not installing a plugin" in flat
    assert "nothing is installed, nothing is enabled" in flat


def test_the_guide_prints_no_cli_install_command():
    """FR-028. One existed on an alpha; it is not the documented stable path, so it is
    not printed as a step someone can copy."""
    assert "no cli installation command is documented" in _flat(GUIDE)


def test_skill_discovery_is_flagged_as_untested_in_the_guide():
    """E6. A reader whose `$doctor` does not resolve should recognise the open question
    rather than assume they made a mistake."""
    flat = _flat(GUIDE)
    assert "e6" in flat
    assert "not a mistake you made" in flat


# ------------------------------------------------ 6-9. the guide lists what exists

@pytest.mark.parametrize("skill", IMPLEMENTED_PRODUCTION_SKILLS)
def test_the_guide_uses_the_codex_invocation_prefix(skill):
    assert f"`${skill}`" in GUIDE.read_text(encoding="utf-8")


def test_the_guide_and_the_codex_block_list_the_same_skills():
    """Compared against the block itself, not the file around it.

    The file's prose discusses `$name` as a form; only the delimited block is the artifact
    a user ends up with, and that is what has to agree with the guide.
    """
    pattern = re.compile(r"`\$([a-z-]+)`")
    block = re.search(r"<!-- BEGIN agent-harness -->.*?<!-- END agent-harness -->",
                      CODEX_BLOCK.read_text(encoding="utf-8"), re.S).group(0)
    in_guide = set(pattern.findall(GUIDE.read_text(encoding="utf-8")))
    in_block = set(pattern.findall(block))
    assert in_guide == in_block == set(IMPLEMENTED_PRODUCTION_SKILLS)


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_the_guide_names_every_role_template(role):
    assert role in _flat(GUIDE)


def test_the_fallback_path_keeps_gate_a():
    """Copying `skills/` into `.agents/skills/` costs the plugin lifecycle but not the
    invocation gate, because the policy file travels inside each Skill directory."""
    flat = _flat(GUIDE)
    assert ".agents/skills/" in flat
    assert "keeps gate a" in flat


# --------------------------------------------- 10-14. the manual copy is safe to follow

def test_project_scope_is_the_documented_default():
    """FR-021 rule 4 / SEC-17. The whole mitigation rests on the copy being visible in a
    diff, which user scope would defeat."""
    flat = _flat(GUIDE)
    assert "project scope, not user scope" in flat
    assert "show up in no diff" in flat


def test_the_guide_says_no_skill_can_install_a_template():
    flat = _flat(GUIDE)
    assert "nothing installs them" in flat
    assert "forbidden write roots" in flat


def test_the_guide_has_a_pre_copy_check():
    """FR-021 rule 5. The build-time validator runs where the file was written, not where
    it came from, so a fork's template needs the reader's own eyes."""
    flat = _flat(GUIDE)
    assert "before you copy" in flat
    assert "obtained it from a fork" in flat


def test_the_guide_documents_removal():
    """FR-021 rule 7 and ATS-019 scenario (e)."""
    flat = _flat(GUIDE)
    assert "removing them" in flat
    assert "the file is the installation" in flat


def test_uninstalling_does_not_delete_user_state():
    flat = _flat(GUIDE)
    assert "uninstalling a tool is not a request to delete the work done with it" in flat


# ------------------------------------------- 15-19. `info` is not a fifth status

def test_info_is_defined_as_a_non_judgement():
    flat = _flat(DOCTOR)
    assert "observations that are not judgements" in flat
    assert "judging it is not this skill's call" in flat


def test_info_never_affects_the_overall_result():
    assert "**`info` never affects the overall result**" in DOCTOR.read_text(encoding="utf-8")


def test_the_four_statuses_did_not_become_five():
    """D-03 established that the four statuses each describe an outcome of judging.

    `info` and `not applicable` are both excluded from that set for the same reason, and
    the status table must still list exactly four rows.
    """
    text = DOCTOR.read_text(encoding="utf-8")
    section = text.split("## Statuses", 1)[1].split("###", 1)[0]
    rows = [line for line in section.splitlines()
            if line.startswith("| `") and "Status" not in line]
    assert len(rows) == 4
    assert "| `info`" not in text


def test_info_is_not_collapsed_into_ok():
    """`ok` reads as endorsement, and nothing was endorsed."""
    flat = _flat(DOCTOR)
    assert "do not report an `info` observation as `ok`" in flat


def test_the_summary_lists_both_non_outcomes_separately():
    flat = _flat(DOCTOR)
    assert "lists `not applicable` and `info` separately — neither is an outcome" in flat


# ------------------------------------------ 20-23. doctor reports, and stays in scope

def test_doctor_reports_the_templates_as_info():
    flat = _flat(DOCTOR)
    assert "host agent templates" in flat
    assert "report, never judge" in flat


def test_doctor_never_reads_user_scope():
    """SEC-17. Reading `~/.codex/agents/` would inspect state the project does not own."""
    flat = _flat(DOCTOR)
    assert "never look in `~/.codex/agents/`" in flat
    assert "nothing here reads there" in flat


def test_the_matrix_row_has_no_verdict_columns():
    """The absence of ok/warn/fail columns on TPL-01 is the contract, not an omission."""
    flat = _flat(MATRIX)
    assert "tpl-01" in flat
    assert "this table has no `ok`/`warn`/`fail` columns, and that is the point" in flat


def test_the_user_scope_row_is_explicitly_never_checked():
    assert "**never checked**" in MATRIX.read_text(encoding="utf-8")


# ------------------------------------------------------ 24-26. catalog and manifest

def test_the_codex_catalog_carries_no_placeholder():
    assert "github.com/OWNER" not in CATALOG.read_text(encoding="utf-8")


def test_the_codex_manifest_is_the_documented_minimum_plus_metadata():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for required in ["name", "version", "description", "skills"]:
        assert required in manifest
    assert manifest["skills"] == "./skills/"


def test_the_catalog_source_is_the_object_form():
    """DEC-P14 Candidate C generates the object form deliberately; it is a local
    architecture choice, and the plain-string form is equally documented."""
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    source = catalog["plugins"][0]["source"]
    assert isinstance(source, dict)
    assert source["path"] == "./plugins/agent-harness"
