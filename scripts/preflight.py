#!/usr/bin/env python3
"""NON-AUTHORITATIVE preflight checks. Standard library only.

This exists so a contributor without the dev virtual environment still gets a fast,
useful answer about obviously broken files. It is explicitly NOT schema validation.

Its scope is deliberately narrow and cannot overlap with the authoritative validators:
  - files that should exist, exist and are readable
  - JSON files parse as JSON (syntax only -- no schema, no field checks)
  - declared paths have no unsafe shape

It never reports success for anything jsonschema or PyYAML would judge, so it cannot
silently disagree with them. A green preflight means "worth running the real
validators", never "valid".

Its result MUST NOT be counted as schema validation evidence.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import REPO_ROOT, Report, load_json, main, path_hygiene_issues  # noqa: E402

REQUIRED_FILES = [
    "plugins/agent-harness/.claude-plugin/plugin.json",
    "plugins/agent-harness/.codex-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    "marketplace/marketplace.source.json",
    "plugins/agent-harness/core/schemas/claude-plugin.schema.json",
    "plugins/agent-harness/core/schemas/codex-plugin.schema.json",
    "plugins/agent-harness/core/schemas/claude-marketplace.schema.json",
    "plugins/agent-harness/core/schemas/openai-marketplace.schema.json",
    "plugins/agent-harness/core/schemas/canonical-marketplace.schema.json",
]


def check(repo_root: pathlib.Path = REPO_ROOT) -> int:
    report = Report("preflight (NON-AUTHORITATIVE)")

    for rel in REQUIRED_FILES:
        path = repo_root / rel
        if not path.is_file():
            report.fail("FILE_MISSING", path, "required file is missing")
            continue
        if path.suffix == ".json":
            load_json(path, report)   # syntax only

    # Path shape only. Whether a path is *correct* is the schemas' business.
    codex = repo_root / "plugins/agent-harness/.codex-plugin/plugin.json"
    if codex.is_file():
        data = load_json(codex, Report("probe"))
        if isinstance(data, dict) and isinstance(data.get("skills"), str):
            for issue in path_hygiene_issues(data["skills"]):
                report.fail(issue, codex, f"unsafe skills path shape: {data['skills']!r}")

    report.note("NON-AUTHORITATIVE: readability, JSON syntax and path shape only. "
                "This is not schema validation and must not be counted as such.")
    report.note("Authoritative validation: validate_manifests.py, validate_marketplaces.py, "
                "validate_skills.py (jsonschema + PyYAML).")
    return report.finish()


if __name__ == "__main__":
    main(check)
