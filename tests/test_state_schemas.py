"""State schemas are well-formed -- and are NOT packaging evidence.

The five state schemas (config, plan, evidence, result, proposal) are retained because
PRD M1 deliverable 4 explicitly requires them. They describe `.agent-harness/` runtime
state, which M1 does not yet produce.

They live in core/schemas/state/ rather than beside the packaging schemas for one
reason: M1 exit criteria E3 and E4 concern the Codex plugin manifest and marketplace
catalog, and a state schema must never be mistaken for evidence about either. This file
tests that they are legal schemas and asserts the separation structurally.
"""

from __future__ import annotations

import pathlib

import pytest

from conftest import REPO_ROOT  # noqa: E402

pytestmark = pytest.mark.deterministic

STATE_DIR = REPO_ROOT / "plugins" / "agent-harness" / "core" / "schemas" / "state"
PACKAGING_DIR = REPO_ROOT / "plugins" / "agent-harness" / "core" / "schemas"

STATE_SCHEMAS = ["config", "plan", "evidence", "result", "proposal"]
PACKAGING_SCHEMAS = [
    "canonical-marketplace", "claude-marketplace", "openai-marketplace",
    "claude-plugin", "codex-plugin",
]


@pytest.mark.parametrize("name", STATE_SCHEMAS)
def test_state_schema_is_a_legal_schema(name):
    """Each state schema passes jsonschema's own check_schema."""
    from _authoritative import load_schema

    path = STATE_DIR / f"{name}.schema.json"
    assert path.is_file(), f"{name} state schema is missing"
    schema = load_schema(str(path.resolve()))
    assert schema["$schema"], "must declare a draft"
    assert schema["$id"], "must declare a stable $id"


@pytest.mark.parametrize("name", PACKAGING_SCHEMAS)
def test_packaging_schema_is_a_legal_schema(name):
    """Each packaging schema passes check_schema and declares its provenance."""
    from _authoritative import load_schema

    path = PACKAGING_DIR / f"{name}.schema.json"
    assert path.is_file(), f"{name} packaging schema is missing"
    schema = load_schema(str(path.resolve()))
    comment = schema.get("$comment", "")
    assert "LOCAL COMPATIBILITY SCHEMA" in comment, (
        f"{name} must identify itself as a local compatibility schema")
    assert "host behaviour remains authoritative" in comment.lower(), (
        f"{name} must state that host behaviour remains authoritative")
    if name != "canonical-marketplace":
        assert "http" in comment, f"{name} must cite the official documentation URL"


def test_state_schemas_are_not_in_the_packaging_directory():
    """Structural separation: a state schema must not sit beside the packaging schemas.

    If one did, a future reader could reasonably cite it as E3/E4 evidence. The
    directory boundary is the guard.
    """
    stray = [p.name for p in PACKAGING_DIR.glob("*.schema.json")
             if p.stem in STATE_SCHEMAS]
    assert not stray, (
        f"state schemas found beside packaging schemas: {stray}. "
        "They belong in core/schemas/state/ so they cannot be counted as packaging "
        "evidence for E3/E4."
    )


def test_state_directory_documents_the_separation():
    readme = STATE_DIR / "README.md"
    assert readme.is_file(), "core/schemas/state/ must explain why it is separate"
    text = readme.read_text(encoding="utf-8")
    assert "never evidence for plugin or marketplace validation" in text.lower() or \
           "never be evidence" in text.lower() or \
           "never evidence" in text.lower(), (
        "the README must state that state schemas are not packaging evidence")


def test_all_five_packaging_schemas_exist():
    """M1.1 Step 6 requires exactly these five packaging schemas."""
    missing = [n for n in PACKAGING_SCHEMAS
               if not (PACKAGING_DIR / f"{n}.schema.json").is_file()]
    assert not missing, f"missing packaging schemas: {missing}"
