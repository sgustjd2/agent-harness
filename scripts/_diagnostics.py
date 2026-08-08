"""Stable diagnostic codes. Development/CI only.

A jsonschema error message is written for humans and may be reworded by an upstream
release. Tests must not assert on it. This module maps a `jsonschema.ValidationError`
to one stable code, so the negative-scenario suite asserts on a contract that survives
both library upgrades and our own rewording.

The mapping is intentionally explicit rather than generic: a code should say what went
wrong in this project's terms ("the Codex skills path was an array") rather than in the
schema's terms ("type mismatch at $.skills").
"""

from __future__ import annotations

from _common import path_hygiene_issues

# Every code the M1 negative-scenario suite may assert.
CODES = {
    # manifest identity
    "PLUGIN_NAME_MISSING",
    "PLUGIN_NAME_NOT_KEBAB",
    "PLUGIN_DESCRIPTION_MISSING",
    "VERSION_MISSING",
    "VERSION_NOT_SEMVER",
    "VERSION_MISMATCH",
    # Codex skills path
    "CODEX_SKILLS_MISSING",
    "CODEX_SKILLS_NOT_STRING",
    "CODEX_SKILLS_PATH_INVALID",
    # path hygiene (from _common.path_hygiene_issues)
    "PATH_ABSOLUTE",
    "PATH_PARENT_TRAVERSAL",
    "PATH_DRIVE_QUALIFIED",
    "PATH_UNC",
    "PATH_TILDE",
    "PATH_ENV_INTERPOLATION",
    "PATH_EMPTY",
    # marketplace catalogs
    "MARKETPLACE_EMPTY",
    "MARKETPLACE_NAME_MISSING",
    "CLAUDE_SOURCE_INVALID",
    "CLAUDE_OWNER_MISSING",
    "OPENAI_SOURCE_INVALID",
    "OPENAI_INTERFACE_MISSING",
    "OPENAI_POLICY_MISSING",
    "OPENAI_POLICY_INSTALLATION_MISSING",
    "OPENAI_POLICY_INSTALLATION_INVALID",
    "OPENAI_POLICY_AUTH_MISSING",
    "OPENAI_POLICY_AUTH_INVALID",
    "OPENAI_POLICY_UNKNOWN_FIELD",
    "OPENAI_CATEGORY_MISSING",
    "OPENAI_SOURCE_TYPE_INVALID",
    "OPENAI_SOURCE_TYPE_MISSING",
    "OPENAI_SOURCE_PATH_MISSING",
    "OPENAI_SOURCE_PATH_INVALID",
    "OPENAI_SOURCE_UNKNOWN_FIELD",
    "CANONICAL_FIELD_MISSING",
    "CATALOG_DRIFT",
    # skills
    "SKILL_DESCRIPTION_MISSING",
    "SKILL_NAME_MISSING",
    "SKILL_NAME_MISMATCH",
    "SKILL_FRONTMATTER_UNSUPPORTED",
    "SKILL_FRONTMATTER_MALFORMED",
    "SKILL_FRONTMATTER_ABSENT",
    "POLICY_FILE_MISSING",
    "POLICY_IMPLICIT_INVOCATION_ENABLED",
    # plugin-root boundary
    "PRODUCTION_SKILL_IN_ROOT",
    "PRODUCTION_HOOK_IN_ROOT",
    "FORBIDDEN_COMPONENT_IN_ROOT",
    "SYMLINK_ESCAPE",
    "PATH_ESCAPES_PLUGIN_ROOT",
    # documentation hygiene
    "UNDOCUMENTED_INSTALL_COMMAND",
    # generic
    "JSON_INVALID",
    "FILE_MISSING",
    "SCHEMA_VIOLATION",
    "UNEXPECTED_FIELD",
}

# (top-level context, field name) -> code, for `required` violations.
_REQUIRED = {
    ("claude-plugin", "name"): "PLUGIN_NAME_MISSING",
    ("claude-plugin", "description"): "PLUGIN_DESCRIPTION_MISSING",
    ("claude-plugin", "version"): "VERSION_MISSING",
    ("codex-plugin", "name"): "PLUGIN_NAME_MISSING",
    ("codex-plugin", "description"): "PLUGIN_DESCRIPTION_MISSING",
    ("codex-plugin", "version"): "VERSION_MISSING",
    ("codex-plugin", "skills"): "CODEX_SKILLS_MISSING",
    ("claude-marketplace", "name"): "MARKETPLACE_NAME_MISSING",
    ("claude-marketplace", "owner"): "CLAUDE_OWNER_MISSING",
    ("openai-marketplace", "name"): "MARKETPLACE_NAME_MISSING",
    ("openai-marketplace", "interface"): "OPENAI_INTERFACE_MISSING",
    ("openai-marketplace", "policy"): "OPENAI_POLICY_MISSING",
    ("openai-marketplace", "installation"): "OPENAI_POLICY_INSTALLATION_MISSING",
    ("openai-marketplace", "authentication"): "OPENAI_POLICY_AUTH_MISSING",
    ("openai-marketplace", "category"): "OPENAI_CATEGORY_MISSING",
    ("openai-marketplace", "path"): "OPENAI_SOURCE_PATH_MISSING",
}

