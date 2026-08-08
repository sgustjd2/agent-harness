#!/usr/bin/env python3
"""Block undocumented host commands from user-facing paths (FR-028).

No plugin-install CLI subcommand appears in the official Codex documentation reviewed.
Marketplace registration and plugin installation are separate lifecycle steps: the CLI
registers a marketplace source, and installation happens through the ChatGPT desktop app.

So the command string must not appear as something a reader could copy and run. What is
blocked is an *affirmative or executable* occurrence: inside a fenced code block, on a
shell prompt line, or in prose that does not mark it as non-existent. A sentence stating
that the command does not exist is the point of the rule, not a violation of it.

docs/PRD.md and docs/compatibility.md are allowlisted outright: they are the designated
record of what was verified, and they must be able to name the command plainly.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import REPO_ROOT, Report, main  # noqa: E402

FORBIDDEN = re.compile(r"codex\s+plugin\s+install\b")

ALLOWLIST = {
    "docs/PRD.md",
    "docs/compatibility.md",
    "docs/m1-remediation.md",
    "scripts/check_no_install_command.py",
}
# Note: tests/ is deliberately NOT allowlisted. The negative test assembles the phrase
# from parts so this checker covers the whole test tree.

# Wording that marks an occurrence as a statement of non-existence.
NEGATION = re.compile(
    r"(?:no\b|not\b|never\b|does not|doesn't|absent|non-existent|nonexistent|"
    r"undocumented|unverified|forbidden|must not|blocked|없|아니|미확인)",
    re.IGNORECASE,
)

# Shapes that make an occurrence copyable.
PROMPT_LINE = re.compile(r"^\s*(?:\$|>|#)?\s*codex\s+plugin\s+install\b")

SEARCH_SUFFIXES = (".md", ".py", ".yml", ".yaml", ".json", ".toml", ".sh")
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv"}


def _fenced_line_numbers(text: str) -> set[int]:
    """Line numbers inside triple-backtick fences."""
    inside = False
    fenced = set()
    for lineno, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if inside:
            fenced.add(lineno)
    return fenced


def check(repo_root: pathlib.Path = REPO_ROOT) -> int:
    report = Report("check_no_install_command")

    for path in sorted(repo_root.rglob("*")):
        if not path.is_file() or path.suffix not in SEARCH_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            rel = path.relative_to(repo_root).as_posix()
        except ValueError:
            continue
        if rel in ALLOWLIST:
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        if not FORBIDDEN.search(text):
            continue
        fenced = _fenced_line_numbers(text)

        for lineno, line in enumerate(text.splitlines(), start=1):
            if not FORBIDDEN.search(line):
                continue
            executable = lineno in fenced or PROMPT_LINE.match(line)
            if executable or not NEGATION.search(line):
                report.fail(
                    "UNDOCUMENTED_INSTALL_COMMAND", path,
                    f"line {lineno}: affirmative or executable use of an undocumented "
                    "plugin-install subcommand. Registration and installation are "
                    "separate steps; installation happens in the ChatGPT desktop app",
                )

    report.note(f"allowlisted (they record the command's non-existence): "
                f"{', '.join(sorted(ALLOWLIST))}")
    return report.finish()


if __name__ == "__main__":
    main(check)
