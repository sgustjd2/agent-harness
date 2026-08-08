#!/usr/bin/env python3
"""Adapter drift check (PRIN-01, NFR-004, TST-007).

The canonical workflow layer lives in skills/ only. Adapters exist to hold
host-specific integration, not copies of workflow prose. Two guards:

  1. no run of 20+ consecutive words from a canonical Skill body may reappear
     in an adapter file
  2. total adapter prose stays under 20% of canonical Skill prose (NFR-004)

Guard 2 is reported as a note while the tree is a scaffold: with placeholder
Skills the ratio is meaningless. It becomes a failure once M2 writes real bodies.
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

    adapter_words = 0
    adapters = plugin_root / "adapters"
    if adapters.is_dir():
        for path in sorted(adapters.rglob("*.md")):
            words = _words(path.read_text(encoding="utf-8"))
            adapter_words += len(words)
            overlap = _shingles(words) & canonical
            if overlap:
                sample = " ".join(sorted(overlap)[0])
                report.fail(
                    path,
                    f"duplicates {len(overlap)} run(s) of {SHINGLE}+ words from the canonical "
                    f"Skill layer, e.g. \"{sample[:120]}...\" -- adapters must not copy "
                    "workflow prose (PRIN-01)",
                )

    if canonical_words:
        ratio = adapter_words / canonical_words
        message = f"adapter prose is {ratio:.0%} of canonical Skill prose (limit {RATIO_LIMIT:.0%})"
        if ratio > RATIO_LIMIT:
            report.note(
                message + " -- not enforced while Skills are M1 placeholders; becomes a "
                "failure once M2 writes real bodies (NFR-004)"
            )
        else:
            report.note(message)

    return report.finish()


if __name__ == "__main__":
    main(check)
