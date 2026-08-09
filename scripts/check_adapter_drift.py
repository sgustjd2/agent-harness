#!/usr/bin/env python3
"""Adapter drift check (PRIN-01, NFR-004, TST-007).

The canonical workflow layer lives in skills/ only. Adapters exist to hold
host-specific integration, not copies of workflow prose. Two guards:

  1. no run of 20+ consecutive words from a canonical Skill body may reappear
     in a host-specific file
  2. total adapter prose stays under 20% of canonical Skill prose (NFR-004)

Guard 1 covers agents/ as well as adapters/ from M3 on. NFR-004 names adapters
and the ratio follows it literally, but PRIN-01 is about where workflow prose
lives, and a role subagent is every bit as host-specific as an adapter file --
so copied prose is a violation there for exactly the same reason. Agent volume
is reported separately rather than folded into a threshold the PRD scopes to
adapters.

Guard 2 was a note through M1, when placeholder Skills made the ratio
meaningless. M2 wrote real bodies, so it is enforced.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import PLUGIN_ROOT, Report, main  # noqa: E402

SHINGLE = 20
RATIO_LIMIT = 0.20
WORD = re.compile(r"[A-Za-z0-9_.-]+")


def _words(text: str) -> list[str]:
    # Strip code fences and blockquotes: shared boilerplate there is not workflow prose.
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"(?m)^\s*>.*$", " ", text)
    return WORD.findall(text.lower())


def _shingles(words: list[str]) -> set[tuple[str, ...]]:
    return {tuple(words[i:i + SHINGLE]) for i in range(len(words) - SHINGLE + 1)}


def check(plugin_root: pathlib.Path = PLUGIN_ROOT) -> int:
    report = Report("check_adapter_drift")

    canonical_words = 0
    canonical: set[tuple[str, ...]] = set()
    for path in sorted((plugin_root / "skills").rglob("*.md")):
        words = _words(path.read_text(encoding="utf-8"))
        canonical_words += len(words)
        canonical |= _shingles(words)

    counted = {}
    for label in ("adapters", "agents"):
        directory = plugin_root / label
        total = 0
        if directory.is_dir():
            for path in sorted(directory.rglob("*.md")):
                words = _words(path.read_text(encoding="utf-8"))
                total += len(words)
                overlap = _shingles(words) & canonical
                if overlap:
                    sample = " ".join(sorted(overlap)[0])
                    report.fail(
                        "ADAPTER_PROSE_DUPLICATED",
                        path,
                        f"duplicates {len(overlap)} run(s) of {SHINGLE}+ words from the "
                        f"canonical Skill layer, e.g. \"{sample[:120]}...\" -- host-specific "
                        "files must not copy workflow prose (PRIN-01)",
                    )
        counted[label] = total

    if canonical_words:
        ratio = counted["adapters"] / canonical_words
        message = (f"adapter prose is {ratio:.0%} of canonical Skill prose "
                   f"(limit {RATIO_LIMIT:.0%})")
        if ratio > RATIO_LIMIT:
            report.fail("ADAPTER_RATIO_EXCEEDED", plugin_root / "adapters",
                        message + " -- NFR-004")
        else:
            report.note(message)
        report.note(f"role subagent prose is {counted['agents'] / canonical_words:.0%} of "
                    "canonical Skill prose -- reported, not thresholded: NFR-004 scopes its "
                    "ratio to adapters")

    return report.finish()


if __name__ == "__main__":
    main(check)
