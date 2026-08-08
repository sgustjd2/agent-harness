# Contributing to agent-harness

## Setup

```bash
python -m venv .venv
```

```bash
.venv/bin/pip install -r requirements-dev.txt
```

Python 3.10+ required. Install into the virtual environment, never globally.

## Before you push

```bash
python scripts/validate_all.py
```

---

## Dependency policy

**Runtime: zero third-party dependencies.** No exceptions. This is what lets a security
reviewer approve the plugin by reading it. CI asserts the plugin root declares no
`requirements.txt`, `pyproject.toml`, `package.json` or lockfile.

**Development validation: established libraries, not hand-written approximations.**

| Concern | Library | Entry point |
| :--- | :--- | :--- |
| YAML | PyYAML | `yaml.safe_load` |
| JSON Schema | jsonschema | validator class from each schema's `$schema` |
| Tests | pytest | `python -m pytest` |

M1 originally shipped a hand-written YAML subset parser and a hand-written JSON Schema
subset validator. Both were removed in M1.1. The reason is worth keeping in mind when
you are tempted to write another one: **an approximation of a standard can disagree with
the real implementation while still reporting success.** Replacing them immediately
exposed three defects they had hidden — a path-traversal hole in a schema pattern, UNC
paths misreported as absolute, and non-deterministic generation on Windows.

`scripts/preflight.py` is the one standard-library-only checker that remains. It is
labeled non-authoritative in its own output, checks only file readability, JSON syntax
and path shape, and never judges anything the authoritative validators judge — so it
cannot silently disagree with them. **Its result is not schema validation.**

---

## Adding a check

```python
from _common import Report, main

def check(root=DEFAULT) -> int:
    report = Report("check_name")
    ...
    report.fail("STABLE_CODE", path, "specific reason")
    return report.finish()

if __name__ == "__main__":
    main(check)
```

Three rules:

1. **`check()` takes a root argument.** That is what lets tests point it at a fixture tree.
2. **Every failure carries a stable diagnostic code** from `scripts/_diagnostics.py`.
   Tests assert on codes, never prose, so wording can improve without breaking the suite.
3. **Each validator runs exactly once** in `validate_all.py`. Re-running a check to raise
   a total makes the summary meaningless.

### Every new check needs a negative scenario

Add a case to `tests/test_negative_scenarios.py` asserting the one primary code it
should produce, and add a row to the coverage table in `docs/m1-remediation.md`. A check
without a negative test has never been shown to fire.

---

## Handling experiment artifacts

Experiment records are committed, so hygiene is a security matter.

**Never record:** the value of an environment variable, a full environment dump,
credentials, or absolute paths containing a username.

**Do record:** host name and version, the command, the exit code, a sanitised output
summary, and `pass` / `fail` / `not-run`.

`scripts/_common.py` provides `redact()` and `bounded()`; every captured host output
goes through them. The hook probe reads the environment into local booleans and its
reporting step touches only those, so no value can reach stdout by construction.

**A negative result is valid. An unrecorded result is not.** `not-run` is honest; a
blank row is not.

---

## Repository invariants

| Invariant | Enforced by |
| :--- | :--- |
| Nothing in the plugin references anything outside it | `check_path_containment.py` |
| No production Skill in the installable root | `validate_skills.py` |
| Exactly one fixture Skill in the installable root | `validate_skills.py` |
| Skill frontmatter is `name` + `description` only | `validate_skills.py` |
| Canonical Skills assume no host path, cache path, `PLUGIN_ROOT`, or cwd | `check_path_portability.py` |
| Runtime code cannot reach the network | `check_no_network.py` |
| Undocumented host commands stay out of user-facing docs | `check_no_install_command.py` |
| Catalogs are generated, never hand-edited | `generate_marketplaces.py --check` |
| One version across all five version-bearing files | `check_version_sync.py` |

### Two that deserve explanation

**Why can't a Skill use `PLUGIN_ROOT`?** It is documented for plugin **hook** commands.
It is not documented as inherited by commands a Skill starts. Treating the first as
evidence for the second is precisely what `check_path_portability.py` exists to prevent.

**Why can't I edit `.claude-plugin/marketplace.json`?** It is generated. Edit
`marketplace/marketplace.source.json` and regenerate. Two hand-maintained catalogs drift,
and the drift is invisible until a user on one host gets a different version.

**Why can't I add a field to a compatibility schema because it seems right?** Because
that is exactly how DEF-001 happened. M1.1 invented `policy.install` and
`authentication: "none"`, the local schema validated them happily, and CI enforced the
fiction until a real host rejected it. Every enum value in
`core/schemas/*-marketplace.schema.json` must trace to a row in the contract table in
`docs/m1-defects.md`, labelled Official-Documented, Host-Observed or Local-M1-Policy.

**Host acceptance is not validity.** The host accepted `policy.install` with a
deliberately bogus value — that proves it ignores the key, not that the key is real.

**Why can't I *remove* a constraint because it seems invented?** Because M1.3 did, and it
was wrong. Auditing DEF-001, it deleted kebab-case from the Claude marketplace `name` and
`plugins[].name` as unfounded inventions. Both are documented by the vendor, whose
validator rejects uppercase and spaces outright. For one milestone our schemas accepted
`"Agent Harness"` as an identifier. Only the `category` pattern was genuinely invented.

Removing a constraint therefore takes the **same** evidence as adding one:

1. cite the vendor page showing the constraint is not required, or that the field is a
   free-form label rather than an identifier;
2. add or update a test that fails without your change;
3. record the removal in the contract table in `docs/m1-defects.md` with the label
   **Removed**.

"I couldn't find where this came from" is a prompt to go and check the vendor
documentation, not a finding. Being narrower than the vendor is allowed and sometimes
right — it just has to be labelled Local-M1-Policy and never described as the vendor's
rule.

**A derived rule needs the derivation checked.** The OpenAI marketplace entry name is
required to be kebab-case, but the vendor never published that rule for a *catalog* field -
it publishes it for the plugin *manifest* name, and the catalog entry inherits it by having
to name the same plugin. That is a legitimate basis, provided identity parity is actually
enforced. It was true but untested until M1.4A, which means the schema comment cited a
derivation nothing verified. If you justify a constraint by deriving it from another rule,
add the test for that other rule in the same change.

**Distinguish identifiers from labels.** Marketplace and plugin `name` fields are
documented kebab-case identifiers on both hosts. `category`, `interface.displayName`,
descriptions and owner display names are free-form: never apply a case pattern to them.

**Two shapes can both be documented.** OpenAI accepts an object *and* a plain string for a
local `source`. The generator emits the object because this repository chose one shape,
not because the other is invalid — so the schema accepts both, and the choice is recorded
as Local-M1-Policy. When a local rule is narrower than the contract, say which is which.

---

## What this milestone does not accept

- production behaviour in any of the seven planned Skills — that is M2
- a production Skill directory in the installable plugin root — at all
- hooks, agents, MCP config, or helper scripts in the installable plugin root
- release automation — that is M8
- writes to user-scope configuration (`~/.claude`, `~/.codex`, `~/.agents`) — ever
- a hand-written parser or validator for a published standard
