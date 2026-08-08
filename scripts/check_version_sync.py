#!/usr/bin/env python3
"""Version consistency across all four version-bearing files (NFR-010).

The product version exists in two plugin manifests and two marketplace catalogs. A
disagreement ships a catalog entry pointing at a different version than the manifest.

This is a deterministic validator, not release automation: it publishes nothing, tags
nothing, and is safe to run on every commit. Renamed from check_release_version.py in
M1.1 so the name stops implying a release step.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import REPO_ROOT, Report, load_json, main  # noqa: E402

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")

SOURCES = [
    ("plugins/agent-harness/.claude-plugin/plugin.json", lambda d: d.get("version")),
    ("plugins/agent-harness/.codex-plugin/plugin.json", lambda d: d.get("version")),
    (".claude-plugin/marketplace.json", lambda d: d["plugins"][0].get("version")),
    (".agents/plugins/marketplace.json", lambda d: d["plugins"][0].get("version")),
    ("marketplace/marketplace.source.json", lambda d: d["plugins"][0].get("version")),
]


def check(repo_root: pathlib.Path = REPO_ROOT) -> int:
    report = Report("check_version_sync")
    found = {}

    for rel, extract in SOURCES:
        path = repo_root / rel
        data = load_json(path, report)
        if data is None:
            continue
        try:
            version = extract(data)
        except (KeyError, IndexError):
            report.fail("VERSION_MISSING", path, "no version could be read from this file")
            continue
        if version is None:
            report.fail("VERSION_MISSING", path, "no version declared")
        elif not SEMVER.match(str(version)):
            report.fail("VERSION_NOT_SEMVER", path, f"version {version!r} is not SemVer")
        else:
            found[rel] = version

    distinct = set(found.values())
    if len(distinct) > 1:
        detail = ", ".join(f"{r}={v}" for r, v in sorted(found.items()))
        report.fail("VERSION_MISMATCH", repo_root, f"versions disagree: {detail}")
    elif distinct:
        report.note(f"{len(found)} files agree on version {sorted(distinct)[0]}")

    return report.finish()


if __name__ == "__main__":
    main(check)
