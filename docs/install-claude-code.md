# Installing agent-harness in Claude Code

**Read the status table first.** Some steps below have been run against a real host and
some have not, and the difference matters more than the instructions do.

| Step | Status |
| :--- | :--- |
| Development load (`--plugin-dir`) | **Observed** — Claude Code 2.1.195 |
| Component discovery after loading | **Observed** — 2.1.195 |
| Marketplace registration | **Documented, not exercised** |
| Marketplace installation | **Documented, not exercised** |
| Invoking a Skill | **Not run** — it needs a paid model call |

Everything marked *not exercised* comes from vendor documentation. It is expected to
work; nobody here has watched it work. ATS-001 is the manual test that would change
those rows, and until someone runs it this page is a plan as much as a procedure.

## Requirements

Claude Code, and a network path to GitHub for the marketplace route. Nothing else — the
plugin has no dependencies, ships no executable, and makes no network call of its own.

## Two surfaces, same operations

Steps 1 and 2 are written as **slash commands**, typed inside a Claude Code session.
Each has a CLI equivalent — `claude plugin marketplace add`, `claude plugin install` —
and `claude plugin --help` lists the full set. Use whichever suits you; they do the same
thing. The checks further down use the CLI form because that is the form that was run.

## Registration and installation are two steps

They complete back to back, which makes them look like one. They are not: registering a
marketplace tells Claude Code where a catalog lives, and installing takes a plugin from
that catalog. Registration alone gives you nothing to invoke.

### 1. Register the marketplace

```
/plugin marketplace add sgustjd2/agent-harness
```

### 2. Install the plugin

```
/plugin install agent-harness@agent-harness
```

The form is `<plugin>@<marketplace>`. Both are named `agent-harness`, which is a naming
coincidence rather than a syntax quirk.

If the install summary asks for a reload, run `/reload-plugins`.

## 3. Check what actually loaded

```
claude plugin details agent-harness@agent-harness
```

Expect **Skills 8** and **Agents 6**.

Eight, not seven: the seven production Skills plus `m1-discovery-fixture`, a compatibility
fixture that does nothing on purpose. Six agents are the role subagents added in M3 — a
lower number means the role definitions did not load, and this is the one check that costs
nothing to run.

The seven you can invoke:

| Skill | For |
| :--- | :--- |
| `/agent-harness:init-project` | set up `.agent-harness/` in a repository |
| `/agent-harness:plan-work` | turn a goal into a plan with completion criteria |
| `/agent-harness:orchestrate` | carry out a plan that is ready |
| `/agent-harness:verify-work` | run the verification gates in `config.yaml` |
| `/agent-harness:doctor` | diagnose the harness itself |
| `/agent-harness:refine-harness` | turn recorded run evidence into one proposal |
| `/agent-harness:apply-refinement` | apply one proposal that was approved |

## 4. Confirm it changed nothing

```
git status
```

Installing must leave your repository byte-identical. Nothing is written to a project
until you invoke `init-project` and approve what it proposes.

If `git status` differs before and after installation, stop and report it — that is a
defect in this plugin, not a step you missed.

## Development load, without installing

This is the path that has actually been run:

```
claude --plugin-dir /path/to/agent-harness/plugins/agent-harness plugin list --json
```

It loads the plugin at **session scope**, creates no installed record, and leaves
`~/.claude/settings.json` untouched. Paths containing spaces work.

Use it to try the plugin, to develop against a checkout, or when you would rather not
register a marketplace at all.

## Restricted networks

`/plugin marketplace add` accepts a local path as well as a GitHub reference, so a clone
placed on disk by any means you already trust can be registered without further network
access. The plugin itself never reaches the network at any point.

## Pinning a version

The catalog carries an explicit `version`. Pin by installing from a checkout of the tag
you want — via `--plugin-dir`, or by registering that checkout as a local marketplace.

There is no published release yet. The current version is `0.0.1` and the plugin is
**experimental**: three M1 exit criteria remain unmet, all needing host access, and the
end-to-end pilot has not been run.

## If something is wrong

Run `/agent-harness:doctor`. It is read-only — it inspects, reports, and repairs nothing —
and it reports a check whose preconditions are unmet as *not applicable* rather than as a
failure, so a fresh installation does not look broken.

## Uninstalling

```
claude plugin uninstall agent-harness@agent-harness
```

That removes the plugin. It does not remove `.agent-harness/` from any repository, which
is deliberate: that directory holds your configuration and memory, it is yours, and
uninstalling a tool is not a request to delete the work done with it. Remove it by hand
when you actually want it gone.
