"""M4 slice 1 — the optional Codex agent TOML templates (FR-021).

These are the only files in the repository designed to be copied **out** of it, into a
user's `.codex/agents/`. Everything else either ships inside the plugin or stays here.

That changes what the tests are for. A defect in a Skill is a defect in this repository;
a defect in a template is a defect that lands in somebody else's project and changes the
permissions of every Codex session they run afterwards (THR-015).
"""

from __future__ import annotations

import pathlib
import sys
import tomllib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_agent_templates as vat  # noqa: E402
from _common import (  # noqa: E402
    ALLOWED_WRITE_PATH_ROOTS,
    FORBIDDEN_WRITE_PATH_PREFIXES,
    PLUGIN_AGENT_ROLES,
    PLUGIN_ROOT,
    ROLE_TOOLS,
)

TEMPLATES = PLUGIN_ROOT / "adapters" / "codex" / "agent-templates"


def _load(role: str) -> dict:
    return tomllib.loads((TEMPLATES / f"{role}.toml").read_text(encoding="utf-8"))


# -------------------------------------------------- 1-4. the six roles, both hosts

def test_every_role_has_a_template():
    assert sorted(p.stem for p in TEMPLATES.glob("*.toml")) == sorted(PLUGIN_AGENT_ROLES)


def test_the_two_hosts_offer_the_same_roles():
    """MET-003 parity is measured on this. A role on one host only is the defect."""
    claude = {p.stem for p in (PLUGIN_ROOT / "agents").glob("*.md")}
    codex = {p.stem for p in TEMPLATES.glob("*.toml")}
    assert claude == codex


def test_the_shipped_templates_validate():
    assert vat.check() == 0


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
@pytest.mark.parametrize("field", ["name", "description", "developer_instructions"])
def test_required_codex_fields_are_present(role, field):
    assert _load(role)[field]


# ----------------------------------------------- 5-8. sandbox mode, where fixed

@pytest.mark.parametrize("role", ["researcher", "reviewer"])
def test_read_only_roles_declare_a_read_only_sandbox(role):
    """On Claude these two are enforced by an absent tool. Codex has no such surface.

    The sandbox mode is the nearest equivalent, and it is the entire reason a user would
    choose to install one of these templates at all.
    """
    assert _load(role)["sandbox_mode"] == "read-only"


def test_the_tester_is_workspace_write_and_no_wider():
    """It runs the project's gates, so read-only would break it. Never wider than that."""
    assert _load("tester")["sandbox_mode"] == "workspace-write"


@pytest.mark.parametrize("role", ["coordinator", "implementer", "refiner"])
def test_roles_without_a_fixed_mode_do_not_invent_one(role):
    """The PRD fixes a sandbox mode for three roles. Inventing one for the others would
    make a session default look like a reviewed constraint, and a reviewer counts it."""
    assert "sandbox_mode" not in _load(role)


def test_no_template_grants_full_access():
    """One line in a bundled file is all THR-015 needs."""
    assert "danger-full-access" not in vat.ALLOWED_SANDBOX_MODES
    for path in TEMPLATES.glob("*.toml"):
        assert "danger-full-access" not in path.read_text(encoding="utf-8")


# ------------------------------------------- 9-13. nothing installs them, ever

@pytest.mark.parametrize("prefix", [".codex/", ".claude/"])
def test_host_agent_directories_are_forbidden_write_roots(prefix):
    """SEC-18 / THR-015. A Skill that could write a host agent definition could widen
    its own authority for every later session, and the user would find out from a diff."""
    assert prefix in FORBIDDEN_WRITE_PATH_PREFIXES


@pytest.mark.parametrize("skill,roots", ALLOWED_WRITE_PATH_ROOTS.items())
def test_no_skill_declares_a_host_agent_path(skill, roots):
    for root in roots:
        assert not root.startswith((".codex", ".claude/"))


def test_no_skill_body_mentions_copying_a_template():
    """FR-021 rules 3 and 6: never silently, and never without approval.

    The strongest form of that guarantee available right now is that no Skill has the
    capability at all -- a canonical Skill cannot locate a sibling directory while
    Q-IMPL-003 is open, so the copy is a documented manual step instead.
    """
    offenders = [p.relative_to(REPO_ROOT).as_posix()
                 for p in (PLUGIN_ROOT / "skills").rglob("*.md")
                 if "agent-templates" in p.read_text(encoding="utf-8")]
    assert not offenders, offenders


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_each_template_says_nothing_installs_it(role):
    text = (TEMPLATES / f"{role}.toml").read_text(encoding="utf-8").lower()
    assert "nothing installs this file" in text
    assert "copy it yourself" in text


