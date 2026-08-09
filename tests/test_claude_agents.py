"""M3 slice 1 — the six Claude Code role subagents (PRD section 12).

These tests exist to keep three things from drifting apart: the tool grant in the
frontmatter, the authority the body claims, and the role definition in the PRD. Any two
of them can agree while the third quietly disagrees, and the disagreement that matters
most is invisible by construction -- a body that says "read-only" beside a frontmatter
that grants Write reads perfectly well to a human.

The negative cases matter more than the positive ones. A validator that only ever sees
correct input has not been shown to reject anything.
"""

from __future__ import annotations

import pathlib
import sys

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_agents  # noqa: E402
from _common import (  # noqa: E402
    AGENT_FRONTMATTER_REQUIRED,
    PLUGIN_AGENT_ROLES,
    ROLE_EXECUTION_TOOL,
    ROLE_INSTRUCTION_ONLY_LIMITS,
    ROLE_TOOL_DELEGATION,
    ROLE_TOOLS,
    ROLE_TOOLS_FORBIDDEN_EVERYWHERE,
    ROLE_WRITE_TOOLS,
    ROLES_FULLY_TOOL_ENFORCED,
    ROLES_PERMITTED_DELEGATION,
    extract_policy_marker,
    split_frontmatter,
)

AGENTS = REPO_ROOT / "plugins" / "agent-harness" / "agents"


def _read(role: str) -> tuple[dict, str]:
    text = (AGENTS / f"{role}.md").read_text(encoding="utf-8")
    raw, body = split_frontmatter(text)
    return yaml.safe_load(raw), body


def _marker(role: str) -> dict:
    return yaml.safe_load(extract_policy_marker(_read(role)[1]))


def _flat(text: str) -> str:
    return " ".join(text.lower().split())


# ------------------------------------------------------- 1-3. the set of roles

def test_exactly_the_six_roles_exist():
    on_disk = sorted(p.stem for p in AGENTS.glob("*.md"))
    assert on_disk == sorted(PLUGIN_AGENT_ROLES)


def test_the_shipped_tree_validates():
    assert validate_agents.check() == 0


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_frontmatter_has_exactly_the_permitted_keys(role):
    front, _ = _read(role)
    assert set(front) == AGENT_FRONTMATTER_REQUIRED
    assert front["name"] == role


# ------------------------------------------------------------- 4-8. tool grants

@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_tools_are_the_documented_comma_separated_string(role):
    front, _ = _read(role)
    assert isinstance(front["tools"], str), (
        "Claude Code documents `tools` as a comma-separated string; a YAML list is a "
        "second form for the same thing and this repository keeps one"
    )
    assert validate_agents._parse_tools(front["tools"]) == ROLE_TOOLS[role]


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_no_role_reaches_the_network(role):
    granted = ROLE_TOOLS[role]
    for forbidden in ROLE_TOOLS_FORBIDDEN_EVERYWHERE:
        assert forbidden not in granted


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_only_the_coordinator_may_delegate(role):
    has_it = ROLE_TOOL_DELEGATION in ROLE_TOOLS[role]
    assert has_it == (role in ROLES_PERMITTED_DELEGATION)


def test_reviewer_cannot_delegate():
    """Explicit because the PRD calls it out: nested delegation is the escape hatch.

    A reviewer that could delegate could hand the review to something holding wider
    permissions than its own, and the read-only guarantee would end one hop away from
    where anyone was looking.
    """
    assert ROLE_TOOL_DELEGATION not in ROLE_TOOLS["reviewer"]


@pytest.mark.parametrize("role", ["researcher", "reviewer"])
def test_read_only_roles_hold_no_write_and_no_shell(role):
    granted = ROLE_TOOLS[role]
    assert not [t for t in ROLE_WRITE_TOOLS if t in granted]
    assert ROLE_EXECUTION_TOOL not in granted


@pytest.mark.parametrize("role", ["tester", "refiner"])
def test_record_writing_roles_cannot_edit(role):
    """Write without Edit. Evidence and proposals are written once.

    A role that could edit its own record could revise a result after seeing it, which
    is the one change nobody downstream would detect.
    """
    assert "Write" in ROLE_TOOLS[role]
    assert "Edit" not in ROLE_TOOLS[role]


# --------------------------------------------- 9-13. markers agree with grants

@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_marker_declares_the_role_it_is_in(role):
    assert _marker(role)["role"] == role


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_read_only_claim_matches_the_write_grant(role):
    marker = _marker(role)
    writes = [t for t in ROLE_WRITE_TOOLS if t in ROLE_TOOLS[role]]
    assert marker["read_only"] is (not writes)


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_execution_and_delegation_claims_match_the_grant(role):
    marker = _marker(role)
    assert marker["executes_commands"] is (ROLE_EXECUTION_TOOL in ROLE_TOOLS[role])
    assert marker["delegates"] is (ROLE_TOOL_DELEGATION in ROLE_TOOLS[role])


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_no_role_claims_network_access(role):
    assert _marker(role)["network_access"] is False


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_no_role_claims_to_write_source_except_implementer(role):
    assert _marker(role)["writes_source"] is (role == "implementer")


# ----------------------------------------------------- 14-17. the Q-IMPL-007 answer

def test_only_the_read_only_roles_are_fully_tool_enforced():
    """The load-bearing claim of this slice.

    Q-IMPL-007 asks whether the `tools` allowlist alone can enforce read-only for
    researcher and reviewer. The expressiveness half is answerable without a host: the
    frontmatter selects TOOLS, and has no syntax for a path scope or a command class.
    So a role whose limits are all "which tool" is fully enforced, and a role with any
    "which path" or "which command" limit is not -- and those are exactly the four that
    hold Write or Bash.
    """
    assert sorted(ROLES_FULLY_TOOL_ENFORCED) == ["researcher", "reviewer"]


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_enforcement_level_follows_from_the_limits(role):
    marker = _marker(role)
    expected = "tool-allowlist" if role in ROLES_FULLY_TOOL_ENFORCED else "mixed"
    assert marker["enforcement"] == expected


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_instruction_only_limits_are_declared_in_the_body(role):
    declared = _marker(role).get("instruction_only_limits") or []
    assert sorted(declared) == sorted(ROLE_INSTRUCTION_ONLY_LIMITS[role])


