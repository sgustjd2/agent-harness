#!/usr/bin/env python3
"""Validate Skill metadata and the installable-plugin Skill boundary.

Frontmatter is parsed by PyYAML (yaml.safe_load) after boundary extraction, so a
malformed block fails with a real YAML error rather than a subset parser's guess.

Boundary rules enforced here (M1.1 Step 7):
  - no production Skill name may exist under the installable plugin root
  - exactly one compatibility fixture Skill, m1-discovery-fixture
  - it must carry agents/openai.yaml with implicit invocation disabled
  - no production hook directory in the installable root
"""

from __future__ import annotations

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _authoritative import load_frontmatter  # noqa: E402
from _common import (  # noqa: E402
    DISCOVERY_FIXTURE_SKILL,
    FORBIDDEN_PRODUCTION_SKILLS,
    PLUGIN_ROOT,
    SKILL_FRONTMATTER_OPTIONAL,
    SKILL_FRONTMATTER_REQUIRED,
    FrontmatterError,
    Report,
    main,
    skill_dirs,
)

DESCRIPTION_MAX = 1536
ALLOWED = SKILL_FRONTMATTER_REQUIRED | SKILL_FRONTMATTER_OPTIONAL

# Component directories that must not appear in the installable plugin root.
FORBIDDEN_COMPONENTS = ["hooks", "agents", "workflows", "monitors", "scripts",
                        ".mcp.json", ".app.json", ".lsp.json", "settings.json"]


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

    # ---- boundary: exactly one fixture Skill --------------------------------
    if DISCOVERY_FIXTURE_SKILL not in names:
        report.fail("FILE_MISSING", plugin_root / "skills" / DISCOVERY_FIXTURE_SKILL,
                    "the single M1 compatibility fixture Skill is missing")
    extras = [n for n in names if n != DISCOVERY_FIXTURE_SKILL
              and n not in FORBIDDEN_PRODUCTION_SKILLS]
    for extra in extras:
        report.fail("FORBIDDEN_COMPONENT_IN_ROOT", plugin_root / "skills" / extra,
                    f"unexpected Skill {extra!r}: M1 permits only "
                    f"{DISCOVERY_FIXTURE_SKILL!r} in the installable root")

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
        if d.name == DISCOVERY_FIXTURE_SKILL and not policy_path.is_file():
            report.fail("POLICY_FILE_MISSING", policy_path,
                        "the discovery fixture must ship agents/openai.yaml")
        if policy_path.is_file():
            try:
                policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                report.fail("SKILL_FRONTMATTER_MALFORMED", policy_path,
                            f"PyYAML rejected the policy file: {exc}")
            else:
                value = ((policy or {}).get("policy") or {}).get("allow_implicit_invocation")
                if value is not False:
                    report.fail("POLICY_IMPLICIT_INVOCATION_ENABLED", policy_path,
                                f"policy.allow_implicit_invocation must be false, "
                                f"got {value!r}")

    report.note("frontmatter parsed by PyYAML (yaml.safe_load)")
    return report.finish()


if __name__ == "__main__":
    main(check)
