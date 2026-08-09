"""Shared infrastructure for agent-harness validation scripts.

Development/CI only. Not part of the installable plugin (PKG-3).

This module contains NO parser and NO schema validator. Authoritative parsing and
validation are delegated to established libraries:

    YAML   -> yaml.safe_load                    (PyYAML)
    JSON Schema -> jsonschema.Draft202012Validator, or the draft each schema declares

Earlier M1 code carried a hand-written YAML subset parser and a hand-written JSON
Schema subset validator. Both were removed in M1.1: an approximation of a published
standard can disagree with the real host implementation while still reporting success,
which is the one failure mode a validator must not have.

What remains here is infrastructure that no library provides for us: bounded output,
diagnostic formatting with stable codes, home-path redaction, path containment,
atomic writes, safe subprocess execution, and frontmatter boundary extraction.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN_ROOT = REPO_ROOT / "plugins" / "agent-harness"

# Bounded output: no diagnostic or captured stream may exceed these.
MAX_EXCERPT_CHARS = 2000
MAX_EXCERPT_LINES = 40


# --------------------------------------------------------------------------
# Redaction and bounded output
# --------------------------------------------------------------------------

_HOME_PATTERNS = [
    re.compile(re.escape(str(pathlib.Path.home())), re.IGNORECASE),
    re.compile(r"[A-Za-z]:\\Users\\[^\\/:*?\"<>|\r\n]+"),
    re.compile(r"/(?:home|Users)/[^/\s]+"),
]

_CREDENTIAL_PATTERNS = [
    (re.compile(r"\bghp_[A-Za-z0-9]{16,}"), "[REDACTED:known-prefix]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), "[REDACTED:known-prefix]"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "[REDACTED:known-prefix]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED:known-prefix]"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "[REDACTED:known-prefix]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "[REDACTED:private-key]"),
    (re.compile(r"://[^/\s:]+:[^/\s@]+@"), "://[REDACTED:connection-string]@"),
]


def redact(text: str) -> str:
    """Remove home paths and credential-shaped strings before anything is recorded.

    Applied to every captured host-command output. Experiment records are committed
    to the repository, so this runs before storage, not after review.
    """
    for pattern, replacement in _CREDENTIAL_PATTERNS:
        text = pattern.sub(replacement, text)
    for pattern in _HOME_PATTERNS:
        text = pattern.sub("[REDACTED:user-path]", text)
    return text


def bounded(text: str, max_chars: int = MAX_EXCERPT_CHARS,
            max_lines: int = MAX_EXCERPT_LINES) -> str:
    """Truncate to a recordable excerpt. Always redacts first."""
    text = redact(text)
    lines = text.splitlines()
    if len(lines) > max_lines:
        head = lines[: max_lines // 2]
        tail = lines[-(max_lines // 2):]
        omitted = len(lines) - len(head) - len(tail)
        lines = head + [f"[... {omitted} lines omitted ...]"] + tail
        text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n[... truncated at {max_chars} chars ...]"
    return text


# --------------------------------------------------------------------------
# Path containment
# --------------------------------------------------------------------------

def is_contained(child, parent) -> bool:
    """True when `child` resolves strictly inside `parent`.

    Used for plugin-root containment and for rejecting traversal in declared paths.
    Symlinks are resolved first, so a link pointing outside the root is caught.
    """
    try:
        c = pathlib.Path(child).resolve()
        p = pathlib.Path(parent).resolve()
    except (OSError, ValueError):
        return False
    try:
        c.relative_to(p)
        return True
    except ValueError:
        return False


def path_hygiene_issues(raw: str) -> list[str]:
    """Return stable diagnostic codes for an unsafe declared path.

    Checks the shapes a manifest path must never take. Returns codes, not prose,
    so tests can assert on a stable identifier.
    """
    issues = []
    if not raw:
        return ["PATH_EMPTY"]
    # UNC is checked before absolute: "//server/share" starts with "/" but reporting it
    # as merely absolute would hide the more specific and more dangerous shape.
    if raw.startswith("\\\\") or raw.startswith("//"):
        issues.append("PATH_UNC")
    elif raw.startswith("/") or raw.startswith("\\"):
        issues.append("PATH_ABSOLUTE")
    if re.match(r"^[A-Za-z]:[\\/]", raw):
        issues.append("PATH_DRIVE_QUALIFIED")
    if raw.startswith("~"):
        issues.append("PATH_TILDE")
    if "$" in raw or "%" in raw:
        issues.append("PATH_ENV_INTERPOLATION")
    parts = re.split(r"[\\/]", raw)
    if ".." in parts:
        issues.append("PATH_PARENT_TRAVERSAL")
    return issues


# --------------------------------------------------------------------------
# Atomic writes
# --------------------------------------------------------------------------

def atomic_write_text(path, text: str, encoding: str = "utf-8") -> None:
    """Write via a temporary file then replace, so a crash cannot truncate the target."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        pathlib.Path(tmp).unlink(missing_ok=True)
        raise


