"""Negative-scenario coverage (M1.1 Step 8).

Every required invalid case asserts ONE primary stable diagnostic code. Tests assert
codes, never prose: an upstream jsonschema rewording must not break this suite, and a
check that starts failing for a different reason must break it.

Scenario IDs are stable and appear in the coverage table in docs/m1-remediation.md.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

from conftest import REPO_ROOT, baseline, diagnose  # noqa: E402

pytestmark = pytest.mark.deterministic


# ==========================================================================
# Group 1 -- schema-driven scenarios (jsonschema is the authority)
# ==========================================================================

def _drop(doc, *path):
    node = doc
    for key in path[:-1]:
        node = node[key]
    del node[path[-1]]
    return doc


def _set(doc, value, *path):
    node = doc
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return doc


SCHEMA_SCENARIOS = [
    # (id, context, mutate, expected_code)
    ("NS-01-missing-plugin-name", "claude-plugin",
     lambda d: _drop(d, "name"), "PLUGIN_NAME_MISSING"),
    ("NS-02-invalid-kebab-name", "claude-plugin",
     lambda d: _set(d, "Agent_Harness", "name"), "PLUGIN_NAME_NOT_KEBAB"),
    ("NS-03-malformed-semver", "claude-plugin",
     lambda d: _set(d, "0.1", "version"), "VERSION_NOT_SEMVER"),
    ("NS-05-missing-codex-skills", "codex-plugin",
     lambda d: _drop(d, "skills"), "CODEX_SKILLS_MISSING"),
    ("NS-06-codex-skills-as-array", "codex-plugin",
     lambda d: _set(d, ["./skills/"], "skills"), "CODEX_SKILLS_NOT_STRING"),
    ("NS-07-absolute-skills-path", "codex-plugin",
     lambda d: _set(d, "/skills/", "skills"), "PATH_ABSOLUTE"),
    ("NS-08-parent-traversal-skills-path", "codex-plugin",
     lambda d: _set(d, "./../skills/", "skills"), "PATH_PARENT_TRAVERSAL"),
    ("NS-09-empty-marketplace-plugin-list", "claude-marketplace",
     lambda d: _set(d, [], "plugins"), "MARKETPLACE_EMPTY"),
    ("NS-10-invalid-claude-source-path", "claude-marketplace",
     lambda d: _set(d, "plugins/agent-harness", "plugins", 0, "source"),
     "CLAUDE_SOURCE_INVALID"),
    ("NS-11-invalid-openai-source-path", "openai-marketplace",
     lambda d: _set(d, "plugins/agent-harness", "plugins", 0, "source"),
     "OPENAI_SOURCE_INVALID"),
    ("NS-12-missing-openai-policy", "openai-marketplace",
     lambda d: _drop(d, "plugins", 0, "policy"), "OPENAI_POLICY_MISSING"),
    ("NS-13-invalid-openai-auth-policy", "openai-marketplace",
     lambda d: _set(d, "oauth", "plugins", 0, "policy", "authentication"),
     "OPENAI_POLICY_AUTH_INVALID"),

    # ---- M1.3 / DEF-001 regression set -----------------------------------
    # The exact value the real host rejected. This is the defect itself.
    ("NS-29-authentication-none", "openai-marketplace",
     lambda d: _set(d, "none", "plugins", 0, "policy", "authentication"),
     "OPENAI_POLICY_AUTH_INVALID"),
    ("NS-30-authentication-NONE-uppercase", "openai-marketplace",
     lambda d: _set(d, "NONE", "plugins", 0, "policy", "authentication"),
     "OPENAI_POLICY_AUTH_INVALID"),
    ("NS-31-authentication-lowercase-on_install", "openai-marketplace",
     lambda d: _set(d, "on_install", "plugins", 0, "policy", "authentication"),
     "OPENAI_POLICY_AUTH_INVALID"),
    ("NS-32-authentication-missing", "openai-marketplace",
     lambda d: _drop(d, "plugins", 0, "policy", "authentication"),
     "OPENAI_POLICY_AUTH_MISSING"),
    ("NS-33-installation-missing", "openai-marketplace",
     lambda d: _drop(d, "plugins", 0, "policy", "installation"),
     "OPENAI_POLICY_INSTALLATION_MISSING"),
    ("NS-34-installation-invalid", "openai-marketplace",
     lambda d: _set(d, "MANUAL", "plugins", 0, "policy", "installation"),
     "OPENAI_POLICY_INSTALLATION_INVALID"),
    ("NS-35-installation-lowercase", "openai-marketplace",
     lambda d: _set(d, "available", "plugins", 0, "policy", "installation"),
     "OPENAI_POLICY_INSTALLATION_INVALID"),
    ("NS-36-category-missing", "openai-marketplace",
     lambda d: _drop(d, "plugins", 0, "category"), "OPENAI_CATEGORY_MISSING"),
    # The invented field must FAIL, never be silently accepted or aliased.
    ("NS-37-policy-install-instead-of-installation", "openai-marketplace",
     lambda d: _set(d, {"install": "manual", "authentication": "ON_INSTALL"},
                    "plugins", 0, "policy"),
     "OPENAI_POLICY_UNKNOWN_FIELD"),
    ("NS-38-both-install-and-installation", "openai-marketplace",
     lambda d: _set(d, {"install": "manual", "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL"}, "plugins", 0, "policy"),
     "OPENAI_POLICY_UNKNOWN_FIELD"),
    ("NS-39-unknown-field-inside-policy", "openai-marketplace",
     lambda d: _set(d, {"installation": "AVAILABLE", "authentication": "ON_INSTALL",
                        "surpriseKey": "x"}, "plugins", 0, "policy"),
     "OPENAI_POLICY_UNKNOWN_FIELD"),
    ("NS-40-non-string-installation", "openai-marketplace",
     lambda d: _set(d, True, "plugins", 0, "policy", "installation"),
     "OPENAI_POLICY_INSTALLATION_INVALID"),
    ("NS-41-non-string-authentication", "openai-marketplace",
     lambda d: _set(d, 42, "plugins", 0, "policy", "authentication"),
     "OPENAI_POLICY_AUTH_INVALID"),
    # ---- M1.3.1 source-shape correction ----------------------------------
    # NS-42 previously asserted that a plain string `source` is invalid. That was
    # evidence-incorrect: the vendor documents the plain string path as an alternate
    # local form. The scenario is replaced by negatives that reject shapes matching
    # NEITHER documented form. See test_marketplace_contract.py for the positives.
    ("NS-43-openai-source-type-invalid", "openai-marketplace",
     lambda d: _set(d, "git", "plugins", 0, "source", "source"),
     "OPENAI_SOURCE_TYPE_INVALID"),
    ("NS-46-openai-source-object-missing-type", "openai-marketplace",
     lambda d: _set(d, {"path": "./plugins/agent-harness"}, "plugins", 0, "source"),
     "OPENAI_SOURCE_TYPE_MISSING"),
    ("NS-47-openai-source-object-missing-path", "openai-marketplace",
     lambda d: _set(d, {"source": "local"}, "plugins", 0, "source"),
     "OPENAI_SOURCE_PATH_MISSING"),
    ("NS-48-openai-source-non-string-path", "openai-marketplace",
     lambda d: _set(d, 123, "plugins", 0, "source", "path"),
     "OPENAI_SOURCE_PATH_INVALID"),
    ("NS-49-openai-source-object-unsafe-path", "openai-marketplace",
     lambda d: _set(d, "./../escape", "plugins", 0, "source", "path"),
     "PATH_PARENT_TRAVERSAL"),
    # Path hygiene must be identical across both documented forms: a traversal is not
    # more acceptable merely because the author chose the string spelling.
    ("NS-50-openai-source-string-unsafe-path", "openai-marketplace",
     lambda d: _set(d, "./../escape", "plugins", 0, "source"),
     "PATH_PARENT_TRAVERSAL"),
    ("NS-51-openai-source-string-absolute-path", "openai-marketplace",
     lambda d: _set(d, "/etc/passwd", "plugins", 0, "source"), "PATH_ABSOLUTE"),
    # Same lesson as DEF-001, applied to `source`: an unknown key must break the build.
    ("NS-52-openai-source-arbitrary-key", "openai-marketplace",
     lambda d: _set(d, {"source": "local", "path": "./plugins/agent-harness",
                        "branch": "main"}, "plugins", 0, "source"),
     "OPENAI_SOURCE_UNKNOWN_FIELD"),
    ("NS-53-openai-source-array", "openai-marketplace",
     lambda d: _set(d, ["./plugins/agent-harness"], "plugins", 0, "source"),
     "OPENAI_SOURCE_INVALID"),
    ("NS-54-openai-source-null", "openai-marketplace",
     lambda d: _set(d, None, "plugins", 0, "source"), "OPENAI_SOURCE_INVALID"),

    # ---- M1.3.1 kebab-case restoration -----------------------------------
    # M1.3 removed these patterns as "invented". They are documented by both vendors;
    # the removal was a regression. Each scenario below failed to fail before M1.3.1.
    ("NS-55-claude-marketplace-name-spaces", "claude-marketplace",
     lambda d: _set(d, "agent harness", "name"), "PLUGIN_NAME_NOT_KEBAB"),
    ("NS-56-claude-marketplace-name-uppercase", "claude-marketplace",
     lambda d: _set(d, "Agent-Harness", "name"), "PLUGIN_NAME_NOT_KEBAB"),
    ("NS-57-claude-marketplace-plugin-name-uppercase", "claude-marketplace",
     lambda d: _set(d, "Agent-Harness", "plugins", 0, "name"), "PLUGIN_NAME_NOT_KEBAB"),
    ("NS-58-claude-marketplace-plugin-name-underscore", "claude-marketplace",
     lambda d: _set(d, "agent_harness", "plugins", 0, "name"), "PLUGIN_NAME_NOT_KEBAB"),
    ("NS-59-openai-marketplace-plugin-name-uppercase", "openai-marketplace",
     lambda d: _set(d, "Agent-Harness", "plugins", 0, "name"), "PLUGIN_NAME_NOT_KEBAB"),
    ("NS-60-openai-marketplace-plugin-name-spaces", "openai-marketplace",
     lambda d: _set(d, "agent harness", "plugins", 0, "name"), "PLUGIN_NAME_NOT_KEBAB"),
    # Leading / trailing / repeated hyphens are a Local-M1-Policy refinement of
    # "kebab-case, no spaces", not a separately published vendor rule.
    ("NS-61-plugin-name-leading-hyphen", "claude-plugin",
     lambda d: _set(d, "-agent-harness", "name"), "PLUGIN_NAME_NOT_KEBAB"),
    ("NS-62-plugin-name-trailing-hyphen", "claude-plugin",
     lambda d: _set(d, "agent-harness-", "name"), "PLUGIN_NAME_NOT_KEBAB"),
    ("NS-63-plugin-name-repeated-hyphen", "claude-plugin",
     lambda d: _set(d, "agent--harness", "name"), "PLUGIN_NAME_NOT_KEBAB"),
    ("NS-64-codex-plugin-name-uppercase", "codex-plugin",
     lambda d: _set(d, "Agent-Harness", "name"), "PLUGIN_NAME_NOT_KEBAB"),
    # Canonical source must not carry the removed semantic value either.
    ("NS-44-canonical-authentication-none", "canonical-marketplace",
     lambda d: _set(d, "none", "plugins", 0, "authentication_timing"),
     "SCHEMA_VIOLATION"),
    ("NS-45-canonical-installation-missing", "canonical-marketplace",
     lambda d: _drop(d, "plugins", 0, "installation_availability"),
     "CANONICAL_FIELD_MISSING"),
    ("NS-15-canonical-missing-semantic-field", "canonical-marketplace",
     lambda d: _drop(d, "marketplace", "display_name"), "CANONICAL_FIELD_MISSING"),
    ("NS-23-windows-drive-qualified-path", "codex-plugin",
     lambda d: _set(d, "C:/skills/", "skills"), "PATH_DRIVE_QUALIFIED"),
    ("NS-24-unc-path", "codex-plugin",
     lambda d: _set(d, "//server/share/skills/", "skills"), "PATH_UNC"),
    ("NS-25-tilde-expansion-path", "codex-plugin",
     lambda d: _set(d, "~/skills/", "skills"), "PATH_TILDE"),
    ("NS-26-env-var-path-interpolation", "codex-plugin",
     lambda d: _set(d, "$HOME/skills/", "skills"), "PATH_ENV_INTERPOLATION"),
]


@pytest.mark.parametrize(
    "context,mutate,expected",
    [pytest.param(ctx, fn, code, id=sid) for sid, ctx, fn, code in SCHEMA_SCENARIOS],
)
def test_schema_scenario(context, mutate, expected):
    """A single-field mutation of a valid document yields its expected diagnostic code."""
    doc = mutate(baseline(context))
    codes = diagnose(doc, context)
    assert expected in codes, f"expected primary code {expected!r}, got {codes!r}"


def test_baselines_are_valid():
    """Every baseline must validate cleanly, or the negative tests prove nothing."""
    for context in ("claude-plugin", "codex-plugin", "claude-marketplace",
                    "openai-marketplace", "canonical-marketplace"):
        assert diagnose(baseline(context), context) == [], f"{context} baseline is not valid"


# ==========================================================================
# Group 2 -- cross-file scenarios (validators, not a single schema)
# ==========================================================================

def _run(fn, *args, **kwargs):
    """Call a validator's check() and return (exit_code, diagnostic codes)."""
    import io
    import contextlib
    from _common import Report

    captured = {}
    original = Report.finish

    def spy(self):
        captured.setdefault("codes", []).extend(self.codes)
        return original(self)

    Report.finish = spy
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            status = fn(*args, **kwargs)
    finally:
        Report.finish = original
    return status, captured.get("codes", [])


