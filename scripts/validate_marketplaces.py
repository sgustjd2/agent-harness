#!/usr/bin/env python3
"""Validate all three marketplace catalogs against their schemas (FR-002, TST-014).

Covered: the canonical source, the Claude native catalog, and the OpenAI native catalog.
Authoritative validation is jsonschema. This script adds the cross-file checks a
single-document schema cannot express: agreement between catalogs and manifests, and
that each relative source resolves from its own marketplace root.

E4 evidence: the OpenAI catalog is validated here by openai-marketplace.schema.json.
No official Codex catalog validator was found (Q-IMPL-009); docs/compatibility.md
records that this local schema is the documented substitute.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _authoritative import load_schema  # noqa: E402
from _common import PLUGIN_ROOT, REPO_ROOT, Report, load_json, main  # noqa: E402
from _diagnostics import classify  # noqa: E402
import jsonschema  # noqa: E402

SCHEMA_DIR = PLUGIN_ROOT / "core" / "schemas"

CATALOGS = [
    ("marketplace/marketplace.source.json", "canonical-marketplace.schema.json",
     "canonical-marketplace"),
    (".claude-plugin/marketplace.json", "claude-marketplace.schema.json",
     "claude-marketplace"),
    (".agents/plugins/marketplace.json", "openai-marketplace.schema.json",
     "openai-marketplace"),
]


def check(repo_root: pathlib.Path = REPO_ROOT, plugin_root: pathlib.Path = PLUGIN_ROOT) -> int:
    report = Report("validate_marketplaces")
    schema_dir = plugin_root / "core" / "schemas"
    if not schema_dir.is_dir():
        schema_dir = SCHEMA_DIR

    loaded = {}
    for rel, schema_name, context in CATALOGS:
        path = repo_root / rel
        data = load_json(path, report)
        if data is None:
            continue
        schema = load_schema(str((schema_dir / schema_name).resolve()))
        validator = jsonschema.validators.validator_for(schema)(schema)
        for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
            location = "$" + "".join(
                f"[{p}]" if isinstance(p, int) else f".{p}" for p in error.absolute_path
            )
            report.fail(classify(error, context), path, f"{location}: {error.message}")
        loaded[context] = (path, data)

        # Each relative source resolves from its own marketplace root, which for all
        # three of these catalogs is the repository root.
        for i, entry in enumerate(data.get("plugins", []) or []):
            raw = entry.get("source") or entry.get("source_path")
            # Claude publishes `source` as a string. OpenAI documents BOTH a plain
            # string path and the object {"source": "local", "path": ...}; this
            # repository generates the object, but resolution must work for either,
            # because a hand-written catalog may legitimately use the string form.
            # Do NOT silently skip an unrecognised shape -- a skipped check looks
            # identical to a passing one.
            if isinstance(raw, dict):
                source = raw.get("path")
            elif isinstance(raw, str):
                source = raw
            else:
                source = None
                report.fail("OPENAI_SOURCE_INVALID" if context == "openai-marketplace"
                            else "CLAUDE_SOURCE_INVALID", path,
                            f"$.plugins[{i}].source has unrecognised shape "
                            f"{type(raw).__name__}; cannot resolve it")
            if isinstance(source, str) and source.startswith("."):
                if not (repo_root / source).resolve().is_dir():
                    code = ("CLAUDE_SOURCE_INVALID" if context == "claude-marketplace"
                            else "OPENAI_SOURCE_INVALID")
                    report.fail(code, path,
                                f"$.plugins[{i}].source {source!r} does not resolve to a "
                                f"directory from the marketplace root")

    # Cross-catalog: the two native catalogs must advertise the same plugin identity,
    # and it must match the installed manifest.
    def identity(context):
        entry = loaded.get(context)
        if not entry:
            return None
        return [(p.get("name"), p.get("version")) for p in entry[1].get("plugins", []) or []]

    claude_ids, openai_ids = identity("claude-marketplace"), identity("openai-marketplace")
    if claude_ids and openai_ids and claude_ids != openai_ids:
        report.fail("VERSION_MISMATCH", repo_root,
                    f"catalog plugin identities differ: claude={claude_ids} openai={openai_ids}")

    manifest = load_json(plugin_root / ".claude-plugin" / "plugin.json", Report("probe"))
    if manifest and claude_ids:
        want = (manifest.get("name"), manifest.get("version"))
        for got in claude_ids:
            if got != want:
                report.fail("VERSION_MISMATCH", repo_root,
                            f"catalog entry {got} does not match plugin manifest {want}")

    report.note("validated by jsonschema against local compatibility schemas "
                "(canonical, claude-marketplace, openai-marketplace)")
    report.note("Candidate C: both native catalogs are generated from "
                "marketplace/marketplace.source.json and must not be hand-edited "
                "(PRIN-10, PKG-9). DEC-P14 remains Proposed.")
    return report.finish()


if __name__ == "__main__":
    main(check)
