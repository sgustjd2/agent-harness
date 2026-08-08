#!/usr/bin/env python3
"""Experiment A probe (ATS-028): report ONLY booleans about plugin-root variables.

SEC-22: never emit variable values, secrets, or a full environment dump. Output is
limited to presence flags and containment flags, which is all the experiment needs.

The environment is read ONCE into local booleans at the top, and the reporting step
touches only those booleans. That ordering is deliberate: it makes "no value can reach
stdout" a structural property of the file rather than something a reader has to verify
by tracing expressions. tests/security/test_experiment_hygiene.py enforces it.

This is a TEST FIXTURE. It is not part of the installable plugin -- the MVP ships no
hooks (FR-022). It exists so the hook-root question can be answered separately from the
Skill-script question (ATS-020), whose result it must not be used as evidence for.
"""

import json
import os
import pathlib

VARS = ["PLUGIN_ROOT", "PLUGIN_DATA", "CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA"]


def _contained(child, parent):
    """True when `child` resolves inside `parent`. Returns a bool, never a path."""
    if not child or not parent:
        return None
    try:
        pathlib.Path(child).resolve().relative_to(pathlib.Path(parent).resolve())
        return True
    except (ValueError, OSError):
        return False


def _collect():
    """Read the environment and reduce it to booleans. Nothing else leaves this function."""
    values = {name: os.environ.get(name) for name in VARS}
    root = values["PLUGIN_ROOT"]
    data = values["PLUGIN_DATA"]
    return {
        "present": {name: value is not None for name, value in values.items()},
        "plugin_root_is_dir": bool(root) and pathlib.Path(root).is_dir(),
        "plugin_data_is_dir": bool(data) and pathlib.Path(data).is_dir(),
        "data_inside_root": _contained(data, root),
        "compat_root_matches_plugin_root": (
            values["CLAUDE_PLUGIN_ROOT"] == root if root else None
        ),
        "compat_data_matches_plugin_data": (
            values["CLAUDE_PLUGIN_DATA"] == data if data else None
        ),
    }


# Every value in FINDINGS is a bool or None. No path or variable value is present.
FINDINGS = _collect()

assert all(
    isinstance(v, (bool, type(None)))
    for v in list(FINDINGS.values()) + list(FINDINGS["present"].values())
    if not isinstance(v, dict)
), "probe would emit a non-boolean; refusing (SEC-22)"

print(json.dumps(FINDINGS, indent=2, sort_keys=True))
