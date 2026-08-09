#!/usr/bin/env python3
"""Validate the optional Codex agent TOML templates (M4, FR-021).

These are the only files in the repository that are **designed to be copied outside it**,
into `.codex/agents/` in a user's project. Everything else here either ships as part of
the plugin or stays in the repository; these leave.

That is why FR-021 rule 5 requires validation *before* a copy. This runs the same checks
at build time, so a template cannot reach the point of being copied while malformed --
and so a malicious fork has to break a check that is in the repository rather than one
that only exists in a procedure nobody runs.

What is checked:

  - one template per role, matching the Claude subagent set exactly. A role that exists
    on one host and not the other is a parity defect, and MET-003 is measured on it
  - required fields present: name, description, developer_instructions
  - no unknown key. An unknown key in an agent definition is either a typo that silently
    does nothing, or a field doing something nobody reviewed
  - sandbox_mode, where present, is one of the documented values -- and never widened
    past what the role needs
  - no path, no shell, no network reference anywhere in the file

Parsing is `tomllib`. This module contains no TOML parser of its own, for the same reason
_common.py contains no YAML parser: an approximation of a standard can disagree with the
real implementation while still reporting success.
"""

from __future__ import annotations

import pathlib
import re
import sys
import tomllib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import PLUGIN_AGENT_ROLES, PLUGIN_ROOT, Report, main  # noqa: E402

TEMPLATE_DIR = "adapters/codex/agent-templates"

REQUIRED_FIELDS = {"name", "description", "developer_instructions"}
OPTIONAL_FIELDS = {"sandbox_mode"}
ALLOWED_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS

# Documented Codex sandbox modes. `danger-full-access` is deliberately not accepted:
# a bundled template that hands out full access is THR-015 in one line, and no role in
# this product needs it.
ALLOWED_SANDBOX_MODES = {"read-only", "workspace-write"}

# Roles whose sandbox mode is fixed by the role itself. Anything else must not declare a
# mode at all -- inventing one to look like a constraint is worse than omitting it,
# because a reviewer counts it.
REQUIRED_SANDBOX_MODE = {
    "researcher": "read-only",
    "reviewer": "read-only",
    "tester": "workspace-write",
}

# Shapes that must never appear in a file destined for someone else's project.
FORBIDDEN_PATTERNS = [
    ("TEMPLATE_USER_SCOPE_PATH", re.compile(r"~/\.codex|~/\.claude|~/\.agents")),
    ("TEMPLATE_PARENT_TRAVERSAL", re.compile(r"\.\.[\\/]")),
    ("TEMPLATE_ABSOLUTE_PATH", re.compile(r"(?:^|\s)(?:/[A-Za-z]|[A-Za-z]:\\)")),
    ("TEMPLATE_NETWORK_REFERENCE", re.compile(r"https?://|\bcurl\b|\bwget\b|\bpip install\b")),
    ("TEMPLATE_ENV_INTERPOLATION", re.compile(r"\$\{|\$[A-Z_]{3,}|%[A-Z_]{3,}%")),
]


def check(plugin_root: pathlib.Path = PLUGIN_ROOT) -> int:
    report = Report("validate_agent_templates")

    directory = plugin_root / TEMPLATE_DIR
    if not directory.is_dir():
        report.fail("TEMPLATE_DIR_MISSING", directory,
                    "the optional Codex agent templates are an M4 deliverable")
        return report.finish()

    found = {p.stem: p for p in sorted(directory.glob("*.toml"))}

    for role in PLUGIN_AGENT_ROLES:
        if role not in found:
            report.fail("TEMPLATE_ROLE_MISSING", directory / f"{role}.toml",
                        f"role {role!r} has a Claude subagent but no Codex template -- "
                        "the two hosts would offer different roles, which is what "
                        "MET-003 parity measures")
    for name, path in found.items():
        if name not in PLUGIN_AGENT_ROLES:
            report.fail("TEMPLATE_ROLE_UNKNOWN", path,
                        f"{name!r} is not one of the six defined roles")

    for role in PLUGIN_AGENT_ROLES:
        path = found.get(role)
        if path is None:
            continue
        raw = path.read_text(encoding="utf-8")
        try:
            data = tomllib.loads(raw)
        except tomllib.TOMLDecodeError as exc:
            report.fail("TEMPLATE_TOML_INVALID", path, f"invalid TOML: {exc}")
            continue

        keys = set(data)
        for missing in sorted(REQUIRED_FIELDS - keys):
            report.fail("TEMPLATE_FIELD_MISSING", path,
                        f"required field {missing!r} is absent")
        for extra in sorted(keys - ALLOWED_FIELDS):
            report.fail("TEMPLATE_FIELD_UNKNOWN", path,
                        f"field {extra!r} is not a documented Codex agent field -- it "
                        "either does nothing silently or does something unreviewed")

        if data.get("name") != role:
            report.fail("TEMPLATE_NAME_MISMATCH", path,
                        f"name {data.get('name')!r} does not match filename {role!r}")

        expected_mode = REQUIRED_SANDBOX_MODE.get(role)
        mode = data.get("sandbox_mode")
        if mode is not None and mode not in ALLOWED_SANDBOX_MODES:
            report.fail("TEMPLATE_SANDBOX_MODE_INVALID", path,
                        f"sandbox_mode {mode!r} is not one of {sorted(ALLOWED_SANDBOX_MODES)}")
        elif expected_mode and mode != expected_mode:
            report.fail("TEMPLATE_SANDBOX_MODE_WRONG", path,
                        f"{role!r} must declare sandbox_mode {expected_mode!r}, found {mode!r}")
        elif not expected_mode and mode is not None:
            report.fail("TEMPLATE_SANDBOX_MODE_UNEXPECTED", path,
                        f"{role!r} declares sandbox_mode {mode!r}; the PRD does not fix one "
                        "for this role, and inventing a value makes a session default look "
                        "like a reviewed constraint")

        for code, pattern in FORBIDDEN_PATTERNS:
            hit = pattern.search(raw)
            if hit:
                report.fail(code, path,
                            f"contains {hit.group(0)!r} -- this file is copied into "
                            "someone else's project and must carry no path, no command "
                            "and no network reference")

    report.note(f"{len(found)} template(s); copied only by hand, never by a Skill "
                "(FR-021 rules 3 and 6)")
    return report.finish()


if __name__ == "__main__":
    main(check)
