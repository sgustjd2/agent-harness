#!/usr/bin/env python3
"""Canonical-layer path portability (FR-027-B, PKG-5).

The canonical Skill layer must not bake in any host-specific way of finding files.
Four things are forbidden there:

  1. host path variables    -- CLAUDE_SKILL_DIR, CLAUDE_PROJECT_DIR
  2. installation cache paths -- ~/.claude/plugins/cache, ~/.codex/plugins/cache
  3. PLUGIN_ROOT / PLUGIN_DATA -- verified for plugin HOOKS only, not Skill context
  4. cwd-dependent execution  -- e.g. running ./scripts/x.py with no anchoring

Adapters are exempt: resolving host-specific paths is exactly their job.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import PLUGIN_ROOT, Report, iter_text_files, main  # noqa: E402

CANONICAL_DIRS = ["skills", "core", "templates"]
ADAPTER_DIR = "adapters"

FORBIDDEN = [
    (re.compile(r"CLAUDE_SKILL_DIR"), "CLAUDE_SKILL_DIR", "rule 3 -- adapters only"),
    (re.compile(r"CLAUDE_PROJECT_DIR"), "CLAUDE_PROJECT_DIR", "rule 3 -- adapters only"),
    (re.compile(r"PLUGIN_ROOT"), "PLUGIN_ROOT", "rule 4 -- verified for plugin hooks only"),
    (re.compile(r"PLUGIN_DATA"), "PLUGIN_DATA", "rule 4 -- verified for plugin hooks only"),
    (re.compile(r"[~$][\w{}/]*[/\\]\.(?:claude|codex)[/\\]plugins[/\\]cache"),
     "installation cache path", "rule 2"),
    (re.compile(r"(?m)^\s*(?:\$\s*)?\./(?:scripts|bin)/"), "cwd-relative execution", "rule 1"),
]

# A line that explicitly states the prohibition is not a violation of it.
NEGATION_MARKERS = (
    "must not", "do not", "never", "forbidden", "outside the", "not assume",
    "adapters only", "hooks only", "prohibited",
)


def _is_negation(line: str) -> bool:
    low = line.lower()
    return any(marker in low for marker in NEGATION_MARKERS)


def check(plugin_root: pathlib.Path = PLUGIN_ROOT) -> int:
    report = Report("check_path_portability")

    for directory in CANONICAL_DIRS:
        base = plugin_root / directory
        if not base.is_dir():
            continue
        for path in iter_text_files(base):
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
            ):
                if _is_negation(line):
                    continue
                for pattern, label, rule in FORBIDDEN:
                    if pattern.search(line):
                        report.fail(
                            path,
                            f"line {lineno}: canonical layer uses {label} ({rule}); "
                            "move host-specific resolution into adapters/",
                        )

    adapters = plugin_root / ADAPTER_DIR
    if adapters.is_dir():
        report.note(
            f"adapters/ is exempt by design -- host-specific path resolution belongs there "
            f"(FR-027-B rule 6)."
        )
    report.note(
        "Skill-context script path resolution is still Open (Q-IMPL-003 / 27-B). "
        "Experiment B (ATS-020) investigates it; no production helper execution in M1."
    )
    return report.finish()


if __name__ == "__main__":
    main(check)
