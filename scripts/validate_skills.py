#!/usr/bin/env python3
"""Validate Skill metadata and the installable-plugin Skill boundary.

Frontmatter is parsed by PyYAML (yaml.safe_load) after boundary extraction, so a
malformed block fails with a real YAML error rather than a subset parser's guess.

Boundary rules enforced here:
  - only Skills on the current milestone allowlist may exist in the installable root
    (M1.1 Step 7; widened one Skill at a time in M2 as each is actually implemented)
  - every still-unimplemented production Skill name is rejected
  - the compatibility fixture must keep implicit invocation disabled
  - no production hook directory in the installable root

Implemented production Skills additionally declare a machine-checkable safety contract
in their body. That contract is parsed as YAML from an explicit marker rather than
grepped out of prose: a read-only Skill's body legitimately contains sentences like
"it never runs commands", and a substring check cannot tell that apart from a promise
to do so. The marker is the claim; the prose is only for the reader.
"""

from __future__ import annotations

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _authoritative import load_frontmatter  # noqa: E402
from _common import (  # noqa: E402
    ALLOWED_SKILLS,
    ALLOWED_WRITE_PATH_ROOTS,
    DISCOVERY_FIXTURE_SKILL,
    FORBIDDEN_PRODUCTION_SKILLS,
    FORBIDDEN_WRITE_PATH_PREFIXES,
    IMPLEMENTED_PRODUCTION_SKILLS,
    IMPLICIT_INVOCATION_MUST_BE_OFF,
    PROFILES_REQUIRING_PATH_ROOTS,
    SKILL_PROFILE,
    SKILL_SAFETY_PROFILES,
    PLUGIN_ROOT,
    SKILL_FRONTMATTER_OPTIONAL,
    SKILL_FRONTMATTER_REQUIRED,
    FrontmatterError,
    Report,
    extract_policy_marker,
    path_hygiene_issues,
    main,
    skill_dirs,
)

DESCRIPTION_MAX = 1536
ALLOWED = SKILL_FRONTMATTER_REQUIRED | SKILL_FRONTMATTER_OPTIONAL

# Component directories that must not appear in the installable plugin ROOT. Note this
# is the root-level `agents/` (Claude subagents), not `skills/<name>/agents/`, which is
# where a Skill's own invocation policy legitimately lives.
FORBIDDEN_COMPONENTS = ["hooks", "agents", "workflows", "monitors", "scripts",
                        ".mcp.json", ".app.json", ".lsp.json", "settings.json"]

# Every implemented production Skill ships two references. The filenames differ per
# Skill because the documents do -- a plan template is not an initialization checklist.
REQUIRED_REFERENCES = {
    "plan-work": ["references/plan-template.md", "references/quality-checklist.md"],
    "init-project": ["references/config-template.yaml",
                     "references/initialization-checklist.md"],
    "verify-work": ["references/execution-contract.md",
                    "references/evidence-template.md"],
}

# Never inside a Skill: these slices are instruction-only, so there is nothing to
# execute and nothing to fetch.
FORBIDDEN_SKILL_SUBDIRS = ["scripts", "assets", "bin", "node_modules"]

# A fenced shell block is a copyable command, which is structural rather than a matter
# of wording -- unlike prose, which may safely discuss commands it must not run.
SHELL_FENCES = ["```bash", "```sh", "```shell", "```console", "```powershell", "```zsh"]

# Files that would make a Skill depend on something at runtime.
DEPENDENCY_MANIFESTS = ["requirements.txt", "package.json", "pyproject.toml",
                        "Gemfile", "go.mod", "pom.xml"]

# Keys that would turn the invocation-policy file into a permission grant.
FORBIDDEN_POLICY_KEYS = ["tools", "dependencies", "connectors", "permissions",
                         "mcp", "network", "mutations", "allowed-tools"]