# The documented OpenAI local-source object form. Both this and a plain string path are
# Official-Documented; Candidate C emits this one by local choice.
_SOURCE_OBJECT_KEYS = {"source", "path"}
_SOURCE_TYPES = {"local"}


def _classify_openai_source(instance) -> str:
    """Name the authoring mistake in an OpenAI `source` value.

    The schema models `source` as a `oneOf` over the two documented local forms, so
    jsonschema reports only the enclosing `oneOf` failure; the useful reason sits in
    `error.context`, ordered by internals this module deliberately does not depend on.
    Dispatching on the instance shape keeps each mistake mapped to its own stable code.
    """
    if isinstance(instance, str):
        issues = path_hygiene_issues(instance)
        return issues[0] if issues else "OPENAI_SOURCE_INVALID"

    if isinstance(instance, dict):
        if set(instance) - _SOURCE_OBJECT_KEYS:
            # Same failure mode as DEF-001's invented `policy.install`: an unknown key
            # must break the build rather than be tolerated or quietly repaired.
            return "OPENAI_SOURCE_UNKNOWN_FIELD"
        if "source" not in instance:
            return "OPENAI_SOURCE_TYPE_MISSING"
        if instance["source"] not in _SOURCE_TYPES:
            return "OPENAI_SOURCE_TYPE_INVALID"
        if "path" not in instance:
            return "OPENAI_SOURCE_PATH_MISSING"
        if not isinstance(instance["path"], str):
            return "OPENAI_SOURCE_PATH_INVALID"
        issues = path_hygiene_issues(instance["path"])
        return issues[0] if issues else "OPENAI_SOURCE_PATH_INVALID"

    # Neither documented form: array, null, number, boolean.
    return "OPENAI_SOURCE_INVALID"


def classify(error, context: str) -> str:
    """Map one jsonschema ValidationError to a stable code.

    `context` names the schema in play: claude-plugin, codex-plugin,
    claude-marketplace, openai-marketplace, or canonical-marketplace.
    """
    path = list(error.absolute_path)
    keyword = error.validator
    field = path[-1] if path else None

    if keyword == "required":
        missing = _missing_property(error)
        if context == "canonical-marketplace":
            return "CANONICAL_FIELD_MISSING"
        mapped = _REQUIRED.get((context, missing))
        if mapped:
            return mapped
        return "SCHEMA_VIOLATION"

    if keyword == "minItems" and "plugins" in path:
        return "MARKETPLACE_EMPTY"

    if keyword == "additionalProperties":
        # A stray key inside the OpenAI policy object gets its own code: this is the
        # exact shape of DEF-001 (the invented `policy.install`), and it must be
        # distinguishable from any other unexpected-field error.
        if context == "openai-marketplace" and path and path[-1] == "policy":
            return "OPENAI_POLICY_UNKNOWN_FIELD"
        return "UNEXPECTED_FIELD"

    if field == "skills" and context == "codex-plugin":
        if keyword == "type":
            return "CODEX_SKILLS_NOT_STRING"
        if keyword == "pattern":
            # Prefer the specific hygiene reason over a generic pattern failure:
            # "absolute path" is actionable, "did not match ^\\./..." is not.
            issues = path_hygiene_issues(str(error.instance))
            return issues[0] if issues else "CODEX_SKILLS_PATH_INVALID"

    if field == "source":
        if keyword == "oneOf" and context == "openai-marketplace":
            return _classify_openai_source(error.instance)
        if keyword == "pattern":
            issues = path_hygiene_issues(str(error.instance))
            if issues:
                return issues[0]
            return ("CLAUDE_SOURCE_INVALID" if context == "claude-marketplace"
                    else "OPENAI_SOURCE_INVALID")
        if keyword in ("type", "required"):
            return ("CLAUDE_SOURCE_INVALID" if context == "claude-marketplace"
                    else "OPENAI_SOURCE_INVALID")

    if field == "source_path" and keyword == "pattern":
        issues = path_hygiene_issues(str(error.instance))
        return issues[0] if issues else "CANONICAL_FIELD_MISSING"

    if field == "version" and keyword == "pattern":
        return "VERSION_NOT_SEMVER"

    if field == "name" and keyword == "pattern":
        return "PLUGIN_NAME_NOT_KEBAB"

    if field == "installation" and keyword in ("enum", "type"):
        return "OPENAI_POLICY_INSTALLATION_INVALID"
    if field == "authentication" and keyword in ("enum", "type"):
        # Covers "none", "NONE", "on_install" and any non-string value.
        return "OPENAI_POLICY_AUTH_INVALID"
    if field == "source" and keyword == "enum":
        return "OPENAI_SOURCE_TYPE_INVALID"

    return "SCHEMA_VIOLATION"


def _missing_property(error) -> str:
    """Extract the property name from a `required` error message."""
    message = error.message
    if "'" in message:
        return message.split("'")[1]
    return ""


def classify_all(errors, context: str) -> list[str]:
    return [classify(e, context) for e in errors]
