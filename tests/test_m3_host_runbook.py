"""M3 slice 4 — the host runbook and the Q-IMPL-007 probe fixture.

Neither artifact can be tested by running it; that is the point of both. What can be
tested is that they remain capable of answering the question they were built for.

The probe is the fragile one. Its whole value rests on a single property — that a
declining agent and a blocked agent produce *different* observations — and that property
is destroyed by an edit that looks like a simplification.
"""

from __future__ import annotations

import pathlib
import sys

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_agents  # noqa: E402
from _common import (  # noqa: E402
    PLUGIN_AGENT_ROLES,
    PLUGIN_ROOT,
    ROLE_WRITE_TOOLS,
    split_frontmatter,
)

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "host-tests" / "agent-tool-enforcement"
PROBE = FIXTURE / "agents" / "m3-readonly-probe.md"
EXPECT = FIXTURE / "EXPECT.md"
RUNBOOK = REPO_ROOT / "docs" / "m3-host-runbook.md"


def _flat(path: pathlib.Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


# ------------------------------------------------- 1-4. the fixture never ships

def test_the_fixture_is_outside_the_installable_root():
    """A probe in the product is a product surface, whatever its filename says."""
    assert not FIXTURE.is_relative_to(PLUGIN_ROOT)


def test_the_probe_role_is_not_a_product_role():
    front, _ = split_frontmatter(PROBE.read_text(encoding="utf-8"))
    assert yaml.safe_load(front)["name"] not in PLUGIN_AGENT_ROLES


def test_the_product_validator_ignores_the_fixture():
    """`validate_agents` scans the installable root only, and must keep doing so."""
    assert validate_agents.check() == 0
    assert sorted(p.stem for p in (PLUGIN_ROOT / "agents").glob("*.md")) == \
        sorted(PLUGIN_AGENT_ROLES)


def test_the_fixture_says_it_is_a_fixture():
    for path in [PROBE, FIXTURE / "skills" / "m3-write-attempt-fixture" / "SKILL.md"]:
        assert "test fixture" in _flat(path)


# --------------------------------------- 5-8. the probe can still answer anything

def test_the_probe_holds_no_write_tool():
    """If it did, the experiment measures nothing — the write would prove only that."""
    front, _ = split_frontmatter(PROBE.read_text(encoding="utf-8"))
    granted = [t.strip() for t in yaml.safe_load(front)["tools"].split(",")]
    for tool in ROLE_WRITE_TOOLS + ["Bash"]:
        assert tool not in granted


def test_the_probe_instructs_the_attempt():
    """The property everything else rests on.

    Without an explicit instruction to try, a well-behaved model declines on its own
    read-only wording — and a declining agent and a blocked agent then leave the same
    evidence. The naive form of this test cannot distinguish the two things it exists to
    distinguish.
    """
    flat = _flat(PROBE)
    assert "attempt to write" in flat
    assert "you are authorized to attempt it" in flat


@pytest.mark.parametrize("outcome", [
    "no write tool was available to me",
    "i wrote the file",
])
def test_the_probe_defines_its_reportable_outcomes(outcome):
    assert outcome in _flat(PROBE)


def test_inconclusive_is_a_permitted_answer():
    """A probe with only two outcomes forces a wrong one when reality is a third."""
    assert "inconclusive" in _flat(EXPECT)


# ------------------------------------------- 9-11. the fixture stays bounded

def test_the_write_target_is_inside_the_fixture():
    flat = _flat(PROBE)
    assert ".probe-output/attempted-write.txt" in flat
    assert "do not write anywhere else" in flat


def test_the_probe_may_not_delegate_or_execute():
    flat = _flat(PROBE)
    assert "do not run a command" in flat
    assert "do not delegate" in flat


def test_no_probe_output_is_committed():
    """The fixture writes during a run. Nothing it writes belongs in the repository."""
    assert not (FIXTURE / ".probe-output").exists()


# ------------------------------------------------- 12-16. the runbook covers M3

@pytest.mark.parametrize("ats", ["ATS-001", "ATS-003", "ATS-004", "ATS-005"])
def test_every_m3_exit_test_has_a_step(ats):
    assert ats.lower() in _flat(RUNBOOK)


def test_the_q_impl_007_probe_has_a_step():
    flat = _flat(RUNBOOK)
    assert "rb-m3-05" in flat
    assert "q-impl-007" in flat


def test_the_already_observed_counts_are_derived():
    """RB-M3-00 records what was run non-interactively; the numbers come from the tree."""
    text = RUNBOOK.read_text(encoding="utf-8")
    assert f"**{len(PLUGIN_AGENT_ROLES)}** — coordinator" in text
    assert f"**{len(list((PLUGIN_ROOT / 'skills').iterdir()))}** — the 7 production" in text


def test_the_ats_005_artifact_gap_is_stated():
    """ATS-005 verifies against `evidence.md`, which no Skill in this milestone writes.

    That is dry-run finding D-01 resurfacing at the acceptance-test level. A runbook that
    let someone tick the row from a response would bury a milestone dependency under a
    green checkmark.
    """
    flat = _flat(RUNBOOK)
    assert "no m2 or m3 skill writes `evidence.md`" in flat
    assert "cannot be closed as literally written" in flat


def test_the_runbook_refuses_to_soften_a_negative_result():
    flat = _flat(RUNBOOK)
    assert "a negative result is a valid outcome. an unrecorded result is not." in flat
    assert "do not soften a *not enforced* result" in flat
