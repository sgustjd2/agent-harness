"""Positive contract tests for the corrected OpenAI marketplace (M1.3 / DEF-001).

The negative suite proves invalid shapes fail. These prove the *shipped* artifact
carries exactly the contract the official documentation defines, and that the invented
field is gone from every artifact a user or host could act on.

Structure is inspected as parsed JSON, not matched as raw text: a text match would pass
on a value buried in a comment.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from conftest import REPO_ROOT

pytestmark = pytest.mark.deterministic

OPENAI_CATALOG = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
CLAUDE_CATALOG = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CANONICAL = REPO_ROOT / "marketplace" / "marketplace.source.json"
GENERATOR = REPO_ROOT / "scripts" / "generate_marketplaces.py"
SCHEMA_DIR = REPO_ROOT / "plugins" / "agent-harness" / "core" / "schemas"


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- golden contract

def test_openai_catalog_carries_the_documented_contract():
    """Candidate C ships installation=AVAILABLE, authentication=ON_INSTALL, category=Productivity."""
    entry = _load(OPENAI_CATALOG)["plugins"][0]
    assert entry["policy"]["installation"] == "AVAILABLE"
    assert entry["policy"]["authentication"] == "ON_INSTALL"
    assert entry["category"] == "Productivity"


def test_openai_policy_has_exactly_the_two_documented_keys():
    """No extra key may creep into policy -- that is how DEF-001 shipped."""
    policy = _load(OPENAI_CATALOG)["plugins"][0]["policy"]
    assert set(policy) == {"installation", "authentication"}, (
        f"policy must contain exactly installation and authentication, got {sorted(policy)}"
    )


def test_openai_source_uses_the_object_form_by_local_choice():
    """Candidate C emits the object form.

    Both the object form and a plain string path are documented for local entries. This
    asserts a LOCAL ARCHITECTURE CHOICE -- one shape, deterministically derived from the
    canonical model -- not a vendor requirement. A string here would be valid for the
    vendor; it would just mean the generator stopped doing what this repository decided.
    """
    source = _load(OPENAI_CATALOG)["plugins"][0]["source"]
    assert isinstance(source, dict), f"source must be an object, got {type(source).__name__}"
    assert source == {"source": "local", "path": "./plugins/agent-harness"}


def test_openai_catalog_emits_on_install():
    """Candidate C selects the Official-Documented literal, never the host-observed one.

    ON_USE was accepted by codex-cli 0.146.0-alpha.9.2 but is not a documented
    cross-version literal, so generation must never reach for it by default.
    """
    assert _load(OPENAI_CATALOG)["plugins"][0]["policy"]["authentication"] == "ON_INSTALL"


# ------------------------------------------------- documented source forms (M1.3.1)

@pytest.mark.parametrize("source", [
    pytest.param({"source": "local", "path": "./plugins/agent-harness"}, id="object-form"),
    pytest.param("./plugins/agent-harness", id="plain-string-form"),
])
def test_both_documented_local_source_forms_validate(source):
    """The schema accepts BOTH documented local forms.

    M1.3 modelled `source` as object-only and recorded the string form as undocumented.
    That was wrong: the vendor documents the plain string path as an alternate local
    form. Rejecting it would make this repository's schema stricter than the contract it
    claims to model -- the same failure as inventing a field, in the opposite direction.
    """
    from conftest import baseline, diagnose

    doc = baseline("openai-marketplace")
    doc["plugins"][0]["source"] = source
    assert diagnose(doc, "openai-marketplace") == []


# ------------------------------------------------- identifier vs label (M1.3.1)

def test_plugin_identity_is_the_same_string_everywhere():
    """Identity parity: all four files must name the same plugin.

    This is the rule the OpenAI marketplace entry's kebab-case constraint DERIVES from
    (M1.4A). The marketplace page does not independently publish a case rule for a
    catalog entry name; what is documented is that the plugin MANIFEST name is a stable
    kebab-case identifier. The catalog entry inherits the constraint by having to name
    that same plugin -- so if parity went unchecked, the derivation would be a claim
    nothing enforces.
    """
    names = {
        "openai catalog": _load(OPENAI_CATALOG)["plugins"][0]["name"],
        "claude catalog": _load(CLAUDE_CATALOG)["plugins"][0]["name"],
        "claude manifest": _load(
            REPO_ROOT / "plugins/agent-harness/.claude-plugin/plugin.json")["name"],
        "codex manifest": _load(
            REPO_ROOT / "plugins/agent-harness/.codex-plugin/plugin.json")["name"],
        "canonical": _load(CANONICAL)["plugins"][0]["name"],
    }
    assert len(set(names.values())) == 1, f"plugin identity diverged: {names}"


@pytest.mark.parametrize("context,path", [
    ("claude-marketplace", ("name",)),
    ("claude-marketplace", ("plugins", 0, "name")),
    ("openai-marketplace", ("plugins", 0, "name")),
    ("claude-plugin", ("name",)),
    ("codex-plugin", ("name",)),
])
def test_kebab_identifiers_accept_valid_kebab(context, path):
    """The pattern must not reject legitimate kebab-case identifiers.

    Evidence differs per field and is recorded in docs/m1-defects.md: Official-Documented
    for the Claude marketplace names and both plugin manifest names; Local-M1-Policy
    derived from identity parity for the OpenAI marketplace entry name. The *behaviour*
    is identical, which is why one parametrized test covers them all.
    """
    from conftest import baseline, diagnose

    doc = baseline(context)
    target = doc
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = "agent-harness-2"
    assert diagnose(doc, context) == []


@pytest.mark.parametrize("value", ["Productivity", "Developer Tools", "AI & Agents"])
def test_category_is_free_form_not_an_identifier(value):
    """`category` is a display label on both hosts. Kebab-case there was an invention."""
    from conftest import baseline, diagnose

    for context in ("claude-marketplace", "openai-marketplace", "canonical-marketplace"):
        doc = baseline(context)
        doc["plugins"][0]["category"] = value
        assert diagnose(doc, context) == [], f"{context} rejected category {value!r}"


@pytest.mark.parametrize("value", ["Agent Harness", "AGENT HARNESS", "Agent Harness v2"])
def test_display_names_are_free_form_not_identifiers(value):
    """Human-facing labels take spaces and capitals; only identifiers are constrained."""
    from conftest import baseline, diagnose

    doc = baseline("openai-marketplace")
    doc["interface"]["displayName"] = value
    assert diagnose(doc, "openai-marketplace") == []

    doc = baseline("canonical-marketplace")
    doc["marketplace"]["display_name"] = value
    assert diagnose(doc, "canonical-marketplace") == []


def test_claude_catalog_has_no_openai_policy_fields():
    """Claude publishes no equivalent of the OpenAI policy fields.

    Emitting them into the Claude catalog would assert a contract Claude does not define
    -- the same class of error as DEF-001, in the other direction.
    """
    entry = _load(CLAUDE_CATALOG)["plugins"][0]
    assert "policy" not in entry
    assert "installation" not in entry
    assert "authentication" not in entry
    # Claude does document `category`, so it stays.
    assert entry["category"] == "Productivity"
    # Claude documents `source` as a string, not the OpenAI object form.
    assert isinstance(entry["source"], str)


def test_canonical_uses_semantic_concept_names_not_host_field_names():
    """Canonical names must not be confusable with either host's output fields."""
    entry = _load(CANONICAL)["plugins"][0]
    assert entry["installation_availability"] == "AVAILABLE"
    assert entry["authentication_timing"] == "ON_INSTALL"
    assert entry["category"] == "Productivity"
    # The host-shaped block must not reappear in the canonical model.
    assert "policy" not in entry, "canonical source must not carry a host-shaped policy block"


