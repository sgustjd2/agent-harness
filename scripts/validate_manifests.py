#!/usr/bin/env python3
"""Validate both plugin manifests against their packaging schemas (FR-001, PKG-4, PKG-7).

Authoritative validation is jsonschema, using the draft each schema declares.
This script adds only the cross-file checks a single-document schema cannot express:
shared-field agreement between the two manifests, and that the declared skills
directory actually exists.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _authoritative import load_schema, validate  # noqa: E402
from _common import PLUGIN_ROOT, Report, load_json, main  # noqa: E402
from _diagnostics import classify  # noqa: E402
import jsonschema  # noqa: E402

SCHEMA_DIR = PLUGIN_ROOT / "core" / "schemas"

# FR-001: these must agree between the two manifests.
SHARED_FIELDS = ["name", "version", "description", "author", "license", "homepage", "repository"]


def _validate_against(path, schema_name: str, context: str, report: Report):
    data = load_json(path, report)
    if data is None:
        return None
    schema = load_schema(str((SCHEMA_DIR / schema_name).resolve()))
    validator = jsonschema.validators.validator_for(schema)(schema)
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        location = "$" + "".join(
            f"[{p}]" if isinstance(p, int) else f".{p}" for p in error.absolute_path
        )
        report.fail(classify(error, context), path, f"{location}: {error.message}")
    return data


def check(plugin_root: pathlib.Path = PLUGIN_ROOT) -> int:
    report = Report("validate_manifests")

    claude_path = plugin_root / ".claude-plugin" / "plugin.json"
    codex_path = plugin_root / ".codex-plugin" / "plugin.json"

    claude = _validate_against(claude_path, "claude-plugin.schema.json", "claude-plugin", report)
    codex = _validate_against(codex_path, "codex-plugin.schema.json", "codex-plugin", report)
    if claude is None or codex is None:
        return report.finish()

    # Cross-file: shared fields must not drift between hosts.
    for field in SHARED_FIELDS:
        in_claude, in_codex = field in claude, field in codex
        if in_claude != in_codex:
            present = ".claude-plugin" if in_claude else ".codex-plugin"
            report.fail("VERSION_MISMATCH" if field == "version" else "SCHEMA_VIOLATION",
                        plugin_root,
                        f"shared field {field!r} present only in {present}/plugin.json")
        elif in_claude and claude[field] != codex[field]:
            report.fail("VERSION_MISMATCH" if field == "version" else "SCHEMA_VIOLATION",
                        plugin_root,
                        f"shared field {field!r} differs between manifests: "
                        f"claude={claude[field]!r} codex={codex[field]!r}")

    # Cross-file: the declared skills directory must exist (PKG-7).
    declared = codex.get("skills")
    if isinstance(declared, str):
        target = plugin_root / declared
        if not target.is_dir():
            report.fail("CODEX_SKILLS_PATH_INVALID", codex_path,
                        f"'skills' declares {declared!r} but that directory does not exist")

    # PKG-4: manifest directories hold nothing but plugin.json.
    for manifest_dir in (plugin_root / ".claude-plugin", plugin_root / ".codex-plugin"):
        if not manifest_dir.is_dir():
            continue
        extras = sorted(p.name for p in manifest_dir.iterdir() if p.name != "plugin.json")
        if extras:
            report.fail("FORBIDDEN_COMPONENT_IN_ROOT", manifest_dir,
                        f"must contain only plugin.json, found: {', '.join(extras)}")

    report.note("validated by jsonschema against local compatibility schemas "
                "(claude-plugin, codex-plugin)")
    return report.finish()


if __name__ == "__main__":
    main(check)
