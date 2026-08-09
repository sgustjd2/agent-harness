#!/usr/bin/env python3
"""Validate the Claude Code role subagents (M3, PRD section 12).

Six roles, one file each, in the installable plugin root's `agents/` directory. This
directory was rejected outright until M3 -- shipping an agent name the hosts can see
with nothing behind it is a product surface, the same argument that kept unimplemented
Skill names out of the root. It is validated now rather than merely permitted.

What is checked:

  - exactly the six roles exist, no extras, no omissions
  - frontmatter carries name, description and tools, and nothing else. Plugin subagents
    do not support hooks, mcpServers or permissionMode, so a file declaring one is
    asking for an enforcement that will not happen
  - the tools allowlist matches the role's grant exactly
  - no role holds a network tool; only coordinator holds the delegation tool
  - the body declares an authority marker, parsed as YAML, agreeing with that grant

The last check is the one that carries weight. A body may honestly say "read-only" while
the frontmatter grants Write, and prose is not machine-checkable -- so the marker states
the claim and this compares it against the tools that were actually granted.
"""

from __future__ import annotations

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _authoritative import load_frontmatter  # noqa: E402
from _common import (  # noqa: E402
    AGENT_ENFORCEMENT_LEVELS,
    AGENT_FRONTMATTER_OPTIONAL,
    AGENT_FRONTMATTER_REQUIRED,
    PLUGIN_AGENT_ROLES,
    PLUGIN_ROOT,
    ROLE_EXECUTION_TOOL,
    ROLE_INSTRUCTION_ONLY_LIMITS,
    ROLE_TOOL_DELEGATION,
    ROLE_TOOLS,
    ROLE_TOOLS_FORBIDDEN_EVERYWHERE,
    ROLE_WRITE_TOOLS,
    ROLES_PERMITTED_DELEGATION,
    FrontmatterError,
    Report,
    agent_files,
    extract_policy_marker,
    main,
)

ALLOWED_KEYS = AGENT_FRONTMATTER_REQUIRED | AGENT_FRONTMATTER_OPTIONAL

# Frontmatter keys a plugin subagent cannot act on. Declaring one is worse than omitting
# it: it reads like a permission boundary and is not one.
UNSUPPORTED_KEYS = ["hooks", "mcpServers", "permissionMode", "allowed-tools",
                    "disable-model-invocation", "sandbox_mode"]

# Authority fields every role marker must declare. All booleans except the last two.
MARKER_BOOLEANS = ["read_only", "writes_source", "writes_harness_state",
                   "executes_commands", "delegates", "network_access"]


def _parse_tools(raw) -> list[str] | None:
    """Split the documented comma-separated `tools` string.

    Claude Code documents this field as a comma-separated string. A YAML list is
    rejected rather than accommodated -- one form in one repository means the drift
    between two files is a diff, not a judgement call.
    """
    if not isinstance(raw, str):
        return None
    return [part.strip() for part in raw.split(",") if part.strip()]


def _check_marker(report: Report, path: pathlib.Path, role: str,
                  body: str, tools: list[str]) -> None:
    raw = extract_policy_marker(body)
    if raw is None:
        report.fail("AGENT_POLICY_MARKER_MISSING", path,
                    f"{role!r} declares no authority marker -- the tools grant is then "
                    "the only statement of what this role may do, and nothing checks "
                    "that the body agrees with it")
        return
    try:
        marker = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        report.fail("AGENT_POLICY_MARKER_INVALID", path, f"marker is not valid YAML: {exc}")
        return
    if not isinstance(marker, dict):
        report.fail("AGENT_POLICY_MARKER_INVALID", path, "marker did not parse to a mapping")
        return

    if marker.get("role") != role:
        report.fail("AGENT_POLICY_ROLE_MISMATCH", path,
                    f"marker declares role {marker.get('role')!r}, file is {role!r}")

    for field in MARKER_BOOLEANS:
        if field not in marker:
            report.fail("AGENT_POLICY_FIELD_MISSING", path,
                        f"{role!r} marker omits {field!r}")
        elif not isinstance(marker[field], bool):
            report.fail("AGENT_POLICY_FIELD_NOT_BOOLEAN", path,
                        f"{role!r} marker field {field!r} must be a boolean")

    # ---- the marker's claims against the tools actually granted -------------
    writes = [t for t in ROLE_WRITE_TOOLS if t in tools]
    if marker.get("read_only") is True and writes:
        report.fail("AGENT_READ_ONLY_CONTRADICTED", path,
                    f"{role!r} declares read_only but is granted {', '.join(writes)}")
    if marker.get("read_only") is False and not writes:
        report.fail("AGENT_READ_ONLY_UNDERCLAIMED", path,
                    f"{role!r} declares read_only: false but holds no write tool -- "
                    "a role that claims more authority than it has invites a reviewer "
                    "to approve a grant nobody made")

    executes = ROLE_EXECUTION_TOOL in tools
    if marker.get("executes_commands") is not executes:
        report.fail("AGENT_EXECUTION_CLAIM_MISMATCH", path,
                    f"{role!r} declares executes_commands: {marker.get('executes_commands')} "
                    f"but {ROLE_EXECUTION_TOOL} is {'granted' if executes else 'absent'}")

    delegates = ROLE_TOOL_DELEGATION in tools
    if marker.get("delegates") is not delegates:
        report.fail("AGENT_DELEGATION_CLAIM_MISMATCH", path,
                    f"{role!r} declares delegates: {marker.get('delegates')} but "
                    f"{ROLE_TOOL_DELEGATION} is {'granted' if delegates else 'absent'}")

    if marker.get("network_access") is not False:
        report.fail("AGENT_NETWORK_CLAIMED", path,
                    f"{role!r} must declare network_access: false")

    # ---- enforcement level -------------------------------------------------
    level = marker.get("enforcement")
    if level not in AGENT_ENFORCEMENT_LEVELS:
        report.fail("AGENT_ENFORCEMENT_LEVEL_INVALID", path,
                    f"{role!r} declares enforcement {level!r}; expected one of "
                    f"{AGENT_ENFORCEMENT_LEVELS}")
        return

    expected_limits = ROLE_INSTRUCTION_ONLY_LIMITS[role]
    declared = marker.get("instruction_only_limits") or []
    if expected_limits and level != "mixed":
        report.fail("AGENT_ENFORCEMENT_OVERCLAIMED", path,
                    f"{role!r} declares enforcement {level!r} while stating limits the "
                    "tools allowlist cannot express -- a path or command scope is prose, "
                    "and calling it tool-enforced misreports what is actually guaranteed")
    if not expected_limits and level != "tool-allowlist":
        report.fail("AGENT_ENFORCEMENT_UNDERCLAIMED", path,
                    f"{role!r} has no instruction-only limit but declares {level!r}")
    if sorted(declared) != sorted(expected_limits):
        report.fail("AGENT_INSTRUCTION_LIMITS_MISMATCH", path,
                    f"{role!r} marker lists {declared!r}; expected {expected_limits!r}")