@pytest.mark.parametrize("role", ["coordinator", "implementer", "tester", "refiner"])
def test_mixed_roles_say_plainly_which_limits_are_only_prose(role):
    """A role that cannot enforce a limit must not let the reader assume it does."""
    body = _flat(_read(role)[1])
    assert "enforcement: mixed" in body
    assert "prose" in body


# ------------------------------------------------------- 18-24. negative cases

def _write_tree(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "plugin"
    (root / "agents").mkdir(parents=True)
    for role in PLUGIN_AGENT_ROLES:
        src = (AGENTS / f"{role}.md").read_text(encoding="utf-8")
        (root / "agents" / f"{role}.md").write_text(src, encoding="utf-8")
    return root


def _codes(root: pathlib.Path, capsys) -> list[str]:
    validate_agents.check(root)
    captured = capsys.readouterr()
    return [line.split("]")[0].lstrip(" -[")
            for line in (captured.err + captured.out).splitlines()
            if line.strip().startswith("- [")]


def test_a_missing_role_is_rejected(tmp_path, capsys):
    root = _write_tree(tmp_path)
    (root / "agents" / "reviewer.md").unlink()
    assert "AGENT_ROLE_MISSING" in _codes(root, capsys)


def test_an_unknown_role_file_is_rejected(tmp_path, capsys):
    root = _write_tree(tmp_path)
    (root / "agents" / "deployer.md").write_text(
        "---\nname: deployer\ndescription: x\ntools: Bash\n---\n", encoding="utf-8")
    assert "AGENT_ROLE_UNKNOWN" in _codes(root, capsys)


def test_a_read_only_role_granted_a_write_tool_is_rejected(tmp_path, capsys):
    """The failure this whole slice exists to catch."""
    root = _write_tree(tmp_path)
    path = root / "agents" / "researcher.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "tools: Read, Glob, Grep", "tools: Read, Glob, Grep, Write"), encoding="utf-8")
    codes = _codes(root, capsys)
    assert "AGENT_TOOLS_MISMATCH" in codes
    assert "AGENT_READ_ONLY_CONTRADICTED" in codes


def test_delegation_granted_to_a_non_coordinator_is_rejected(tmp_path, capsys):
    root = _write_tree(tmp_path)
    path = root / "agents" / "reviewer.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "tools: Read, Glob, Grep", "tools: Read, Glob, Grep, Agent"), encoding="utf-8")
    assert "AGENT_DELEGATION_TOOL_GRANTED" in _codes(root, capsys)


def test_a_network_tool_is_rejected(tmp_path, capsys):
    root = _write_tree(tmp_path)
    path = root / "agents" / "researcher.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "tools: Read, Glob, Grep", "tools: Read, Glob, Grep, WebFetch"), encoding="utf-8")
    assert "AGENT_NETWORK_TOOL_GRANTED" in _codes(root, capsys)


def test_an_unsupported_frontmatter_key_is_rejected(tmp_path, capsys):
    """`permissionMode` is not supported by plugin subagents.

    Rejected rather than ignored: a key that reads like a permission boundary and is
    not one is more dangerous than its absence, because a reviewer will count it.
    """
    root = _write_tree(tmp_path)
    path = root / "agents" / "researcher.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "tools: Read, Glob, Grep", "tools: Read, Glob, Grep\npermissionMode: readOnly"),
        encoding="utf-8")
    assert "AGENT_FIELD_UNSUPPORTED" in _codes(root, capsys)


def test_a_role_claiming_tool_enforcement_it_lacks_is_rejected(tmp_path, capsys):
    root = _write_tree(tmp_path)
    path = root / "agents" / "tester.md"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "enforcement: mixed", "enforcement: tool-allowlist"), encoding="utf-8")
    assert "AGENT_ENFORCEMENT_OVERCLAIMED" in _codes(root, capsys)


def test_a_missing_authority_marker_is_rejected(tmp_path, capsys):
    root = _write_tree(tmp_path)
    path = root / "agents" / "refiner.md"
    text = path.read_text(encoding="utf-8")
    start = text.index("<!-- agent-harness:policy")
    end = text.index("-->", start) + 3
    path.write_text(text[:start] + text[end:], encoding="utf-8")
    assert "AGENT_POLICY_MARKER_MISSING" in _codes(root, capsys)


# ---------------------------------------------------- 25-27. boundary with skills

def test_agents_are_no_longer_forbidden_in_the_installable_root():
    import validate_skills

    assert "agents" not in validate_skills.FORBIDDEN_COMPONENTS
    assert "hooks" in validate_skills.FORBIDDEN_COMPONENTS, (
        "lifting the agents ban must not have widened the rest of it"
    )


def test_the_drift_check_covers_agents():
    """PRIN-01 is about where workflow prose lives, not about a directory name."""
    source = (REPO_ROOT / "scripts" / "check_adapter_drift.py").read_text(encoding="utf-8")
    assert '("adapters", "agents")' in source


def test_the_adapter_ratio_is_enforced_now_that_skills_are_real():
    """It was a note while Skills were placeholders. M2 ended that."""
    source = (REPO_ROOT / "scripts" / "check_adapter_drift.py").read_text(encoding="utf-8")
    assert "ADAPTER_RATIO_EXCEEDED" in source
