"""M5 slice 1 — run-state persistence and the state-model document.

The slice's real change is that `orchestrate` and `verify-work` now write run artifacts.
That closes dry-run finding D-01, and it is the first time in the project's history that a
Skill's write surface has been *widened* rather than narrowed — so most of these tests are
about the widening staying as small as it was justified to be.

The document is tested against the constants rather than against itself, so a page that
describes a policy the code does not implement fails here rather than misleading someone.
"""

from __future__ import annotations

import pathlib
import sys

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _common import (  # noqa: E402
    ALLOWED_WRITE_PATH_ROOTS,
    PROFILES_REQUIRING_PATH_ROOTS,
    PROFILES_WRITING_RUN_ARTIFACTS,
    RUN_ARTIFACT_ROOT,
    SKILL_SAFETY_PROFILES,
    extract_policy_marker,
)

DOC = REPO_ROOT / "docs" / "state-model.md"
SKILLS = REPO_ROOT / "plugins" / "agent-harness" / "skills"
SCHEMAS = REPO_ROOT / "plugins" / "agent-harness" / "core" / "schemas" / "state"

PRODUCERS = ["orchestrate", "verify-work"]


def _flat(path: pathlib.Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


def _marker(skill: str) -> dict:
    return yaml.safe_load(extract_policy_marker(
        (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")))


# ------------------------------------------------ 1-5. the widening stays narrow

@pytest.mark.parametrize("skill", PRODUCERS)
def test_the_producers_declare_run_artifact_persistence(skill):
    marker = _marker(skill)
    assert marker["evidence_persistence"] == "run-artifacts"
    assert marker["writes_run_artifacts"] is True


def test_verify_work_gained_exactly_one_write_root():
    """Narrower than init-project's `.agent-harness/` on purpose: a verifier has no
    business touching config or memory."""
    assert ALLOWED_WRITE_PATH_ROOTS["verify-work"] == [RUN_ARTIFACT_ROOT]
    assert "bounded-verification" in PROFILES_REQUIRING_PATH_ROOTS


def test_verify_work_still_modifies_no_source_and_no_config():
    """The widening is a write surface, not an authority."""
    profile = SKILL_SAFETY_PROFILES["bounded-verification"]
    assert profile["modifies_source"] is False
    assert profile["modifies_config"] is False
    assert profile["spawns_agents"] is False


def test_orchestrate_declares_no_static_write_roots():
    """Its surface is plan-defined and cannot be enumerated in advance, which is why it
    is absent from PROFILES_REQUIRING_PATH_ROOTS while still writing run artifacts."""
    assert "plan-bounded-orchestration" not in PROFILES_REQUIRING_PATH_ROOTS
    assert "orchestrate" not in ALLOWED_WRITE_PATH_ROOTS
    assert "plan-bounded-orchestration" in PROFILES_WRITING_RUN_ARTIFACTS


def test_only_the_two_producers_write_run_artifacts():
    """A third Skill acquiring this by inheritance would be a decision, not a default."""
    writers = [name for name, p in SKILL_SAFETY_PROFILES.items()
               if p.get("writes_run_artifacts")]
    assert sorted(writers) == sorted(PROFILES_WRITING_RUN_ARTIFACTS)


# ------------------------------------------- 6-10. the immutability rules are stated

@pytest.mark.parametrize("skill", PRODUCERS)
def test_evidence_is_append_only(skill):
    body = _flat(SKILLS / skill / "SKILL.md")
    assert "append-only" in body
    assert "correction is a new item" in body or "correction is a new item" in body


@pytest.mark.parametrize("skill", PRODUCERS)
def test_a_result_is_written_in_every_terminal_state(skill):
    """A run with no result file is indistinguishable from one that never started."""
    assert "every** terminal state" in _flat(SKILLS / skill / "SKILL.md")


@pytest.mark.parametrize("skill", PRODUCERS)
def test_neither_producer_creates_the_harness_directory(skill):
    """Initialization is approval-gated and belongs to init-project."""
    body = _flat(SKILLS / skill / "SKILL.md")
    assert "init-project" in body
    assert "do not create" in body


def test_verification_still_reports_when_it_cannot_persist():
    """Results you can read beat results withheld because the paperwork failed."""
    assert "could not be persisted" in _flat(SKILLS / "verify-work" / "SKILL.md")


def test_the_queue_and_resume_engine_remain_out_of_scope():
    """Writing down what happened does not require run lifecycle machinery."""
    assert "still no queue and no resume engine" in _flat(SKILLS / "orchestrate" / "SKILL.md")


# ------------------------------------------------- 11-18. the document is accurate

def test_the_document_is_no_longer_a_placeholder():
    flat = _flat(DOC)
    for stale in ["m1 placeholder", "written in m5"]:
        assert stale not in flat


def test_the_document_names_the_same_run_artifact_root():
    """Derived from the constant, so the page cannot drift from the validator."""
    assert RUN_ARTIFACT_ROOT.rstrip("/") in DOC.read_text(encoding="utf-8")


@pytest.mark.parametrize("schema", ["plan", "evidence", "result", "config", "proposal"])
def test_every_state_schema_is_still_there_to_be_authoritative(schema):
    """The page defers to the schemas; the schemas have to exist for that to mean
    anything."""
    assert (SCHEMAS / f"{schema}.schema.json").is_file()


def test_the_document_defers_to_the_schemas():
    flat = _flat(DOC)
    assert "the schemas are authoritative and this page is the bug" in flat


def test_the_commit_split_is_stated_with_its_reason():
    """Memory is shared because a team not sharing it runs three different harnesses;
    evidence stays local because it quotes raw output."""
    flat = _flat(DOC)
    assert "memory is the product; evidence is the exhaust" in flat
    assert "the plugin never runs `git add` or `git commit`" in flat


def test_completion_does_not_require_committing_evidence():
    assert "completing a run never requires committing evidence" in _flat(DOC)


def test_deletion_is_never_automatic_by_default():
    flat = _flat(DOC)
    assert "nothing is deleted automatically unless you set `runs.auto_prune: true`" in flat
    assert "deletion is irreversible" in flat


def test_redaction_is_described_as_fail_closed_and_before_writing():
    flat = _flat(DOC)
    assert "fail-closed" in flat
    assert "before** anything is written, never after" in flat


def test_the_newer_schema_version_rule_stops_writing():
    """A newer file means something understands the format better than this version."""
    flat = _flat(DOC)
    assert "writing stops" in flat


def test_the_d01_lesson_is_recorded_where_the_model_is_explained():
    """The union of verified parts is not a verified whole — the sentence this project
    has now paid for twice."""
    flat = _flat(DOC)
    assert "d-01" in flat
    assert "the union of verified parts is not a verified whole" in flat


def test_memory_files_are_described_as_data_not_instructions():
    """They are read back into context on every later run."""
    flat = _flat(DOC)
    assert "data and not instructions" in flat
    assert "standing injection surface" in flat
