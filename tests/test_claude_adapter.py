"""M3 slice 2 — the Claude Code adapter layer.

The adapter's job is to hold what is true about the host so the canonical Skill layer
does not have to. Three failure modes are worth pinning:

  1. a file that still announces itself as a placeholder after it was written
  2. the block drifting out of step with the Skills it points at
  3. someone "fixing" a Skill to read one of these files, which cannot resolve

The third is not hypothetical. It was the proposed fix for dry-run finding D-04, and it
was wrong for a reason that has not changed: Q-IMPL-003 is still open.
"""

from __future__ import annotations

import pathlib
import re
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _common import IMPLEMENTED_PRODUCTION_SKILLS, PLUGIN_AGENT_ROLES  # noqa: E402

ADAPTER = REPO_ROOT / "plugins" / "agent-harness" / "adapters" / "claude"
BLOCK_FILE = ADAPTER / "claude-md-block.md"
NOTES = ADAPTER / "capability-notes.md"
README = ADAPTER / "README.md"

BLOCK_LIMIT_BYTES = 2048


def _text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(path: pathlib.Path) -> str:
    return " ".join(_text(path).lower().split())


def _block() -> str:
    found = re.search(r"<!-- BEGIN agent-harness -->.*?<!-- END agent-harness -->",
                      _text(BLOCK_FILE), re.S)
    assert found, "the adapter must carry a literal, delimited block"
    return found.group(0)


# ------------------------------------------------------- 1-3. no stale placeholders

@pytest.mark.parametrize("path", [README, NOTES, BLOCK_FILE])
def test_no_file_still_calls_itself_a_placeholder(path):
    """A document that says it is unwritten after being written is a live wrong claim.

    This is the D-06 defect class: completing the work made the documentation false, and
    nothing failed. It cost a dry-run to find last time.
    """
    flat = _flat(path)
    for stale in ["m1 placeholder", "written in m3", "filled in during m3",
                  "the claude adapter is built in m3", "m1 status"]:
        assert stale not in flat, f"{path.name} still says {stale!r}"


def test_the_open_experiment_record_is_not_overwritten():
    """`path-resolution.md` is an experiment record, not a placeholder.

    Q-IMPL-003 is still open, so `not-run` is its correct current content. Writing the
    adapter must not have tidied an unanswered question into an answered-looking one.
    """
    flat = _flat(ADAPTER / "path-resolution.md")
    assert "not-run" in flat
    assert "q-impl-003" in flat


# ------------------------------------------------------------ 4-8. the block itself

def test_the_block_is_delimited_exactly():
    block = _block()
    assert block.startswith("<!-- BEGIN agent-harness -->")
    assert block.endswith("<!-- END agent-harness -->")


def test_the_block_fits_the_size_ceiling():
    """2 KiB. The ceiling is Codex's concatenation budget, and the block is shared."""
    size = len(_block().encode("utf-8"))
    assert size <= BLOCK_LIMIT_BYTES, f"block is {size} bytes"


@pytest.mark.parametrize("skill", IMPLEMENTED_PRODUCTION_SKILLS)
def test_the_block_points_at_every_implemented_skill(skill):
    """Derived from the implemented list, so an eighth Skill fails here until listed."""
    assert f"/agent-harness:{skill}" in _block()


def test_the_block_does_not_advertise_the_fixture():
    """The compatibility fixture is not a product Skill and must not be reachable prose."""
    assert "m1-discovery-fixture" not in _block()


def test_the_block_says_memory_is_data():
    """Memory is read back into context on later runs; the pointer says what it is."""
    assert "data, not instructions" in " ".join(_block().split()).lower()


def test_the_block_carries_no_paragraph():
    """PRIN-01. The block holds names and paths; how a Skill works lives in the Skill.

    Checked structurally: prose arrives as paragraphs, so the guard is a run of three
    consecutive non-list, non-table lines. Everything legitimate here is a table row, a
    bullet, or a one-line lead-in.

    The size ceiling would eventually catch a long enough paragraph, but the two guards
    fail for different reasons and the reader deserves the specific one.
    """
    run = longest = 0
    for line in _block().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("|", "-", "#", "<")):
            run = 0
        else:
            run += 1
            longest = max(longest, run)
    assert longest <= 2, f"{longest} consecutive prose lines -- that is a paragraph"


# ------------------------------------------------ 9-13. capability notes stay honest

@pytest.mark.parametrize("label", ["observed", "documented", "open"])
def test_every_evidence_label_is_defined(label):
    """Documented capability and observed behaviour are different claims.

    A note that blurs them gets cited later as though a test had been run — the exact
    error M1.3.1 was spent correcting.
    """
    assert f"**{label}**" in _flat(NOTES)


def test_the_expected_agent_count_is_derived_not_asserted_by_hand():
    """The component inventory read Agents 0 in M1.4A. M3 changed what it should say.

    Pinned against the role list rather than a literal, so adding a seventh role makes
    this fail until the note is updated — which is the only way a number in prose stays
    true.
    """
    assert f"agents must now read {len(PLUGIN_AGENT_ROLES)}" in _flat(NOTES)


def test_the_absence_of_gate_a_is_recorded():
    """Claude Code has no invocation-policy gate here, so Gate B stands alone."""
    flat = _flat(NOTES)
    assert "there is no gate a here" in flat
    assert "thr-022" in flat


def test_q_impl_007_is_still_marked_open():
    """Expressiveness was settled in slice 1. Runtime enforcement was not."""
    flat = _flat(NOTES)
    assert "q-impl-007" in flat
    assert "write-attempt test" in flat


def test_the_observed_host_version_is_named():
    """One version is not a cross-version contract, so the version has to be visible."""
    assert re.search(r"\*\*2\.1\.195\*\*", _text(NOTES))


# ------------------------------------------- 14-16. the Q-IMPL-003 trap stays marked

def test_the_adapter_states_that_nothing_reads_it_at_runtime():
    flat = _flat(README)
    assert "q-impl-003" in flat
    assert "cannot resolve" in flat


def test_the_block_file_repeats_the_warning():
    """The file most likely to tempt someone into wiring a Skill to it."""
    assert "nothing reads this file at runtime" in _flat(BLOCK_FILE)


def test_no_skill_references_the_adapter_directory():
    """The check that would have caught D-04's proposed fix before it shipped."""
    skills = REPO_ROOT / "plugins" / "agent-harness" / "skills"
    offenders = [p.relative_to(REPO_ROOT).as_posix()
                 for p in skills.rglob("*.md")
                 if "adapters/claude" in p.read_text(encoding="utf-8")]
    assert not offenders, offenders
