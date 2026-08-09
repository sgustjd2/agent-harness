"""M3 slice 3 — the final Claude manifest, catalog and installation guide.

Packaging metadata is the one part of this repository a user reads *before* deciding to
trust it. Two failure modes are worth pinning:

  1. a placeholder that shipped — `OWNER` in a homepage URL is a 404 on a link the host
     puts in front of people
  2. a description or an instruction that describes an earlier version of the product

Both are invisible to every other check, because a manifest with a wrong description is
still a valid manifest.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _common import (  # noqa: E402
    DISCOVERY_FIXTURE_SKILL,
    IMPLEMENTED_PRODUCTION_SKILLS,
    PLUGIN_AGENT_ROLES,
    skill_dirs,
)

PLUGIN = REPO_ROOT / "plugins" / "agent-harness"
CLAUDE_MANIFEST = PLUGIN / ".claude-plugin" / "plugin.json"
CODEX_MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"
CATALOG = REPO_ROOT / ".claude-plugin" / "marketplace.json"
SOURCE = REPO_ROOT / "marketplace" / "marketplace.source.json"
GUIDE = REPO_ROOT / "docs" / "install-claude-code.md"
BLOCK_FILE = PLUGIN / "adapters" / "claude" / "claude-md-block.md"

REPO_URL = "https://github.com/sgustjd2/agent-harness"

MANIFESTS = [CLAUDE_MANIFEST, CODEX_MANIFEST]


def _json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _flat(path: pathlib.Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


# ------------------------------------------------------ 1-5. no shipped placeholders

@pytest.mark.parametrize("path", MANIFESTS + [CATALOG, SOURCE, GUIDE])
def test_no_owner_placeholder_survives(path):
    """`OWNER` is a URL the host renders as a link. It has to go somewhere real."""
    assert "github.com/OWNER" not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("path", MANIFESTS)
def test_manifest_urls_point_at_the_repository(path):
    manifest = _json(path)
    assert manifest["homepage"] == REPO_URL
    assert manifest["repository"] == REPO_URL


@pytest.mark.parametrize("path", MANIFESTS)
def test_no_manifest_still_calls_the_skills_placeholders(path):
    """The description shipped by M1 said the Skills were placeholders. M2 ended that.

    Same defect class as dry-run D-06: finishing the work made the documentation false,
    and a valid manifest stays valid while saying the wrong thing.
    """
    flat = _flat(path)
    for stale in ["m1 scaffold", "skills are placeholders", "placeholder"]:
        assert stale not in flat


@pytest.mark.parametrize("path", MANIFESTS)
def test_the_description_still_says_experimental(path):
    """Three M1 exit criteria are unmet and the pilot has not run. Say so."""
    assert "experimental" in _flat(path)


def test_the_guide_is_no_longer_a_draft():
    flat = _flat(GUIDE)
    for stale in ["m1 placeholder", "written in m3", "still a draft"]:
        assert stale not in flat


# ---------------------------------------------------- 6-9. the guide stays truthful

def test_the_guide_leads_with_what_was_actually_run():
    """The status table is the point of the page, not an appendix.

    Marketplace installation is documented and unexercised. A guide that presents it in
    the same voice as the step someone verified is claiming evidence it does not have.
    """
    flat = _flat(GUIDE)
    assert "documented, not exercised" in flat
    assert "ats-001" in flat


def test_the_verified_path_is_identified_as_such():
    """`--plugin-dir` session loading is the one thing M1.4A actually observed."""
    flat = _flat(GUIDE)
    assert "--plugin-dir" in flat
    assert "**observed**" in flat


def test_the_guide_does_not_claim_a_release():
    flat = _flat(GUIDE)
    assert "there is no published release yet" in flat


def test_the_guide_says_installation_touches_no_project_file():
    """ATS-001's fourth condition, and the one a reader can check in one command."""
    flat = _flat(GUIDE)
    assert "git status" in flat
    assert "byte-identical" in flat


# ------------------------------------------- 10-13. counts derived, never hand-typed

def test_the_expected_skill_count_matches_the_tree():
    """Eight, not seven: the fixture is discoverable too, and a reader will see it."""
    assert f"**Skills {len(skill_dirs())}**" in GUIDE.read_text(encoding="utf-8")


def test_the_expected_agent_count_matches_the_role_list():
    assert f"**Agents {len(PLUGIN_AGENT_ROLES)}**" in GUIDE.read_text(encoding="utf-8")


@pytest.mark.parametrize("skill", IMPLEMENTED_PRODUCTION_SKILLS)
def test_the_guide_lists_every_invocable_skill(skill):
    assert f"/agent-harness:{skill}" in GUIDE.read_text(encoding="utf-8")


def test_the_guide_does_not_offer_the_fixture_as_a_command():
    """It is discoverable, which is why the guide explains it — not invocable."""
    assert f"/agent-harness:{DISCOVERY_FIXTURE_SKILL}" not in GUIDE.read_text(encoding="utf-8")


# ---------------------------------------------- 14. the two user-facing lists agree

def test_the_guide_and_the_marker_block_list_the_same_skills():
    """Two places tell a user which Skills exist. They disagree exactly once: silently.

    The `CLAUDE.md` block lands in the user's repository and the guide is read before
    that. Divergence would mean one of them is wrong for as long as nobody notices.
    """
    pattern = re.compile(r"/agent-harness:([a-z-]+)")
    in_guide = set(pattern.findall(GUIDE.read_text(encoding="utf-8")))
    in_block = set(pattern.findall(BLOCK_FILE.read_text(encoding="utf-8")))
    assert in_guide == in_block == set(IMPLEMENTED_PRODUCTION_SKILLS)


# ------------------------------------------------------- 15-16. manifest structure

def test_both_manifests_carry_the_same_keywords():
    assert _json(CLAUDE_MANIFEST)["keywords"] == _json(CODEX_MANIFEST)["keywords"]


def test_the_catalog_is_still_generated_not_hand_edited():
    """Candidate C. Editing the generated catalog directly is how the two drift.

    Compares the rendered output against what is on disk, rather than shelling out --
    the deterministic run belongs to `generate_marketplaces --check` in the validator
    inventory, and duplicating it here would run it twice for one result.
    """
    import generate_marketplaces

    rendered = generate_marketplaces.render(_json(SOURCE))
    for relative, text in rendered.items():
        assert (REPO_ROOT / relative).read_text(encoding="utf-8") == text, relative
