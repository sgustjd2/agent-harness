"""Shared pytest fixtures and helpers.

Adds scripts/ to sys.path so validators are importable, and provides builders for
valid baseline documents that negative scenarios mutate one field at a time. Mutating
a known-good document isolates the failure: if a test fails, the mutation caused it.
"""

from __future__ import annotations

import copy
import json
import pathlib
import shutil
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
SCHEMAS = REPO_ROOT / "plugins" / "agent-harness" / "core" / "schemas"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


# --------------------------------------------------------------------------
# Valid baselines
# --------------------------------------------------------------------------

CLAUDE_PLUGIN = {
    "name": "agent-harness",
    "description": "valid baseline",
    "version": "0.0.1",
    "author": {"name": "maintainers"},
    "license": "Apache-2.0",
}

CODEX_PLUGIN = {
    "name": "agent-harness",
    "version": "0.0.1",
    "description": "valid baseline",
    "skills": "./skills/",
    "author": {"name": "maintainers"},
    "license": "Apache-2.0",
}

CLAUDE_MARKETPLACE = {
    "name": "agent-harness",
    "description": "valid baseline",
    "owner": {"name": "maintainers"},
    "plugins": [{
        "name": "agent-harness",
        "source": "./plugins/agent-harness",
        "description": "valid baseline",
        "version": "0.0.1",
        "category": "Productivity",
    }],
}

OPENAI_MARKETPLACE = {
    "name": "agent-harness",
    "interface": {"displayName": "agent-harness"},
    "plugins": [{
        "name": "agent-harness",
        # One of TWO documented local forms. The plain string "./plugins/agent-harness"
        # is equally documented; the object is what Candidate C emits, by local choice.
        "source": {"source": "local", "path": "./plugins/agent-harness"},
        "description": "valid baseline",
        "version": "0.0.1",
        "category": "Productivity",
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
    }],
}

CANONICAL_MARKETPLACE = {
    "schema_version": 1,
    "marketplace": {
        "name": "agent-harness",
        "description": "valid baseline",
        "display_name": "agent-harness",
        "owner": {"name": "maintainers"},
    },
    "plugins": [{
        "name": "agent-harness",
        "version": "0.0.1",
        "description": "valid baseline",
        "source_path": "./plugins/agent-harness",
        "category": "Productivity",
        "installation_availability": "AVAILABLE",
        "authentication_timing": "ON_INSTALL",
    }],
}

BASELINES = {
    "claude-plugin": CLAUDE_PLUGIN,
    "codex-plugin": CODEX_PLUGIN,
    "claude-marketplace": CLAUDE_MARKETPLACE,
    "openai-marketplace": OPENAI_MARKETPLACE,
    "canonical-marketplace": CANONICAL_MARKETPLACE,
}

SCHEMA_FILES = {
    "claude-plugin": "claude-plugin.schema.json",
    "codex-plugin": "codex-plugin.schema.json",
    "claude-marketplace": "claude-marketplace.schema.json",
    "openai-marketplace": "openai-marketplace.schema.json",
    "canonical-marketplace": "canonical-marketplace.schema.json",
}


def baseline(context: str) -> dict:
    """A deep copy of a known-valid document, safe to mutate."""
    return copy.deepcopy(BASELINES[context])


def schema_path(context: str) -> pathlib.Path:
    return SCHEMAS / SCHEMA_FILES[context]


def diagnose(instance: dict, context: str) -> list[str]:
    """Validate with jsonschema and return stable diagnostic codes."""
    from _authoritative import load_schema
    from _diagnostics import classify
    import jsonschema

    schema = load_schema(str(schema_path(context).resolve()))
    validator = jsonschema.validators.validator_for(schema)(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    return [classify(e, context) for e in errors]


# --------------------------------------------------------------------------
# Filesystem fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def plugin_tree(tmp_path: pathlib.Path):
    """A minimal, VALID installable plugin tree that a test can then break.

    Returns the plugin root. Every negative boundary scenario starts from a tree that
    passes, so a failure is attributable to the single change the test made.
    """
    root = tmp_path / "plugins" / "agent-harness"
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".codex-plugin").mkdir(parents=True)
    (root / "core" / "schemas").mkdir(parents=True)
    (root / "adapters").mkdir(parents=True)

    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(CLAUDE_PLUGIN, indent=2), encoding="utf-8")
    (root / ".codex-plugin" / "plugin.json").write_text(
        json.dumps(CODEX_PLUGIN, indent=2), encoding="utf-8")

    fixture = root / "skills" / "m1-discovery-fixture"
    (fixture / "agents").mkdir(parents=True)
    (fixture / "SKILL.md").write_text(
        "---\nname: m1-discovery-fixture\ndescription: valid baseline fixture\n---\n\nbody\n",
        encoding="utf-8")
    (fixture / "agents" / "openai.yaml").write_text(
        "policy:\n  allow_implicit_invocation: false\n", encoding="utf-8")

    for name in SCHEMA_FILES.values():
        shutil.copy2(SCHEMAS / name, root / "core" / "schemas" / name)

    return root


@pytest.fixture
def repo_with_spaces(tmp_path: pathlib.Path):
    """A copy of the packaging-relevant repo files under a path containing spaces.

    Exercises the ATS-015 path condition without moving the real repository.
    """
    target = tmp_path / "dir with spaces" / "agent harness copy"
    target.mkdir(parents=True)
    for rel in (".claude-plugin", ".agents", "marketplace", "plugins"):
        src = REPO_ROOT / rel
        if src.is_dir():
            shutil.copytree(src, target / rel)
    return target