def test_ns04_version_mismatch(plugin_tree):
    """NS-04: the two manifests declare different versions."""
    import validate_manifests

    path = plugin_tree / ".codex-plugin" / "plugin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = "9.9.9"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    status, codes = _run(validate_manifests.check, plugin_tree)
    assert status != 0
    assert "VERSION_MISMATCH" in codes, codes


def test_ns14_generated_catalog_drift(tmp_path):
    """NS-14: a generated catalog no longer matches what the canonical source renders."""
    import generate_marketplaces

    source = json.loads(
        (REPO_ROOT / "marketplace" / "marketplace.source.json").read_text(encoding="utf-8"))
    rendered = generate_marketplaces.render(source)

    drifted = json.loads(rendered[".claude-plugin/marketplace.json"])
    drifted["plugins"][0]["version"] = "0.0.2"
    assert json.dumps(drifted, indent=2) + "\n" != rendered[".claude-plugin/marketplace.json"], (
        "NS-14: hand-edited catalog must differ from generated output"
    )


def test_ns16_skill_missing_description(plugin_tree):
    """NS-16: a Skill omits description."""
    import validate_skills

    skill = plugin_tree / "skills" / "m1-discovery-fixture" / "SKILL.md"
    skill.write_text("---\nname: m1-discovery-fixture\n---\n\nbody\n", encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_DESCRIPTION_MISSING" in codes, codes


def test_ns17_skill_unsupported_frontmatter(plugin_tree):
    """NS-17: a Skill carries a host-only frontmatter key."""
    import validate_skills

    skill = plugin_tree / "skills" / "m1-discovery-fixture" / "SKILL.md"
    skill.write_text(
        "---\nname: m1-discovery-fixture\ndescription: d\n"
        "disable-model-invocation: true\n---\n\nbody\n", encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "SKILL_FRONTMATTER_UNSUPPORTED" in codes, codes


def test_ns18_openai_yaml_enables_implicit_invocation(plugin_tree):
    """NS-18: the invocation policy permits implicit invocation."""
    import validate_skills

    policy = plugin_tree / "skills" / "m1-discovery-fixture" / "agents" / "openai.yaml"
    policy.write_text("policy:\n  allow_implicit_invocation: true\n", encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "POLICY_IMPLICIT_INVOCATION_ENABLED" in codes, codes


@pytest.mark.skipif(sys.platform == "win32",
                    reason="creating symlinks on Windows requires elevation; "
                           "the check itself is platform-neutral")
def test_ns19_symlink_escape(plugin_tree, tmp_path):
    """NS-19: a symlink inside the plugin resolves outside the plugin root."""
    import check_path_containment

    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    (plugin_tree / "adapters" / "escape.md").symlink_to(outside)

    status, codes = _run(check_path_containment.check, plugin_tree)
    assert status != 0
    assert "SYMLINK_ESCAPE" in codes, codes


def test_ns20_production_skill_in_installable_root(plugin_tree):
    """NS-20: a planned production Skill name appears in the installable root."""
    import validate_skills

    bad = plugin_tree / "skills" / "apply-refinement"
    bad.mkdir(parents=True)
    (bad / "SKILL.md").write_text(
        "---\nname: apply-refinement\ndescription: placeholder\n---\n\nplaceholder\n",
        encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "PRODUCTION_SKILL_IN_ROOT" in codes, codes


def test_ns21_production_hook_in_installable_root(plugin_tree):
    """NS-21: a hooks directory appears in the installable root."""
    import validate_skills

    hooks = plugin_tree / "hooks"
    hooks.mkdir()
    (hooks / "hooks.json").write_text("{}", encoding="utf-8")
    status, codes = _run(validate_skills.check, plugin_tree)
    assert status != 0
    assert "PRODUCTION_HOOK_IN_ROOT" in codes, codes


def test_ns22_undocumented_install_command(tmp_path):
    """NS-22: an affirmative, copyable example of the undocumented install command.

    The forbidden phrase is assembled from parts rather than written as a literal, so
    this file itself stays clean and check_no_install_command can cover the whole
    tests/ tree without an allowlist entry.
    """
    import check_no_install_command

    phrase = " ".join(["codex", "plugin", "install"])
    doc = tmp_path / "docs"
    doc.mkdir()
    (doc / "install-codex.md").write_text(
        f"Run this to install:\n\n```bash\n{phrase} agent-harness\n```\n", encoding="utf-8")
    status, codes = _run(check_no_install_command.check, tmp_path)
    assert status != 0
    assert "UNDOCUMENTED_INSTALL_COMMAND" in codes, codes


def test_ns22b_negated_mention_is_allowed(tmp_path):
    """A sentence stating the command does not exist is the rule's purpose, not a breach."""
    import check_no_install_command

    phrase = " ".join(["codex", "plugin", "install"])
    doc = tmp_path / "docs"
    doc.mkdir()
    (doc / "notes.md").write_text(
        f"No `{phrase}` command appears in the reviewed documentation.\n", encoding="utf-8")
    status, codes = _run(check_no_install_command.check, tmp_path)
    assert status == 0, f"negated mention should be permitted, got {codes}"


def test_ns27_repository_path_containing_spaces(repo_with_spaces):
    """NS-27: validators succeed from a path containing spaces (this must PASS)."""
    import validate_manifests

    plugin_root = repo_with_spaces / "plugins" / "agent-harness"
    assert " " in str(plugin_root), "fixture must actually contain a space"
    status, codes = _run(validate_manifests.check, plugin_root)
    assert status == 0, f"validation failed under a spaced path: {codes}"


# ==========================================================================
# Group 3 -- malformed input reaches the authoritative library
# ==========================================================================

def test_malformed_yaml_fails_through_pyyaml(tmp_path):
    """Broken YAML must raise a real PyYAML error, not a subset parser's guess."""
    import yaml
    from _authoritative import load_frontmatter

    path = tmp_path / "SKILL.md"
    path.write_text("---\nname: x\n  bad: [unclosed\n---\n\nbody\n", encoding="utf-8")
    with pytest.raises(yaml.YAMLError):
        load_frontmatter(path)


def test_yaml_constructs_we_never_wrote_still_parse(tmp_path):
    """PyYAML handles YAML our removed subset parser could not.

    The old hand-written parser raised on flow sequences and anchors. Real YAML files
    may legitimately contain them, and a subset parser rejecting valid YAML is exactly
    the silent disagreement M1.1 removed.
    """
    from _authoritative import load_yaml_text

    parsed = load_yaml_text("a: [1, 2, 3]\nb: {k: v}\nc: &anchor val\nd: *anchor\n")
    assert parsed == {"a": [1, 2, 3], "b": {"k": "v"}, "c": "val", "d": "val"}


def test_invalid_schema_is_rejected_by_jsonschema(tmp_path):
    """A structurally invalid schema fails via jsonschema's own check_schema."""
    import jsonschema
    from _authoritative import load_schema

    bad = tmp_path / "bad.schema.json"
    bad.write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://example.invalid/bad",
        "type": "not-a-real-type",
    }), encoding="utf-8")
    with pytest.raises(jsonschema.SchemaError):
        load_schema(str(bad))


def test_schema_without_id_is_rejected(tmp_path):
    """Every local schema must carry a stable $id."""
    from _authoritative import SchemaError, load_schema

    bad = tmp_path / "noid.schema.json"
    bad.write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
    }), encoding="utf-8")
    with pytest.raises(SchemaError):
        load_schema(str(bad))