# --------------------------------------------------------------------------
# Safe subprocess
# --------------------------------------------------------------------------

def run_capture(argv: list[str], timeout: int = 60, cwd=None) -> dict:
    """Run a command safely and return a bounded, redacted result.

    argv is always a list -- never a shell string -- so no shell interpretation
    occurs. Output is bounded and redacted before it can reach a record.
    """
    if not isinstance(argv, list) or not all(isinstance(a, str) for a in argv):
        raise TypeError("argv must be a list of strings (no shell strings)")
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout,
            cwd=str(cwd) if cwd else None, shell=False,
        )
    except FileNotFoundError:
        return {"available": False, "exit_code": None, "stdout": "", "stderr": "",
                "note": "command not found"}
    except subprocess.TimeoutExpired:
        return {"available": True, "exit_code": None, "stdout": "", "stderr": "",
                "note": f"timed out after {timeout}s"}
    return {
        "available": True,
        "exit_code": proc.returncode,
        "stdout": bounded(proc.stdout),
        "stderr": bounded(proc.stderr),
        "note": "",
    }


# --------------------------------------------------------------------------
# Frontmatter boundary extraction
# --------------------------------------------------------------------------

class FrontmatterError(Exception):
    """Raised when the --- delimiters are absent or unterminated."""


def split_frontmatter(text: str) -> tuple[str, str]:
    """Split a Markdown file into (raw YAML frontmatter, body).

    This performs boundary extraction ONLY. It does not parse YAML -- the raw block
    is handed to yaml.safe_load by the caller, so PyYAML remains the authoritative
    parser and any YAML error surfaces as a real PyYAML error.
    """
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        raise FrontmatterError("file does not start with a '---' frontmatter delimiter")
    offset = text.index("\n") + 1
    end = text.find("\n---", offset)
    if end == -1:
        raise FrontmatterError("unterminated frontmatter: no closing '---'")
    closing_line_end = text.find("\n", end + 1)
    body = "" if closing_line_end == -1 else text[closing_line_end + 1:]
    return text[offset:end], body


# --------------------------------------------------------------------------
# Diagnostics
# --------------------------------------------------------------------------

class Report:
    """Collects diagnostics so one run reports every problem, each with a stable code.

    A diagnostic code is part of the contract: tests assert on the code, not on the
    prose, so wording can improve without breaking the negative-scenario suite.
    """

    def __init__(self, check_name: str) -> None:
        self.check_name = check_name
        self.failures: list[tuple[str, str, str]] = []   # (code, where, message)
        self.notes: list[str] = []

    def fail(self, code: str, path, message: str) -> None:
        self.failures.append((code, rel(path) if path is not None else self.check_name, message))

    def note(self, message: str) -> None:
        self.notes.append(message)

    @property
    def codes(self) -> list[str]:
        return [code for code, _, _ in self.failures]

    def finish(self) -> int:
        for note in self.notes:
            print(f"  note: {note}")
        if not self.failures:
            print(f"OK   {self.check_name}")
            return 0
        print(f"FAIL {self.check_name}", file=sys.stderr)
        for code, where, message in self.failures:
            print(f"  - [{code}] {where}: {message}", file=sys.stderr)
        return 1