def check(plugin_root: pathlib.Path = PLUGIN_ROOT) -> int:
    report = Report("validate_agents")

    files = agent_files(plugin_root)
    found = {p.stem: p for p in files}

    for role in PLUGIN_AGENT_ROLES:
        if role not in found:
            report.fail("AGENT_ROLE_MISSING", plugin_root / "agents" / f"{role}.md",
                        f"role {role!r} has no subagent definition")
    for name, path in found.items():
        if name not in PLUGIN_AGENT_ROLES:
            report.fail("AGENT_ROLE_UNKNOWN", path,
                        f"{name!r} is not one of the six defined roles")

    for role in PLUGIN_AGENT_ROLES:
        path = found.get(role)
        if path is None:
            continue
        try:
            front, body = load_frontmatter(path)
        except FrontmatterError as exc:
            report.fail("FRONTMATTER_MISSING", path, str(exc))
            continue
        except yaml.YAMLError as exc:
            report.fail("FRONTMATTER_INVALID_YAML", path, f"invalid YAML: {exc}")
            continue
        if not isinstance(front, dict):
            report.fail("FRONTMATTER_INVALID_YAML", path, "frontmatter is not a mapping")
            continue

        keys = set(front)
        for missing in sorted(ALLOWED_KEYS - keys):
            report.fail("AGENT_FIELD_MISSING", path, f"required field {missing!r} is absent")
        for extra in sorted(keys - ALLOWED_KEYS):
            code = ("AGENT_FIELD_UNSUPPORTED" if extra in UNSUPPORTED_KEYS
                    else "AGENT_FIELD_UNKNOWN")
            report.fail(code, path, f"field {extra!r} is not permitted in a plugin subagent")

        if front.get("name") != role:
            report.fail("AGENT_NAME_MISMATCH", path,
                        f"frontmatter name {front.get('name')!r} does not match filename {role!r}")

        tools = _parse_tools(front.get("tools"))
        if tools is None:
            report.fail("AGENT_TOOLS_NOT_A_STRING", path,
                        "tools must be the documented comma-separated string form")
            continue

        expected = ROLE_TOOLS[role]
        if tools != expected:
            report.fail("AGENT_TOOLS_MISMATCH", path,
                        f"{role!r} grants {tools!r}; the role permits {expected!r}")

        for forbidden in ROLE_TOOLS_FORBIDDEN_EVERYWHERE:
            if forbidden in tools:
                report.fail("AGENT_NETWORK_TOOL_GRANTED", path,
                            f"{role!r} is granted {forbidden!r}; no role reaches the network")

        if ROLE_TOOL_DELEGATION in tools and role not in ROLES_PERMITTED_DELEGATION:
            report.fail("AGENT_DELEGATION_TOOL_GRANTED", path,
                        f"{role!r} is granted {ROLE_TOOL_DELEGATION!r}; only "
                        f"{ROLES_PERMITTED_DELEGATION} may delegate")

        _check_marker(report, path, role, body, tools)

    return report.finish()


if __name__ == "__main__":
    main(check)
