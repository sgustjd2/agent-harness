#!/usr/bin/env python3
"""Static half of the dual-manifest co-location experiment (PKG-6, PKG-8, ATS-018).

This script covers only what can be decided without a host. The dynamic half --
does Claude Code validate a plugin root containing .codex-plugin/, does Codex load
one containing .claude-plugin/ -- requires the actual hosts and is recorded as a
manual result in docs/compatibility.md (ATS-018-1, ATS-018-2, PRD §23.1.1).

Passing this script does NOT confirm co-location. DEC-P13 stays Proposed until the
manual results are recorded.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import PLUGIN_ROOT, Report, main  # noqa: E402

# PKG-8: these must survive packaging and cache copy alongside both manifests.
SHARED_RESOURCES = ["skills", "core", "templates"]


def check(plugin_root: pathlib.Path = PLUGIN_ROOT) -> int:
    report = Report("check_colocation")

    claude = plugin_root / ".claude-plugin" / "plugin.json"
    codex = plugin_root / ".codex-plugin" / "plugin.json"

    # PKG-6: both manifests coexist in one plugin root.
    for path, host in ((claude, "Claude Code"), (codex, "Codex")):
        if not path.is_file():
            report.fail(path, f"{host} manifest missing; co-location requires both (PKG-6)")

    # PKG-8: shared resources present and reachable from the same root.
    for name in SHARED_RESOURCES:
        if not (plugin_root / name).is_dir():
            report.fail(plugin_root / name, "shared resource missing (PKG-8)")

    # Both hosts must resolve to the SAME physical skills directory.
    if codex.is_file():
        import json

        try:
            manifest = json.loads(codex.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.fail(codex, f"invalid JSON: {exc.msg}")
        else:
            declared = manifest.get("skills")
            if isinstance(declared, str):
                resolved = (plugin_root / declared).resolve()
                claude_default = (plugin_root / "skills").resolve()
                if resolved != claude_default:
                    report.fail(
                        plugin_root,
                        f"Codex skills path resolves to {resolved} but Claude Code uses "
                        f"{claude_default}; both hosts must share one physical directory (PKG-7)",
                    )

    # Neither manifest directory may hold host components (PKG-4 overlap, checked here
    # too because a stray directory is exactly what would break co-location).
    for manifest_dir in (plugin_root / ".claude-plugin", plugin_root / ".codex-plugin"):
        if manifest_dir.is_dir():
            for child in sorted(manifest_dir.iterdir()):
                if child.is_dir():
                    report.fail(
                        child,
                        "component directory inside a manifest directory; this is the layout "
                        "most likely to break the other host's loader",
                    )

    report.note(
        "Static checks only. ATS-018-1/018-2 (does each host tolerate the other's manifest "
        "directory) are manual host tests -- DEC-P13 stays Proposed until they are recorded."
    )
    return report.finish()


if __name__ == "__main__":
    main(check)