def rel(path) -> str:
    p = pathlib.Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return redact(p.as_posix())


def load_json(path, report: Report, code: str = "JSON_INVALID"):
    """Read JSON, recording a parse failure instead of raising."""
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.fail("FILE_MISSING", path, "file not found")
    except json.JSONDecodeError as exc:
        report.fail(code, path, f"invalid JSON: {exc.msg} (line {exc.lineno}, col {exc.colno})")
    return None


# --------------------------------------------------------------------------
# Repo conventions
# --------------------------------------------------------------------------

# M1.1: no production Skill may exist under the installable plugin root.
PLANNED_PRODUCTION_SKILLS = [
    "init-project", "plan-work", "orchestrate",
    "verify-work", "refine-harness", "apply-refinement", "doctor",
]

# Production Skills actually implemented, by milestone. A name moves here only when its
# body, references and tests exist -- a shipped SKILL.md is host-discoverable whatever
# it says, so an unimplemented name in the installable root is a product surface with
# nothing behind it.
IMPLEMENTED_PRODUCTION_SKILLS = ["plan-work", "init-project", "verify-work",
                                "doctor", "orchestrate",
                                "refine-harness"]            # M2 slices 1-6

# Still unimplemented, and therefore still rejected in the installable root.
FORBIDDEN_PRODUCTION_SKILLS = [
    name for name in PLANNED_PRODUCTION_SKILLS if name not in IMPLEMENTED_PRODUCTION_SKILLS
]

# The single compatibility fixture Skill permitted in the installable root.
DISCOVERY_FIXTURE_SKILL = "m1-discovery-fixture"

# Every Skill directory permitted in the installable root right now.
ALLOWED_SKILLS = [DISCOVERY_FIXTURE_SKILL, *IMPLEMENTED_PRODUCTION_SKILLS]

# Skills whose invocation policy must keep implicit invocation OFF. Reachability should
# match side effects: the fixture does nothing, so being selectable buys nothing;
# init-project writes files, so it must start only because someone named it. plan-work
# is read-only, so implicit selection costs a document, not a mutation.
IMPLICIT_INVOCATION_MUST_BE_OFF = [DISCOVERY_FIXTURE_SKILL, "init-project",
                                   "verify-work", "orchestrate",
                                   "refine-harness"]

# --------------------------------------------------------------------------
# Skill safety profiles
# --------------------------------------------------------------------------
# Each implemented production Skill declares a machine-checkable contract in its body.
# Profiles exist because "safe" is not one thing: a read-only Skill and a
# mutation-capable one make different promises, and collapsing them would either let a
# writer claim read-only or force a planner to declare approval fields it never uses.

# True for every production Skill regardless of profile.
#
# `executes_commands` USED to live here. It stopped being universal the moment a
# verification Skill existed: running the user's own configured checks is that Skill's
# entire purpose. Leaving the field here and letting one profile override it would have
# been worse than moving it -- a "universal guarantee" with an exception is not a
# guarantee, it is a default wearing the wrong name. Each profile now states its own
# execution posture explicitly, so no Skill inherits a promise it does not keep.
UNIVERSAL_SKILL_POLICY = {
    "network_access": False,
}