def check(plugin_root: pathlib.Path = PLUGIN_ROOT) -> int:
    report = Report("validate_skills")

    # ---- boundary: forbidden components ------------------------------------
    for name in FORBIDDEN_COMPONENTS:
        target = plugin_root / name
        if target.exists():
            code = "PRODUCTION_HOOK_IN_ROOT" if name == "hooks" else "FORBIDDEN_COMPONENT_IN_ROOT"
            report.fail(code, target,
                        f"{name!r} must not exist in the installable plugin root during M1")

    dirs = skill_dirs(plugin_root)
    if not dirs:
        report.fail("FILE_MISSING", plugin_root / "skills", "no skill directories found")
        return report.finish()

    names = [d.name for d in dirs]

    # ---- boundary: no production Skill in the installable root --------------
    for name in names:
        if name in FORBIDDEN_PRODUCTION_SKILLS:
            report.fail("PRODUCTION_SKILL_IN_ROOT", plugin_root / "skills" / name,
                        f"{name!r} is a planned production Skill; a shipped SKILL.md is "
                        "host-discoverable regardless of body text, so it must not exist "
                        "in the installable root during M1")

    # ---- boundary: the milestone allowlist ----------------------------------
    for required in ALLOWED_SKILLS:
        if required not in names:
            report.fail("FILE_MISSING", plugin_root / "skills" / required,
                        f"{required!r} is on the current milestone allowlist but is missing")
    extras = [n for n in names if n not in ALLOWED_SKILLS
              and n not in FORBIDDEN_PRODUCTION_SKILLS]
    for extra in extras:
        report.fail("FORBIDDEN_COMPONENT_IN_ROOT", plugin_root / "skills" / extra,
                    f"unexpected Skill {extra!r}: the installable root currently permits "
                    f"only {ALLOWED_SKILLS}")

    # ---- per-Skill metadata -------------------------------------------------
    for d in dirs:
        skill_md = d / "SKILL.md"
        if not skill_md.is_file():
            report.fail("FILE_MISSING", skill_md, "SKILL.md is missing")
            continue
        try:
            front, _ = load_frontmatter(skill_md)
        except FrontmatterError as exc:
            report.fail("SKILL_FRONTMATTER_ABSENT", skill_md, str(exc))
            continue
        except yaml.YAMLError as exc:
            report.fail("SKILL_FRONTMATTER_MALFORMED", skill_md,
                        f"PyYAML rejected the frontmatter: {exc}")
            continue

        if not isinstance(front, dict):
            report.fail("SKILL_FRONTMATTER_MALFORMED", skill_md,
                        f"frontmatter must be a mapping, got {type(front).__name__}")
            continue

        keys = set(front)
        if "name" not in keys:
            report.fail("SKILL_NAME_MISSING", skill_md, "missing required key 'name'")
        if "description" not in keys:
            report.fail("SKILL_DESCRIPTION_MISSING", skill_md,
                        "missing required key 'description'")
        for key in sorted(keys - ALLOWED):
            report.fail("SKILL_FRONTMATTER_UNSUPPORTED", skill_md,
                        f"key {key!r} is outside the portable minimum set "
                        f"{sorted(ALLOWED)} (FR-025 / DEC-C25)")

        name = front.get("name")
        if name is not None and name != d.name:
            report.fail("SKILL_NAME_MISMATCH", skill_md,
                        f"frontmatter name {name!r} does not match directory {d.name!r}")

        description = front.get("description")
        if description is not None:
            if not isinstance(description, str) or not description.strip():
                report.fail("SKILL_DESCRIPTION_MISSING", skill_md,
                            "description must be a non-empty string")
            elif len(description) > DESCRIPTION_MAX:
                report.fail("SKILL_FRONTMATTER_UNSUPPORTED", skill_md,
                            f"description is {len(description)} chars, exceeds "
                            f"{DESCRIPTION_MAX}")

        # ---- invocation policy ---------------------------------------------
        policy_path = d / "agents" / "openai.yaml"
        if d.name in ALLOWED_SKILLS and not policy_path.is_file():
            report.fail("POLICY_FILE_MISSING", policy_path,
                        f"{d.name!r} must ship agents/openai.yaml")
        if policy_path.is_file():
            try:
                policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                report.fail("SKILL_FRONTMATTER_MALFORMED", policy_path,
                            f"PyYAML rejected the policy file: {exc}")
            else:
                policy = policy or {}
                value = (policy.get("policy") or {}).get("allow_implicit_invocation")
                if d.name in IMPLICIT_INVOCATION_MUST_BE_OFF:
                    if value is not False:
                        report.fail("POLICY_IMPLICIT_INVOCATION_ENABLED", policy_path,
                                    f"policy.allow_implicit_invocation must be false for "
                                    f"{d.name!r}, got {value!r}")
                elif not isinstance(value, bool):
                    report.fail("POLICY_INVOCATION_UNDECLARED", policy_path,
                                f"policy.allow_implicit_invocation must be declared as a "
                                f"boolean, got {value!r}")
                # The file decides WHETHER the Skill may start, never what it may do.
                for key in FORBIDDEN_POLICY_KEYS:
                    if key in policy or key in (policy.get("policy") or {}):
                        report.fail("POLICY_GRANT_NOT_PERMITTED", policy_path,
                                    f"{key!r} must not appear in an invocation-policy "
                                    "file: it controls invocation, not permissions")

        if d.name in IMPLEMENTED_PRODUCTION_SKILLS:
            _check_production_skill(d, skill_md, report)

    report.note("frontmatter parsed by PyYAML (yaml.safe_load)")
    report.note(f"installable-root Skill allowlist: {ALLOWED_SKILLS}; still rejected: "
                f"{FORBIDDEN_PRODUCTION_SKILLS}")
    return report.finish()


