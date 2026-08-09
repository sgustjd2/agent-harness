#!/usr/bin/env python3
"""Adapter drift check (PRIN-01, NFR-004, TST-007).

The canonical workflow layer lives in skills/ only. Adapters exist to hold
host-specific integration, not copies of workflow prose. Two guards:

  1. no run of 20+ consecutive words from a canonical Skill body may reappear
     in a host-specific file
  2. total adapter prose stays under 20% of canonical Skill prose (NFR-004)

Guard 1 covers agents/ as well as adapters/ from M3 on, and the Codex agent
TOML templates from M4 -- their developer_instructions field is prose, and
prose is where workflow text gets copied. NFR-004 names adapters
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


ADAPTER_PROSE = "adapter prose"
ROLE_DEFINITIONS = "role definitions"
TEMPLATE_DIR_NAME = "agent-templates"


def _host_specific_files(plugin_root: pathlib.Path):
    for directory, patterns in (("adapters", ("*.md", "*.toml")), ("agents", ("*.md",))):
        root = plugin_root / directory
        if root.is_dir():
            for pattern in patterns:
                yield from root.rglob(pattern)


def _bucket(path: pathlib.Path) -> str:
    """Which budget a host-specific file belongs to.

    Role definitions are separated from adapter prose because the ratio would otherwise
    penalize the two hosts unequally for the same content. The six roles exist on both:
    on Claude as `agents/*.md`, on Codex as agent TOML templates. Claude's copy sits
    outside `adapters/` and never counted; Codex's sits inside it only because that is
    where the host requires the file to be.

    Counting one and not the other would mean shrinking the Codex role instructions to
    stay under a limit Claude's identical content does not touch -- and Codex is the host
    with weaker enforcement, so its prose is doing more work, not less. NFR-004 exists to
    stop the adapter layer growing into a second copy of the workflow, which is a
    different thing from carrying the role definitions the PRD requires on both hosts.
    """
    if TEMPLATE_DIR_NAME in path.parts or path.parts[-2] == "agents":
        return ROLE_DEFINITIONS
    return ADAPTER_PROSE


def check(plugin_root: pathlib.Path = PLUGIN_ROOT) -> int:
    report = Report("check_adapter_drift")

    canonical_words = 0
    canonical: set[tuple[str, ...]] = set()
    for path in sorted((plugin_root / "skills").rglob("*.md")):
        words = _words(path.read_text(encoding="utf-8"))
        canonical_words += len(words)
        canonical |= _shingles(words)

    counted = {ADAPTER_PROSE: 0, ROLE_DEFINITIONS: 0}
    for path in sorted(_host_specific_files(plugin_root)):
        words = _words(path.read_text(encoding="utf-8"))
        counted[_bucket(path)] += len(words)
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

    if canonical_words:
        ratio = counted[ADAPTER_PROSE] / canonical_words
        message = (f"adapter prose is {ratio:.0%} of canonical Skill prose "
                   f"(limit {RATIO_LIMIT:.0%})")
        if ratio > RATIO_LIMIT:
            report.fail("ADAPTER_RATIO_EXCEEDED", plugin_root / "adapters",
                        message + " -- NFR-004")
        else:
            report.note(message)
        report.note(
            f"role definitions are {counted[ROLE_DEFINITIONS] / canonical_words:.0%} of "
            "canonical Skill prose -- reported, not thresholded (see module docstring)")

    return report.finish()


if __name__ == "__main__":
    main(check)