SKILL_SAFETY_PROFILES = {
    # Plans, proposes, and writes only when explicitly asked to save.
    "read-only": {
        **UNIVERSAL_SKILL_POLICY,
        "read_only": True,
        "executes_commands": False,
        "modifies_source": False,
        "modifies_config": False,
        "spawns_agents": False,
        "verification_default": "Not Run",
        "persistence": "on-request-only",
    },
    # Writes files, but only after approval tied to a shown proposal.
    #
    # The two rollback fields are deliberately separate. "Never deletes anything" and
    # "cleans up after a failed attempt" read as a contradiction when stated as one
    # promise, and the resolution is a distinction, not a preference: content that
    # existed BEFORE the attempt is untouchable, while content the attempt itself
    # created may be withdrawn by it.
    "approval-gated-mutation": {
        **UNIVERSAL_SKILL_POLICY,
        "read_only": False,
        "executes_commands": False,
        "requires_explicit_invocation": True,
        "requires_mutation_approval": True,
        "installs_packages": False,
        "modifies_user_settings": False,
        "overwrites_existing_files": False,
        "idempotent": True,
        "deletes_preexisting_content": False,
        "may_rollback_current_attempt": True,
    },
    # Runs the user's own configured verification gates, and nothing else.
    #
    # `read_only: false` here means only "subprocesses run, so this is not
    # side-effect-free". It grants no authority to edit source or configuration --
    # `modifies_source` and `modifies_config` stay false, and there is no write surface
    # at all. The dangerous power in this profile is execution, so the constraint that
    # matters is `executes_configured_gates_only`: the command set comes from
    # config.yaml, never from inference about the repository.
    "bounded-verification": {
        **UNIVERSAL_SKILL_POLICY,
        "read_only": False,
        "executes_commands": True,
        "requires_explicit_invocation": True,
        "requires_execution_approval": True,
        "executes_configured_gates_only": True,
        "modifies_source": False,
        "modifies_config": False,
        "spawns_agents": False,
        "installs_packages": False,
        "modifies_user_settings": False,
        "command_definition": "argv-array",
        "verification_default": "Not Run",
        "evidence_persistence": "response-only",
    },
    # Carries out a ready plan: writes planned source paths and may delegate to
    # subagents. It does NOT execute commands in this milestone.
    #
    # A ready plan defines the allowed SCOPE; explicit invocation is the user's
    # authorization to begin ordinary non-destructive work within that scope. Those are
    # two different things, and neither is a general licence: work outside the plan is
    # unauthorized however the Skill was invoked.
    #
    # `executes_commands` is False because there is no structured, validated command
    # representation for plan tasks yet -- no argv, no working directory, no timeout, no
    # security semantics. Executing prose that merely looks like a command would be
    # exactly the injection surface verify-work's argv contract exists to prevent, so
    # direct implementation-command execution is deferred until that representation
    # exists. `executes_planned_commands_only` stays declared as the standing constraint
    # for when it does.
    # Reads run evidence and writes exactly ONE proposal. It never applies that proposal.
    #
    # It deliberately does NOT reuse approval-gated-mutation. That profile requires
    # mutation approval tied to an already-shown proposal -- and this Skill is what
    # produces the proposal, so reusing it would make the authorization circular: the
    # artifact would need to exist before it could be authorized to exist.
    #
    # The distinction that replaces it: explicit invocation authorizes CREATING the
    # proposal artifact; creating a proposal is never permission to APPLY its contents.
    # apply-refinement owns application approval, and does not exist yet.
    "proposal-only-mutation": {
        **UNIVERSAL_SKILL_POLICY,
        "read_only": False,
        "executes_commands": False,
        "spawns_agents": False,
        "modifies_source": False,
        "modifies_config": False,
        "requires_explicit_invocation": True,
        "requires_mutation_approval": False,
        "writes_single_proposal_only": True,
        "modifies_existing_proposals": False,
        "overwrites_existing_files": False,
        "deletes_preexisting_content": False,
        "may_rollback_current_attempt": True,
        "requires_evidence_refs": True,
        "initial_proposal_status": "proposed",
        "requires_repository_contained_paths": True,
        "rejects_symlink_escape": True,
        "installs_packages": False,
        "modifies_user_settings": False,
    },
    "plan-bounded-orchestration": {
        **UNIVERSAL_SKILL_POLICY,
        "read_only": False,
        "executes_commands": False,
        "spawns_agents": True,
        "modifies_source": True,
        "requires_explicit_invocation": True,
        "requires_ready_plan": True,
        "executes_planned_commands_only": True,
        "modifies_planned_paths_only": True,
        "requires_repository_contained_paths": True,
        "rejects_symlink_escape": True,
        "modifies_harness_state": False,
        "destructive_actions_require_approval": True,
        "respects_dependency_graph": True,
        "max_parallel_from_config": True,
        "auto_merge_conflicts": False,
        "modifies_user_settings": False,
        "evidence_persistence": "response-only",
        "run_state_runtime": "deferred",
    },
}