# ---------------------------------------------------------------- DEF-001 absence

# Files that may legitimately name the removed field, as historical evidence.
HISTORICAL_ALLOWLIST = {
    "docs/m1-defects.md",
    "docs/m1-experiments.md",
    "docs/m1-decisions.md",
    "docs/m1-remediation.md",
    "docs/compatibility.md",
    "docs/m1-traceability.md",
    "docs/m1-runbook.md",
    "CHANGELOG.md",
    "tests/test_negative_scenarios.py",   # asserts the invented field FAILS
    "tests/test_marketplace_contract.py",
}


def test_policy_install_is_absent_from_every_valid_artifact():
    """`policy.install` must not survive anywhere a host or user would act on it.

    Checked as parsed structure for JSON, and as text only for the generator and
    schemas, where the field name would appear in code rather than data.
    """
    # 1. canonical source -- structural
    canonical_entry = _load(CANONICAL)["plugins"][0]
    assert "install" not in canonical_entry
    assert "policy" not in canonical_entry

    # 2. generated OpenAI catalog -- structural
    assert "install" not in _load(OPENAI_CATALOG)["plugins"][0]["policy"]

    # 3. generator mapping -- the emitted key must be `installation`
    gen = GENERATOR.read_text(encoding="utf-8")
    assert '"installation"' in gen, "generator must emit the documented field name"
    assert '"install":' not in gen, "generator must not emit an `install` key"

    # 4. schemas -- the invented enum and field must be gone from the contract
    for name in ("openai-marketplace", "canonical-marketplace"):
        schema = _load(SCHEMA_DIR / f"{name}.schema.json")
        flat = json.dumps(schema)
        assert '"install"' not in flat.replace('"installation"', ""), (
            f"{name} still models an `install` field")


def test_authentication_none_is_absent_from_every_valid_artifact():
    """The exact value the real host rejected must not appear in any shipped artifact."""
    assert _load(OPENAI_CATALOG)["plugins"][0]["policy"]["authentication"] != "none"
    assert _load(CANONICAL)["plugins"][0]["authentication_timing"] != "none"

    schema = _load(SCHEMA_DIR / "openai-marketplace.schema.json")
    auth = (schema["properties"]["plugins"]["items"]["properties"]
            ["policy"]["properties"]["authentication"])
    assert "none" not in auth["enum"] and "NONE" not in auth["enum"], (
        f"authentication enum must not permit a none variant, got {auth['enum']}")


def test_no_user_facing_doc_presents_the_invented_field_as_valid():
    """Historical defect records may name it; user-facing metadata guidance may not."""
    offenders = []
    for path in sorted(REPO_ROOT.rglob("*.md")):
        if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in HISTORICAL_ALLOWLIST or rel == "docs/PRD.md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if '"install":' in text or "policy.install " in text:
            offenders.append(rel)
    assert not offenders, f"invented field presented as valid metadata in: {offenders}"


# ---------------------------------------------------------------- determinism

def test_generation_is_deterministic_and_matches_disk():
    """Rendering twice yields identical bytes, and disk matches the render."""
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import generate_marketplaces as gen

    source = _load(CANONICAL)
    first, second = gen.render(source), gen.render(source)
    assert first == second, "generation is not deterministic"

    for rel, text in first.items():
        on_disk = (REPO_ROOT / rel).read_bytes()
        assert on_disk == text.encode("utf-8"), (
            f"{rel} differs from generator output -- it must not be hand-edited")
        assert on_disk.endswith(b"\n") and not on_disk.endswith(b"\n\n"), (
            f"{rel} must end with exactly one newline")
        assert b"\r\n" not in on_disk, f"{rel} must use LF line endings"
