#!/usr/bin/env python3
"""M1 exit-criteria status, computed from a structured table.

The previous M1 report claimed "12 of 17" while listing 11 criteria. That happened
because the total was written by hand. Here the table is the only input and every
number is derived from it, so the arithmetic cannot drift from the evidence again.

Only PASSED counts as met. Partially implemented does not.

Usage:
    python scripts/m1_status.py            summary + counts
    python scripts/m1_status.py --markdown emit the table for the M1 documents
"""

from __future__ import annotations

import argparse
import collections
import sys

PASSED = "Passed"
FAILED = "Failed"
BLOCKED = "Blocked"
NOT_AVAILABLE = "Not Available"
MANUAL_REQUIRED = "Manual Required"

VALID_STATES = {PASSED, FAILED, BLOCKED, NOT_AVAILABLE, MANUAL_REQUIRED}

# (id, requirement, state, evidence)
CRITERIA = [
    ("E1", "Valid Claude plugin fixture passes `claude plugin validate`", PASSED,
     "`claude plugin validate ./plugins/agent-harness --strict` -> exit 0, "
     "'Validation passed'. Claude Code 2.1.195."),
    ("E2", "Valid Claude marketplace fixture passes Claude validation", PASSED,
     "`claude plugin validate . --strict` -> exit 0, 'Validation passed'. "
     "Claude Code 2.1.195."),
    ("E3", "Codex plugin manifest validated by official mechanism, else a documented "
           "local schema", PASSED,
     "M1.2 correction: Codex CLI IS available (codex-cli 0.146.0-alpha.9.2, bundled "
     "with ChatGPT Desktop). Its help exposes no `validate` subcommand, so no official "
     "manifest validator exists. `.codex-plugin/plugin.json` validated by "
     "`codex-plugin.schema.json` via jsonschema Draft 2020-12. INDIRECT HOST EVIDENCE: "
     "`codex plugin add` accepted and installed the plugin from this manifest, so the "
     "real host parsed it successfully."),
    ("E4", "Codex marketplace validated by official mechanism, else a documented "
           "local schema", PASSED,
     "M1.3: DEF-001 remediated and REVALIDATED ON THE REAL HOST. The corrected catalog "
     "(policy.installation=AVAILABLE, policy.authentication=ON_INSTALL, "
     "category=Productivity, object source) was accepted by "
     "`codex plugin marketplace add` on codex-cli 0.146.0-alpha.9.2, in an isolated "
     "CODEX_HOME, registration only -- no plugin installed. Also validated by "
     "openai-marketplace.schema.json via jsonschema, whose enums now trace to the "
     "contract evidence table. 16 regression scenarios (NS-29..NS-45, less the withdrawn "
     "NS-42) lock the fix. M1.3.1: evidence classification corrected -- the schema now "
     "accepts BOTH documented local source forms (the object form is a local generation "
     "choice, not a vendor requirement) and the officially documented kebab-case "
     "identifier patterns were restored after an incorrect M1.3 removal. Deterministic "
     "revalidation only; the M1.3 host evidence above is retained and was NOT re-run."),
    ("E5", "The same plugin root works in both hosts, or the generated-distribution "
           "fallback decision is triggered", PASSED,
     "M1.4A: BOTH HOSTS NOW LOAD THE SAME CO-LOCATED ROOT. Claude half RESOLVED -- "
     "`claude --plugin-dir ./plugins/agent-harness plugin list --json` returned "
     "agent-harness@inline, scope=session, enabled=true, version 0.0.1, loaded from the "
     "root containing .codex-plugin/. This is RUNTIME LOADING, not validator tolerance. "
     "No installed record was created: a bare `claude plugin list` omits it and the "
     "plugin cache digest was byte-identical before and after. Codex half (M1.2): "
     "installed from a root containing .claude-plugin/, both manifests and skills/ "
     "preserved in the isolated cache -- version-scoped and PROC-001 protocol-deviating, "
     "retained but not re-run. VERSION-SCOPED: Claude Code 2.1.195 and codex-cli "
     "0.146.0-alpha.9.2 only; future versions remain subject to regression testing. "
     "ATS-018-1/2/3 pass; 018-4/5/6/7 are not yet all recorded, so DEC-P13 is NOT "
     "promoted -- the PRD conditions promotion on all seven checks AND a PRD revision."),
    ("E6", "Both hosts discover the same minimal canonical Skill", MANUAL_REQUIRED,
     "CLAUDE HALF PASSED (M1.4A, ATS-018-3): `claude --plugin-dir <root> plugin details "
     "agent-harness@inline` returned a component inventory listing Skills (1) "
     "m1-discovery-fixture, with Agents/Hooks/MCP/LSP all 0 and no production Skill "
     "name present. Non-interactive, no model invoked. This is DISCOVERY, not "
     "invocation -- the fixture was never run and the marker was neither expected nor "
     "claimed. CODEX HALF NOT RUN (ATS-018-4): no `skill` subcommand exists and "
     "`codex exec` would invoke a paid model. Cache-file presence is explicitly NOT "
     "accepted as discovery evidence. E6 requires BOTH halves, so it stays non-Passed."),
    ("E7", "Codex manifest `skills` format is no longer an unknown", PASSED,
     "Documented format `\"skills\": \"./skills/\"` encoded in codex-plugin.schema.json "
     "as a string with a path-shape pattern; an array is rejected (NS-06)."),
    ("E8", "All valid fixtures pass", PASSED,
     "12/12 deterministic validators pass; pytest 103 passed, 1 skipped (M1.3.1). All "
     "five baseline documents validate cleanly (test_baselines_are_valid), and both "
     "documented OpenAI local source forms validate."),
    ("E9", "Each invalid fixture fails for its intended reason", PASSED,
     "52 schema-mutation scenarios plus filesystem/boundary scenarios, each asserting "
     "one stable diagnostic code rather than prose. M1.3.1 withdrew NS-42 (it asserted "
     "an evidence-incorrect contract) and added NS-46..NS-64 covering source shapes and "
     "restored kebab-case identifiers. See the coverage table in docs/m1-remediation.md."),
    ("E10", "Validation runs without network access where possible", PASSED,
     "Offline CI job blocks sockets and runs validate_all.py. Dependency installation "
     "is a separate, prior step and is not a validator network dependency."),
    ("E11", "No paid model invocation is required in normal CI", PASSED,
     "Neither workflow configures a model API key or invokes a model. Model-requiring "
     "tests are marked `manual` and excluded by marker."),
    ("E12", "Marketplace Candidates A, B and C each recorded, selection "
            "evidence-backed", BLOCKED,
     "M1.3: Candidate C now PASSES Codex marketplace registration after the DEF-001 fix, "
     "and passes Claude strict validation. Still missing: ChatGPT Desktop surface for "
     "all three candidates, and Codex/desktop evidence for A and B. Candidate B cannot "
     "be selected without positive evidence on every mandatory surface. "
     "DEC-P14 stays Proposed."),
    ("E13", "Hook-root behaviour tested separately from Skill-script behaviour",
     MANUAL_REQUIRED,
     "Separation IMPLEMENTED and still enforced. M1.2: Codex CLI IS available, but "
     "firing a hook or executing a Skill both require a session that invokes a paid "
     "model, which M1.2 forbids automatically. Neither experiment EXECUTED. "
     "Static fixture validation remains Passed; runtime remains Manual Required."),
    ("E14", "Manual host tests are clearly separated from deterministic CI tests",
     PASSED,
     "pytest markers deterministic / host_cli / manual with --strict-markers; CI runs "
     "`-m 'not manual and not host_cli'`; validate_all.py states it excludes manual "
     "tests; docs/m1-experiments.md records them as pending."),
    ("E15", "No production implementation of the seven planned Skills exists", PASSED,
     "All seven placeholder directories removed from the installable root. "
     "validate_skills fails on any of the seven names (NS-20). Zero .py files under "
     "the plugin root."),
    ("E16", "No user-level configuration was changed", PASSED,
     "No CONFIGURATION changed: real ~/.codex/config.toml contains only pre-existing "
     "openai-bundled/openai-primary-runtime marketplaces -- no agent-harness entry. No "
     "plugin installed to the real cache. All M1.2 marketplace/plugin state landed in an "
     "isolated CODEX_HOME. DISCLOSED: every codex invocation incidentally writes "
     "~/.codex/logs_2.sqlite-wal, models_cache.json and 3 ~/.codex/tmp helper files; "
     "CODEX_HOME does not redirect those. Logs/cache/temp are not configuration."),
    ("E17", "No secret or complete environment dump is stored in artifacts", PASSED,
     "Hook probe reports booleans only, by construction. redact() strips home paths and "
     "credential shapes from every captured output before recording."),
]