@pytest.mark.parametrize("role", PLUGIN_AGENT_ROLES)
def test_each_template_names_its_removal_procedure(role):
    assert "removal:" in (TEMPLATES / f"{role}.toml").read_text(encoding="utf-8").lower()


# ------------------------------------------------------------ 14-19. negative cases

def _tree(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "plugin"
    target = root / vat.TEMPLATE_DIR
    target.mkdir(parents=True)
    for role in PLUGIN_AGENT_ROLES:
        (target / f"{role}.toml").write_text(
            (TEMPLATES / f"{role}.toml").read_text(encoding="utf-8"), encoding="utf-8")
    return root


def _codes(root: pathlib.Path, capsys) -> list[str]:
    vat.check(root)
    captured = capsys.readouterr()
    return [line.split("]")[0].lstrip(" -[")
            for line in (captured.err + captured.out).splitlines()
            if line.strip().startswith("- [")]


def test_a_missing_role_template_is_rejected(tmp_path, capsys):
    root = _tree(tmp_path)
    (root / vat.TEMPLATE_DIR / "refiner.toml").unlink()
    assert "TEMPLATE_ROLE_MISSING" in _codes(root, capsys)


def test_an_unknown_field_is_rejected(tmp_path, capsys):
    """A key Codex does not define either does nothing silently or does something
    nobody reviewed. Both are worse than its absence."""
    root = _tree(tmp_path)
    path = root / vat.TEMPLATE_DIR / "researcher.toml"
    path.write_text(path.read_text(encoding="utf-8") + '\nallowed_commands = "rm"\n',
                    encoding="utf-8")
    assert "TEMPLATE_FIELD_UNKNOWN" in _codes(root, capsys)


def test_full_access_is_rejected(tmp_path, capsys):
    root = _tree(tmp_path)
    path = root / vat.TEMPLATE_DIR / "researcher.toml"
    path.write_text(path.read_text(encoding="utf-8").replace(
        'sandbox_mode = "read-only"', 'sandbox_mode = "danger-full-access"'),
        encoding="utf-8")
    assert "TEMPLATE_SANDBOX_MODE_INVALID" in _codes(root, capsys)


def test_widening_a_read_only_role_is_rejected(tmp_path, capsys):
    """The quiet version of the same attack: a legal value, on the wrong role."""
    root = _tree(tmp_path)
    path = root / vat.TEMPLATE_DIR / "reviewer.toml"
    path.write_text(path.read_text(encoding="utf-8").replace(
        'sandbox_mode = "read-only"', 'sandbox_mode = "workspace-write"'),
        encoding="utf-8")
    assert "TEMPLATE_SANDBOX_MODE_WRONG" in _codes(root, capsys)


def test_a_user_scope_path_is_rejected(tmp_path, capsys):
    """SEC-17. A template that names the user's home directory is asking to be copied
    somewhere the project's git diff would never show."""
    root = _tree(tmp_path)
    path = root / vat.TEMPLATE_DIR / "coordinator.toml"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "Hold the state of a run.", "Write results to ~/.codex/agents/notes."),
        encoding="utf-8")
    assert "TEMPLATE_USER_SCOPE_PATH" in _codes(root, capsys)


def test_a_network_reference_is_rejected(tmp_path, capsys):
    root = _tree(tmp_path)
    path = root / vat.TEMPLATE_DIR / "tester.toml"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "Run the checks the project already defines.",
        "Fetch the checks from https://example.invalid/gates."), encoding="utf-8")
    assert "TEMPLATE_NETWORK_REFERENCE" in _codes(root, capsys)


# -------------------------------------------------- 20. the asymmetry stays visible

def test_the_claude_side_still_carries_a_tools_allowlist():
    """The templates are not a second enforcement mechanism; Codex has none to give.

    Claude constrains a role by withholding tools. Codex's plugin format defines no
    equivalent, so the template's sandbox mode is the closest available and it is coarser.
    Recording them as the same thing would overstate the Codex guarantee.
    """
    assert ROLE_TOOLS["researcher"] == ["Read", "Glob", "Grep"]
    assert "tools" not in _load("researcher")