def _check_production_skill(d: pathlib.Path, skill_md: pathlib.Path, report: Report) -> None:
    """Structural contract for an implemented production Skill.

    The expected contract comes from the Skill's safety profile, because "safe" differs
    by kind: a planner promises it writes nothing, while an initializer promises it
    writes only what was approved. One shared table would let a writer claim read-only.
    """
    body = skill_md.read_text(encoding="utf-8")
    profile_name = SKILL_PROFILE.get(d.name)
    if profile_name is None:
        report.fail("SKILL_PROFILE_UNDECLARED", skill_md,
                    f"{d.name!r} is implemented but has no safety profile; add one to "
                    "SKILL_PROFILE before shipping it")
        return
    expected_policy = SKILL_SAFETY_PROFILES[profile_name]

    # ---- declared safety contract ------------------------------------------
    raw = extract_policy_marker(body)
    if raw is None:
        report.fail("SKILL_POLICY_MARKER_MISSING", skill_md,
                    "an implemented production Skill must declare a machine-checkable "
                    "safety contract in an agent-harness:policy marker")
    else:
        try:
            declared = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            report.fail("SKILL_POLICY_MARKER_MALFORMED", skill_md,
                        f"PyYAML rejected the policy marker: {exc}")
        else:
            if not isinstance(declared, dict):
                report.fail("SKILL_POLICY_MARKER_MALFORMED", skill_md,
                            f"policy marker must be a mapping, got {type(declared).__name__}")
            else:
                for key, expected in expected_policy.items():
                    if key not in declared:
                        report.fail("SKILL_POLICY_MARKER_MISSING", skill_md,
                                    f"policy marker omits {key!r} (profile {profile_name!r})")
                    elif declared[key] != expected:
                        code = ("SKILL_VERIFICATION_DEFAULT_INVALID"
                                if key == "verification_default"
                                else "SKILL_MUTATION_NOT_PERMITTED")
                        report.fail(code, skill_md,
                                    f"policy {key!r} must be {expected!r} under profile "
                                    f"{profile_name!r}, got {declared[key]!r}")
                if profile_name in PROFILES_REQUIRING_PATH_ROOTS:
                    _check_write_path_roots(d, skill_md, declared, report)

    # ---- no executable command block ---------------------------------------
    # Prose may discuss commands; a fenced shell block is a copyable instruction.
    for fence in SHELL_FENCES:
        if fence in body:
            report.fail("SKILL_COMMAND_BLOCK_PRESENT", skill_md,
                        f"{fence!r} fenced block found: a read-only Skill must not carry "
                        "an executable command block, only proposed commands as text")

    # ---- required references, contained and dependency-free -----------------
    root = d.resolve()
    for rel in REQUIRED_REFERENCES.get(d.name, []):
        target = d / rel
        if not target.is_file():
            report.fail("SKILL_REFERENCE_MISSING", target,
                        f"{rel!r} is required by an implemented production Skill")
            continue
        if not str(target.resolve()).startswith(str(root)):
            report.fail("PATH_ESCAPES_PLUGIN_ROOT", target,
                        f"{rel!r} resolves outside the Skill root")

    for sub in FORBIDDEN_SKILL_SUBDIRS:
        if (d / sub).exists():
            report.fail("SKILL_EXECUTABLE_DIR_PRESENT", d / sub,
                        f"{sub!r} must not exist inside a Skill: this milestone ships "
                        "instruction-only Skills with nothing to execute")

    for manifest in DEPENDENCY_MANIFESTS:
        if (d / manifest).exists():
            report.fail("SKILL_RUNTIME_DEPENDENCY", d / manifest,
                        f"{manifest!r} would give the Skill a runtime dependency")


def _check_write_path_roots(d: pathlib.Path, skill_md: pathlib.Path,
                            declared: dict, report: Report) -> None:
    """A mutation-capable Skill must declare its entire write surface, and keep it safe."""
    roots = declared.get("allowed_path_roots")
    if not isinstance(roots, list) or not roots:
        report.fail("SKILL_WRITE_ROOTS_MISSING", skill_md,
                    "a mutation-capable Skill must declare allowed_path_roots as a "
                    f"non-empty list, got {roots!r}")
        return

    expected = ALLOWED_WRITE_PATH_ROOTS.get(d.name)
    if expected is not None and list(roots) != list(expected):
        report.fail("SKILL_WRITE_ROOTS_UNEXPECTED", skill_md,
                    f"declared write roots {roots!r} do not match the approved surface "
                    f"{expected!r}: widening it is a product decision, not an edit")

    for root in roots:
        if not isinstance(root, str) or not root.strip():
            report.fail("SKILL_WRITE_ROOTS_MISSING", skill_md,
                        f"write root {root!r} must be a non-empty string")
            continue
        # Reject user scope (SEC-17), absolutes, traversal, and the repository's own
        # packaging: a Skill that can rewrite plugins/ can rewrite its own guarantees.
        issues = path_hygiene_issues(root)
        if issues:
            report.fail(issues[0], skill_md,
                        f"write root {root!r} is unsafe: {issues}")
            continue
        if any(root.startswith(prefix) for prefix in FORBIDDEN_WRITE_PATH_PREFIXES):
            report.fail("SKILL_WRITE_ROOT_FORBIDDEN", skill_md,
                        f"write root {root!r} is outside what any Skill may declare")


if __name__ == "__main__":
    main(check)