SKILL_PROFILE = {
    "plan-work": "read-only",
    "init-project": "approval-gated-mutation",
    "verify-work": "bounded-verification",
    # doctor reuses the existing read-only profile unchanged. It diagnoses the harness,
    # so it needs no execution and no write surface -- the profile already says exactly
    # that, and widening it to fit would have defeated the point of having profiles.
    "doctor": "read-only",
    "orchestrate": "plan-bounded-orchestration",
    "refine-harness": "proposal-only-mutation",
}

# Only this profile may run a subprocess. Asserted in tests so a future profile cannot
# acquire execution by inheritance without someone deciding to grant it.
PROFILES_PERMITTING_EXECUTION = ["bounded-verification"]

# Delegating to subagents is narrower still than executing. verify-work runs commands but
# must never spawn an agent: a verifier that could delegate could delegate its way around
# its own gate list.
PROFILES_PERMITTING_AGENT_SPAWN = ["plan-bounded-orchestration"]

# A mutation-capable Skill must also declare its entire write surface. Anything outside
# these roots is a path the user never agreed to.
PROFILES_REQUIRING_PATH_ROOTS = ["approval-gated-mutation", "proposal-only-mutation"]
ALLOWED_WRITE_PATH_ROOTS = {
    "init-project": [".agent-harness/", "CLAUDE.md", "AGENTS.md"],
    # One directory, and only ever one new file inside it. Note this is NARROWER than
    # init-project's `.agent-harness/` root: two Skills now hold different permissions
    # over the same tree, which is the point -- memory, config and run artifacts each
    # keep their own approval path.
    "refine-harness": [".agent-harness/proposals/"],
}

# Roots a Skill may never declare: user scope is out of bounds (SEC-17), and so is
# anything that would let a Skill rewrite version control or its own packaging.
FORBIDDEN_WRITE_PATH_PREFIXES = [
    "~", "/", "\\", ".git/", ".github/", "plugins/", "marketplace/", "scripts/",
]

# Structural policy marker embedded in a production SKILL.md body. Parsed as YAML, not
# grepped: prose like "this Skill never runs commands" must not be mistaken for either
# a promise or a violation, and only a declared block can be checked exactly.
POLICY_MARKER_OPEN = "<!-- agent-harness:policy"
POLICY_MARKER_CLOSE = "-->"


def extract_policy_marker(text: str):
    """Return the raw YAML inside a SKILL.md policy marker, or None if absent."""
    start = text.find(POLICY_MARKER_OPEN)
    if start < 0:
        return None
    body_start = start + len(POLICY_MARKER_OPEN)
    end = text.find(POLICY_MARKER_CLOSE, body_start)
    if end < 0:
        return None
    return text[body_start:end]

# FR-025 / DEC-C25: canonical cross-host frontmatter minimum set.
SKILL_FRONTMATTER_REQUIRED = {"name", "description"}
SKILL_FRONTMATTER_OPTIONAL = {"license", "metadata"}


def skill_dirs(plugin_root: pathlib.Path = PLUGIN_ROOT):
    skills = plugin_root / "skills"
    if not skills.is_dir():
        return []
    return sorted(p for p in skills.iterdir() if p.is_dir())


def iter_text_files(root: pathlib.Path,
                    suffixes=(".md", ".json", ".yaml", ".yml", ".py", ".toml")):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in suffixes:
            yield path


def main(fn):
    """Run a check function and exit with its status."""
    sys.exit(fn())
