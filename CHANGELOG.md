# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### M1.1 — scaffold correction and scope audit

Corrective pass over the M1 scaffold. **M2 has not begun.**

#### Changed

- **Development validation now uses established libraries.** The hand-written YAML
  subset parser and hand-written JSON Schema subset validator were removed in favour of
  PyYAML (`yaml.safe_load`) and jsonschema. The plugin runtime remains dependency-free.
- **pytest is the authoritative test runner.** `run_all.py` became `validate_all.py`,
  which orchestrates the 12 deterministic validators and then invokes pytest.
- Catalogs are now **generated** from `marketplace/marketplace.source.json` rather than
  hand-maintained (Candidate C, provisional implementation strategy only).
- Renamed `check_packaging.py` to `check_path_containment.py` and
  `check_release_version.py` to `check_version_sync.py`.

#### Added

- Five packaging schemas: claude-plugin, codex-plugin, claude-marketplace,
  openai-marketplace, canonical-marketplace. None existed before.
- Stable diagnostic codes (`scripts/_diagnostics.py`); tests assert codes, not prose.
- 27 negative scenarios, up from 16.
- `scripts/m1_status.py`, which computes exit-criteria counts from a structured table.
- `requirements-dev.txt`, `pyproject.toml` with pytest markers, `.gitattributes`.
- `docs/m1-remediation.md`, `docs/m1-decisions.md`, `docs/m1-experiments.md`,
  `docs/m1-traceability.md`.

#### Removed

- All seven production Skill placeholders from the installable plugin root.
- `.github/workflows/release.yml` — release automation is an M8 deliverable.
- `agents/`, `scripts/`, `core/roles/`, `core/workflows/`, `adapters/codex/agent-templates/`
  from the installable plugin root.
- Empty M2/M5/M6 stub trees under `tests/`.

#### Fixed

Three defects the hand-written tooling had hidden:

- a path-traversal hole: `./../skills/` matched the schema path pattern
- UNC paths reported as absolute rather than UNC
- catalog generation emitted CRLF on Windows, so output was not byte-deterministic

#### Corrected

- Exit-criteria arithmetic. The prior report claimed 12 of 17 while listing 11.
  The count is now computed programmatically: **13 of 17**.

## [0.0.1] - 2026-08-08

M1 — repository and validation scaffold. No production Skill behaviour.

[Unreleased]: https://github.com/OWNER/agent-harness/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/OWNER/agent-harness/releases/tag/v0.0.1
