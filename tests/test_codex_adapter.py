"""M4 slice 2 — the Codex adapter layer.

Mirrors `test_claude_adapter.py`, with one addition that only exists here: the two
`AGENTS.md`/`CLAUDE.md` blocks must name the same Skills while using different invocation
prefixes. That pair is easy to get wrong in both directions — copied verbatim and wrong on
one host, or edited independently and silently divergent.
"""

from __future__ import annotations

import pathlib
import re
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _common import IMPLEMENTED_PRODUCTION_SKILLS  # noqa: E402

ADAPTERS = REPO_ROOT / "plugins" / "agent-harness" / "adapters"
CODEX = ADAPTERS / "codex"
NOTES = CODEX / "capability-notes.md"
BLOCK_FILE = CODEX / "agents-md-block.md"
CLAUDE_BLOCK_FILE = ADAPTERS / "claude" / "claude-md-block.md"

BLOCK_LIMIT_BYTES = 2048


def _text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(path: pathlib.Path) -> str:
    return " ".join(_text(path).lower().split())


def _block(path: pathlib.Path) -> str:
    found = re.search(r"<!-- BEGIN agent-harness -->.*?<!-- END agent-harness -->",
                      _text(path), re.S)
    assert found, f"{path.name} must carry a literal, delimited block"
    return found.group(0)


# ------------------------------------------------------- 1-3. no stale placeholders

@pytest.mark.parametrize("path", [NOTES, BLOCK_FILE, CODEX / "README.md"])
def test_no_file_still_calls_itself_a_placeholder(path):
    flat = _flat(path)
    for stale in ["m1 placeholder", "written in m4", "filled in during m4",
                  "the codex adapter is built in m4", "m1 status"]:
        assert stale not in flat, f"{path.name} still says {stale!r}"


@pytest.mark.parametrize("record", ["hook-root-findings.md", "install-surface.md",
                                    "path-resolution.md"])
def test_the_m1_experiment_records_are_not_overwritten(record):
    """These are results, not placeholders. Writing the adapter must not tidy an open
    question into an answered-looking one."""
    assert (CODEX / record).exists()
    assert len(_text(CODEX / record).split()) > 100


def test_the_open_path_question_still_reads_open():
    flat = _flat(CODEX / "path-resolution.md")
    assert "not-run" in flat
    assert "q-impl-003" in flat


# ------------------------------------------------------------ 4-8. the block itself

def test_the_block_is_delimited_and_fits_the_ceiling():
    block = _block(BLOCK_FILE)
    assert block.startswith("<!-- BEGIN agent-harness -->")
    assert block.endswith("<!-- END agent-harness -->")
    size = len(block.encode("utf-8"))
    assert size <= BLOCK_LIMIT_BYTES, f"block is {size} bytes"


@pytest.mark.parametrize("skill", IMPLEMENTED_PRODUCTION_SKILLS)
def test_the_block_uses_the_codex_invocation_prefix(skill):
    assert f"`${skill}`" in _block(BLOCK_FILE)


def test_the_block_names_the_chatgpt_prefix_too():
    """`$<skill>` in Codex and IDEs, `@<skill>` in ChatGPT. A block showing only one is
    wrong for whoever is on the other surface.

    The placeholders are written `<skill>` rather than `name` so they cannot be mistaken
    for a Skill entry -- by a reader or by the parity test below.
    """
    assert "`@<skill>` in chatgpt" in " ".join(_block(BLOCK_FILE).lower().split())


def test_the_block_says_memory_is_data():
    assert "data, not instructions" in " ".join(_block(BLOCK_FILE).split()).lower()


def test_the_block_carries_no_paragraph():
    run = longest = 0
    for line in _block(BLOCK_FILE).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("|", "-", "#", "<")):
            run = 0
        else:
            run += 1
            longest = max(longest, run)
    assert longest <= 2, f"{longest} consecutive prose lines -- that is a paragraph"


def test_the_block_does_not_present_templates_as_installed():
    """FR-021: optional, and never installed automatically. The block a user reads in
    their own repository is the last place that should imply otherwise."""
    flat = " ".join(_block(BLOCK_FILE).lower().split())
    assert "never installed automatically" in flat


# ----------------------------------------- 9-11. the two blocks agree where they must

def test_both_blocks_name_the_same_skills():
    """The part that must never diverge."""
    codex = set(re.findall(r"`\$([a-z-]+)`", _block(BLOCK_FILE)))
    claude = set(re.findall(r"`/agent-harness:([a-z-]+)`", _block(CLAUDE_BLOCK_FILE)))
    assert codex == claude == set(IMPLEMENTED_PRODUCTION_SKILLS)


def test_the_blocks_are_not_identical():
    """The part that must diverge. Invocation differs by host, so a block copied verbatim
    from one adapter to the other is wrong in the most visible possible way."""
    assert _block(BLOCK_FILE) != _block(CLAUDE_BLOCK_FILE)


def test_the_claude_adapter_no_longer_claims_the_blocks_are_identical():
    """It did, in M3 slice 2 — written before the Codex block existed to contradict it.

    Two user-facing files, one wrong claim, and every check green: the same shape as the
    manifest that called the Skills placeholders for two milestones.
    """
    flat = _flat(CLAUDE_BLOCK_FILE)
    assert "kept identical across both hosts" not in flat
    assert "same structure, different prefix" in flat


# ------------------------------------------------ 12-17. capability notes stay honest

@pytest.mark.parametrize("label", ["observed", "documented", "open"])
def test_every_evidence_label_is_defined(label):
    assert f"**{label}**" in _flat(NOTES)


def test_the_observed_host_version_is_named_as_an_alpha():
    flat = _flat(NOTES)
    assert "0.146.0-alpha.9.2" in flat
    assert "an alpha is not a cross-version contract" in flat


def test_registration_is_recorded_as_distinct_from_installation():
    """Confirmed empirically, not inferred — the plugin read `not installed` right after
    registering."""
    flat = _flat(NOTES)
    assert "not installed" in flat
    assert "separate lifecycle steps" in flat


def test_the_install_subcommand_carries_its_caveat():
    """It worked on one alpha and is not the documented stable path. Recorded, not relied
    on — and PROC-001 says the run itself deviated from protocol."""
    flat = _flat(NOTES)
    assert "proc-001" in flat
    assert "not a general guarantee" in flat


def test_skill_discovery_is_still_open():
    """E6. Registration proves the files arrive, not that the host offers them."""
    flat = _flat(NOTES)
    assert "open — e6" in flat or "open — e6." in flat
    assert "not run" in flat


def test_the_gate_a_asymmetry_runs_the_other_way():
    """Codex has the invocation gate and no tool-level role enforcement; Claude is the
    reverse. A document that cast one host as the weaker one throughout would be wrong
    in whichever direction it picked.
    """
    flat = _flat(NOTES)
    assert "codex has gate a, and claude does not" in flat
    assert "neither host dominates" in flat
