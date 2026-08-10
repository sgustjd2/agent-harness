"""M5 slice 4 — the three reference example configurations.

Each README has claimed, since M1, that its config is *"validated against
`config.schema.json` in CI, so it cannot drift from the schema"*.

**Nothing validated them.** No test and no script referenced `examples/` at all. The claim
was not merely untested — it was a claim *about* being tested, which is the worst kind to
leave unbacked, because it is the sentence a reader uses to decide not to check.

This file makes it true. It also guards the defect the examples were quietly carrying:
`python -m pytest`, the exact command a contract dry-run found reporting failure on
passing tests. `init-project`, its template and `doctor` were all fixed when D-02 was
found. The examples were not — and an example is the one place a wrong command gets
copied into somebody's project on purpose.
"""

from __future__ import annotations

import pathlib
import sys

import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

EXAMPLES = REPO_ROOT / "examples"
CONFIG_SCHEMA = ("plugins/agent-harness/core/schemas/state/config.schema.json")

NAMES = ["generic-repo", "python-service", "typescript-web"]

# Bare names that get resolved by PATH at gate time. On Windows several of these are
# app-execution stubs that run nothing and exit non-zero (D-02).
BARE_INTERPRETERS = ["python", "python3", "node", "ruby", "npx", "npm", "pip", "pip3"]


def _config(name: str) -> dict:
    return yaml.safe_load(
        (EXAMPLES / name / ".agent-harness" / "config.yaml").read_text(encoding="utf-8"))


def _config_text(name: str) -> str:
    return (EXAMPLES / name / ".agent-harness" / "config.yaml").read_text(encoding="utf-8")


def _readme(name: str) -> str:
    return " ".join((EXAMPLES / name / "README.md").read_text(encoding="utf-8").lower().split())


def _gates(name: str) -> list:
    return _config(name)["verification"].get("gates") or []


# ---------------------------------------------- 1-4. the README claim is now true

def test_the_examples_that_exist_are_the_ones_expected():
    assert sorted(p.name for p in EXAMPLES.iterdir() if p.is_dir()) == NAMES


@pytest.mark.parametrize("name", NAMES)
def test_the_example_config_validates_against_the_schema(name):
    """The check every README has promised since M1, finally performed."""
    from _authoritative import load_schema, validate

    errors = validate(_config(name), load_schema(CONFIG_SCHEMA))
    assert errors == [], errors


@pytest.mark.parametrize("name", NAMES)
def test_the_readme_still_claims_ci_validation(name):
    """If someone removes the claim, this test should go with it — not survive as the
    only reason the claim looks safe."""
    assert "validated against `config.schema.json` in ci" in _readme(name)


@pytest.mark.parametrize("name", NAMES)
def test_the_schema_path_comment_is_correct(name):
    """It pointed at `core/schemas/config.schema.json` for four milestones. The file is
    under `core/schemas/state/`, which is a different directory for a stated reason."""
    assert CONFIG_SCHEMA in _config_text(name)
    assert (REPO_ROOT / CONFIG_SCHEMA).is_file()


# ------------------------------------------------- 5-8. the D-02 regression guard

@pytest.mark.parametrize("name", NAMES)
def test_no_example_gate_starts_with_a_bare_interpreter(name):
    """The defect these examples were shipping.

    A bare name is resolved by PATH when the gate runs. It may be a different
    interpreter than the one the project's packages live in, and on Windows it is
    frequently a stub that runs nothing and exits non-zero — so the gate reports failure
    while the tests pass, and no verification status can tell that from a real failure.
    """
    offenders = [g["id"] for g in _gates(name) if g["command"][0] in BARE_INTERPRETERS]
    assert not offenders, offenders


def test_the_python_example_names_a_project_owned_interpreter():
    for gate in _gates("python-service"):
        assert gate["command"][0].startswith(".venv/")


def test_the_typescript_example_uses_project_local_binaries():
    """`npx` fetches and runs what is not installed, turning a gate into a download."""
    for gate in _gates("typescript-web"):
        assert gate["command"][0].startswith("node_modules/.bin/")


def test_the_python_readme_admits_the_path_is_platform_specific():
    """`config.yaml` is committed and shared, so one interpreter path cannot serve a
    mixed-platform team. There is no fix in the file; naming the cost beats a config
    that silently works only for whoever wrote it.
    """
    readme = _readme("python-service")
    assert ".venv/scripts/python.exe" in readme
    assert "committed** and shared" in readme or "committed and shared" in readme


# --------------------------------------------- 9-13. each example teaches one thing

def test_the_generic_example_ships_no_gates_on_purpose():
    """`unverified` is not `passed` and not `failed`."""
    assert _gates("generic-repo") == []
    readme = _readme("generic-repo")
    assert "not `passed`, not `failed`" in readme
    assert "invented on the spot" in readme


def test_the_generic_example_marks_generic_as_a_placeholder():
    """D-05's wording, carried into the file a user copies."""
    assert "`generic` is a placeholder, not a fallback" in _readme("generic-repo")


def test_the_flaky_policy_is_shown_on_exactly_one_gate():
    """Applied everywhere it becomes a way to make failures go away."""
    flaky = [g["id"] for g in _gates("typescript-web") if g.get("flaky_policy") == "rerun-once"]
    assert flaky == ["e2e"]


def test_the_flaky_readme_says_a_rerun_pass_is_not_a_pass():
    readme = _readme("typescript-web")
    assert "classified `flaky`, not `pass`" in readme
    assert "do not apply it to deterministic gates" in readme


def test_working_dir_is_demonstrated_instead_of_a_shell_wrapper():
    gates = {g["id"]: g for g in _gates("typescript-web")}
    assert gates["e2e"]["working_dir"] == "e2e"
    assert "quoting bugs and injection live" in _readme("typescript-web")


# ------------------------------------------------ 14-16. redaction and evidence

def test_extra_redaction_patterns_are_demonstrated():
    """The built-ins catch shapes that look the same everywhere; they cannot know that
    this project's hostnames matter."""
    patterns = _config("generic-repo")["redaction"]["extra_patterns"]
    assert len(patterns) >= 2


@pytest.mark.parametrize("name", NAMES)
def test_no_example_commits_evidence_by_default(name):
    """`true` un-ignores runs/ and commits raw output; doctor warns about it."""
    assert _config(name)["runs"]["commit_evidence"] is False


@pytest.mark.parametrize("name", NAMES)
def test_no_example_prunes_runs_automatically(name):
    """Deletion is irreversible and can destroy an audit trail."""
    assert _config(name)["runs"]["auto_prune"] is False
