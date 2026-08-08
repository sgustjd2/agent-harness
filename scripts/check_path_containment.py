#!/usr/bin/env python3
"""Plugin-root containment (PKG-1, PKG-2, PKG-3, SEC-05, SEC-06).

The installed plugin must be self-contained. Nothing inside it may reference a path
outside it, resolve outside it through a symlink, or depend on a development-only tree.

Renamed from check_packaging.py in M1.1: the old name described where it ran, not what
it enforced.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import PLUGIN_ROOT, Report, is_contained, iter_text_files, main  # noqa: E402

RELATIVE_CLIMB = re.compile(r"(?<![\w.])((?:\.\./)+)")
DEV_ONLY = ("tests/", ".github/workflows/")


def _may_discuss_layout(rel: pathlib.Path) -> bool:
    """Human-facing records may name a dev tree; anything a host loads may not.

    README.md explains layout by definition, and Markdown under adapters/ is the
    experiment-record layer -- recording where a fixture lives is its purpose.
    skills/** stays strict: a model reads SKILL.md and would act on a path found there.
    """
    return rel.name == "README.md" or (rel.parts[0] == "adapters" and rel.suffix == ".md")


def check(plugin_root: pathlib.Path = PLUGIN_ROOT) -> int:
    report = Report("check_path_containment")
    if not plugin_root.is_dir():
        report.fail("FILE_MISSING", plugin_root, "plugin root does not exist")
        return report.finish()

    for path in iter_text_files(plugin_root):
        rel = path.relative_to(plugin_root)
        depth = len(rel.parts) - 1
        text = path.read_text(encoding="utf-8", errors="replace")

        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in RELATIVE_CLIMB.finditer(line):
                if match.group(1).count("../") > depth:
                    report.fail("PATH_ESCAPES_PLUGIN_ROOT", path,
                                f"line {lineno}: relative path climbs past the plugin root")

        if not _may_discuss_layout(rel):
            for marker in DEV_ONLY:
                if marker in text:
                    report.fail("PATH_ESCAPES_PLUGIN_ROOT", path,
                                f"references development-only tree {marker!r} (PKG-3)")

    # SEC-06: a symlink resolving outside the plugin root escapes containment.
    for path in sorted(plugin_root.rglob("*")):
        if path.is_symlink() and not is_contained(path, plugin_root):
            report.fail("SYMLINK_ESCAPE", path,
                        "symbolic link resolves outside the installable plugin root")

    for required in ("skills", "core/schemas", "adapters"):
        if not (plugin_root / required).is_dir():
            report.fail("FILE_MISSING", plugin_root / required,
                        "required runtime directory is missing (PKG-1)")

    return report.finish()


if __name__ == "__main__":
    main(check)