def validate_table() -> list[str]:
    problems = []
    seen = set()
    for cid, _, state, evidence in CRITERIA:
        if state not in VALID_STATES:
            problems.append(f"{cid}: invalid state {state!r}")
        if cid in seen:
            problems.append(f"{cid}: duplicate criterion id")
        seen.add(cid)
        if not evidence.strip():
            problems.append(f"{cid}: no evidence recorded")
    expected = {f"E{i}" for i in range(1, 18)}
    missing = sorted(expected - seen, key=lambda s: int(s[1:]))
    extra = sorted(seen - expected)
    if missing:
        problems.append(f"missing criteria: {missing}")
    if extra:
        problems.append(f"unexpected criteria: {extra}")
    return problems


def counts() -> dict[str, int]:
    tally = collections.Counter(state for _, _, state, _ in CRITERIA)
    return {state: tally.get(state, 0) for state in
            (PASSED, FAILED, BLOCKED, NOT_AVAILABLE, MANUAL_REQUIRED)}


def phase_label() -> str:
    """Only 'M1 complete' when every criterion is Passed."""
    return ("M1 complete" if counts()[PASSED] == len(CRITERIA)
            else "M1 scaffold complete, host verification pending")


def markdown() -> str:
    lines = ["| ID | Criterion | Status | Evidence |", "| :--- | :--- | :--- | :--- |"]
    for cid, requirement, state, evidence in CRITERIA:
        mark = f"**{state}**" if state == PASSED else state
        lines.append(f"| {cid} | {requirement} | {mark} | {evidence} |")
    tally = counts()
    lines += [
        "",
        f"**Total criteria: {len(CRITERIA)}**",
        "",
        "| Status | Count |",
        "| :--- | ---: |",
    ]
    for state in (PASSED, FAILED, BLOCKED, NOT_AVAILABLE, MANUAL_REQUIRED):
        lines.append(f"| {state} | {tally[state]} |")
    lines.append(f"| **Sum** | **{sum(tally.values())}** |")
    lines += [
        "",
        f"**Met (Passed only): {tally[PASSED]} of {len(CRITERIA)}**",
        "",
        f"**Phase: {phase_label()}**",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", action="store_true", help="emit the markdown table")
    args = parser.parse_args()

    problems = validate_table()
    if problems:
        print("FAIL m1_status: the criteria table is malformed", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    if args.markdown:
        print(markdown())
        return 0

    tally = counts()
    total = len(CRITERIA)
    assert sum(tally.values()) == total, "tally must sum to the number of criteria"
    for cid, _, state, _ in CRITERIA:
        print(f"  {cid:4s} {state}")
    print()
    for state, n in tally.items():
        print(f"  {state:16s} {n}")
    print(f"\n  total criteria   {total}")
    print(f"  met (Passed)     {tally[PASSED]} of {total}")
    print(f"\n  phase: {phase_label()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
