"""M4 slice 4 — the Codex host runbook and the Q-IMPL status record.

The runbook cannot be tested by running it. What can be tested is that it keeps stating
the two things a reader would otherwise get wrong.

The first is that three of ATS-019's five scenarios are **not testable as written**,
because they describe a Skill that offers template installation and no such Skill can
exist while Q-IMPL-003 is open. A runbook that let someone tick those rows would record a
verified approval flow where there is no flow.

The second is that M4's exit asks for *documented answers*, not resolved questions — and
that the three remaining questions are open in different ways, only one of which costs
anything.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _common import PLUGIN_AGENT_ROLES, PLUGIN_ROOT  # noqa: E402

RUNBOOK = REPO_ROOT / "docs" / "m4-host-runbook.md"
M3_RUNBOOK = REPO_ROOT / "docs" / "m3-host-runbook.md"
COMPAT = REPO_ROOT / "docs" / "compatibility.md"


def _flat(path: pathlib.Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


# --------------------------------------------------- 1-4. the runbook covers M4's exit

@pytest.mark.parametrize("criterion", ["ATS-002", "ATS-019", "MET-003", "Q-IMPL-002",
                                       "Q-IMPL-003", "Q-IMPL-004"])
def test_every_m4_exit_criterion_has_a_step(criterion):
    assert criterion.lower() in _flat(RUNBOOK)


def test_gate_a_recognition_has_its_own_step():
    """Exit criterion 5. Codex is the host that has one, so it is testable here."""
    flat = _flat(RUNBOOK)
    assert "gate a on this host" in flat
    assert "rb-m4-05" in flat


def test_gate_a_is_kept_distinct_from_gate_b():
    """Gate B has to hold on a host with no Gate A, which is Claude Code today. A step
    that let one stand in for the other would erase the reason Gate B exists."""
    flat = _flat(RUNBOOK)
    assert "gate a is not gate b" in flat
    assert "claude code has no gate a at all" in flat


def test_the_gate_a_step_checks_that_explicit_invocation_still_works():
    """A policy blocking both implicit and explicit selection passes the first check
    while having broken the Skill."""
    flat = _flat(RUNBOOK)
    assert "explicit `$apply-refinement` still works" in flat
    assert "both rows matter equally" in flat


# ------------------------------------- 5-9. the untestable half of ATS-019 stays visible

def test_the_untestable_scenarios_are_named():
    flat = _flat(RUNBOOK)
    assert "not testable as written" in flat
    assert "no such skill exists, and none can be built yet" in flat


def test_the_reason_is_q_impl_003_and_says_so():
    flat = _flat(RUNBOOK)
    assert "q-impl-003" in flat
    assert "d-04" in flat, "the same blocker already produced a dry-run finding"


def test_the_runbook_forbids_marking_them_passed():
    """A pass would claim an approval flow was verified when there is no flow."""
    flat = _flat(RUNBOOK)
    assert "do not mark them passed" in flat
    assert "not applicable — no offering skill exists" in flat


def test_the_replacement_route_is_mapped_rule_by_rule():
    """The manual procedure meets the same FR-021 rules; the mapping is what makes that
    checkable rather than asserted."""
    flat = _flat(RUNBOOK)
    for phrase in ["approval before installation", "project scope default",
                   "validate before copying", "never silently", "documented removal"]:
        assert phrase in flat


def test_it_names_the_precedent_in_the_m3_runbook():
    """ATS-005 has the same shape: an acceptance test whose subject was deferred. Both
    are recorded rather than quietly satisfied."""
    assert "ats-005" in _flat(RUNBOOK)
    assert "cannot be closed as literally written" in _flat(M3_RUNBOOK)


# ------------------------------------------ 10-13. no free step, and it says why

def test_the_absence_of_a_non_interactive_step_is_explained():
    """M3's runbook opens with a pre-filled step because `plugin details` cost nothing.
    Codex has no equivalent, and the difference is stated rather than left as a gap."""
    flat = _flat(RUNBOOK)
    assert "there is no free non-interactive step here" in flat
    # Matched without the preceding "Codex has no": the sentence wraps inside a
    # blockquote, so a `>` lands mid-phrase once whitespace is collapsed.
    assert "equivalent read-only inventory command" in flat


def test_the_before_state_is_captured_before():
    """ATS-019 is verified by comparing directory listings across steps."""
    flat = _flat(RUNBOOK)
    assert "record both agent directories **before you start**" in flat
    assert "a list captured afterwards is not a before" in flat


def test_the_zero_template_baseline_is_called_out():
    """FR-021's premise. If the workflow needs a template, the optional assets have
    become mandatory and the design is wrong."""
    flat = _flat(RUNBOOK)
    assert "baseline, not a degraded mode" in flat


def test_doctor_must_report_info_not_ok():
    flat = _flat(RUNBOOK)
    assert "reports it as **`info`**, not `ok`" in flat


# -------------------------------------------- 14-18. the Q-IMPL record is honest

@pytest.mark.parametrize("qid", ["Q-IMPL-002", "Q-IMPL-003", "Q-IMPL-004"])
def test_compatibility_records_each_question_after_m4(qid):
    assert qid.lower() in _flat(COMPAT)


def test_documented_answers_are_distinguished_from_resolved_questions():
    flat = _flat(COMPAT)
    assert "documented answers**, not resolved questions" in flat


def test_q_impl_002_is_open_because_nothing_depends_on_it():
    """The canonical minimum set was chosen *because* the answer was unknown, so the
    design is correct either way. Answering it would permit a widening, not a fix."""
    flat = _flat(COMPAT)
    assert "a widening, not a fix" in flat


def test_q_impl_003_lists_what_it_has_already_decided():
    """Three consequences, each recorded where it bites."""
    flat = _flat(COMPAT)
    assert "designed around three times" in flat
    assert "copied by hand rather than by a skill" in flat


def test_the_two_kinds_of_open_question_are_distinguished():
    """The reusable idea: a question the design does not rely on is free to leave open;
    one the design routes around bills you every time it does."""
    flat = _flat(COMPAT)
    assert "can stay open indefinitely without cost" in flat
    assert "q-impl-003 is the second kind" in flat


# --------------------------------------------------- 19-20. parity is measurable

def test_parity_compares_roles_as_well_as_skills():
    flat = _flat(RUNBOOK)
    assert "same 6 roles" in flat or f"same {len(PLUGIN_AGENT_ROLES)} roles" in flat


def test_parity_excludes_invocation_syntax_deliberately():
    """Invocation differs by host and always will. Anything else differing is drift."""
    flat = _flat(RUNBOOK)
    assert "anything else differing is drift" in flat
    assert (PLUGIN_ROOT / "adapters" / "codex" / "agent-templates").is_dir()
