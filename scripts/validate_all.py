#!/usr/bin/env python3
"""Run every deterministic M1 check, then pytest. One authoritative inventory.

Renamed from run_all.py in M1.1. Two rules govern this file:

  1. It ORCHESTRATES; it does not replace pytest. Pytest is the authoritative test
     runner, and its result is reported verbatim.
  2. Each validator runs EXACTLY ONCE. Re-running a check to inflate a total would
     make the summary meaningless.

Manual host tests are never run here. They need a real host and, in some cases, an
interactive or paid model. Their recorded results live in docs/m1-experiments.md.

Usage:
    python scripts/validate_all.py          run everything
    python scripts/validate_all.py --list   show the inventory without running
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# The authoritative inventory of deterministic validators. One entry per validator.
VALIDATORS = [
    ("preflight", "scripts/preflight.py",
     "NON-AUTHORITATIVE readability / JSON syntax / path shape"),
    ("generate_marketplaces --check", "scripts/generate_marketplaces.py",
     "Candidate C generation determinism"),
    ("validate_manifests", "scripts/validate_manifests.py",
     "both plugin manifests vs packaging schemas (jsonschema)"),
    ("validate_marketplaces", "scripts/validate_marketplaces.py",
     "three catalogs vs packaging schemas (jsonschema)"),
    ("validate_skills", "scripts/validate_skills.py",
     "Skill frontmatter (PyYAML) + installable-root boundary"),
    ("check_path_containment", "scripts/check_path_containment.py",
     "plugin-root containment, symlink escape"),
    ("check_path_portability", "scripts/check_path_portability.py",
     "canonical layer uses no host path assumption"),
    ("check_version_sync", "scripts/check_version_sync.py",
     "version agreement across all five version-bearing files"),
    ("check_no_install_command", "scripts/check_no_install_command.py",
     "no undocumented host command in user-facing paths"),
    ("check_no_network", "scripts/check_no_network.py",
     "runtime code imports nothing network-capable"),
    ("check_adapter_drift", "scripts/check_adapter_drift.py",
     "adapters do not copy canonical Skill prose"),
    ("check_colocation", "scripts/check_colocation.py",
     "dual-manifest co-location, static half only"),
]

EXTRA_ARGS = {"scripts/generate_marketplaces.py": ["--check"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list the inventory only")
    args = parser.parse_args()

    if args.list:
        print(f"Deterministic validators ({len(VALIDATORS)}), each run once:")
        for label, rel, purpose in VALIDATORS:
            print(f"  {label:34s} {rel:42s} {purpose}")
        print("\nAuthoritative test runner: pytest (python -m pytest)")
        print("Manual host tests are NOT run here -- see docs/m1-experiments.md")
        return 0

    failed: list[str] = []
    for label, rel, _ in VALIDATORS:
        print(f"\n=== {label} ===")
        argv = [sys.executable, str(REPO_ROOT / rel)] + EXTRA_ARGS.get(rel, [])
        if subprocess.run(argv, cwd=REPO_ROOT).returncode != 0:
            failed.append(label)

    print("\n=== pytest (authoritative test runner) ===")
    pytest_rc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"], cwd=REPO_ROOT).returncode
    if pytest_rc != 0:
        failed.append("pytest")

    print("\n" + "=" * 68)
    print(f"deterministic validators : {len(VALIDATORS) - len([f for f in failed if f != 'pytest'])}"
          f"/{len(VALIDATORS)} passed")
    print(f"pytest                   : {'passed' if pytest_rc == 0 else 'FAILED'}")
    if failed:
        print(f"FAILED: {', '.join(failed)}", file=sys.stderr)
        return 1
    print("all deterministic checks passed")
    print("manual host tests are separate and are NOT covered by this run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
