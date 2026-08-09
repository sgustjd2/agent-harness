# Installing agent-harness in Codex and the OpenAI surfaces

**Read the status table first.** Less has been run against a real host here than on the
Claude side, and the difference matters more than the instructions do.

| Step | Status |
| :--- | :--- |
| Marketplace registration (CLI) | **Observed** — codex-cli 0.146.0-alpha.9.2, isolated |
| Registration ≠ installation | **Observed** — the plugin read `not installed` immediately after |
| Dual-manifest root accepted | **Observed** |
| Installation via ChatGPT desktop | **Documented, not exercised** |
| Skill discovery and `$` invocation | **Not run** — E6, still open |
| Everything below about templates | **Documented procedure, not exercised** |

The one observation that constrains all of this: **registering a marketplace is not
installing a plugin.** They are separate lifecycle steps, and this page keeps them apart
because the host does.

An alpha is not a cross-version contract. Anything that worked once, on one build, is
recorded that way rather than promoted to a rule.

## 1. Register the marketplace source (CLI)

```bash
codex plugin marketplace add sgustjd2/agent-harness
```

Other documented forms:

| Command | Purpose |
| :--- | :--- |
| `codex plugin marketplace add sgustjd2/agent-harness --ref main` | pin a branch or tag |
| `codex plugin marketplace add ./path/to/checkout` | register a local directory |
| `codex plugin marketplace list` | list registered sources |
| `codex plugin marketplace upgrade` | refresh sources |
| `codex plugin marketplace remove agent-harness` | deregister |

The repository-scope catalog lives at `.agents/plugins/marketplace.json`, which is why
`--sparse .agents/plugins` works against a repository holding several plugins.

After this step the host knows the plugin **exists**. Nothing is installed, nothing is
enabled, and no Skill is callable.

## 2. Install and enable (ChatGPT desktop app)

Open **Plugins**, find agent-harness in the directory the registered marketplace exposes,
and install it. It becomes selectable after a restart.

**No CLI installation command is documented.** One existed and worked on
0.146.0-alpha.9.2, but it is not in the published packaging documentation as the stable
path, so this guide does not print it as a step to copy. If your build offers one, that is
your build's behaviour, not a contract this project relies on.

## 3. Fallback where there is no installation surface

Copy `plugins/agent-harness/skills/` into `.agents/skills/` at your repository root.

This costs the plugin lifecycle — no version, no upgrade, no uninstall — and you own the
copy from then on. It **keeps Gate A**, because each Skill's invocation policy travels
inside its own directory rather than in the manifest.

## 4. Check what loaded

Explicit invocation is `$<skill>` in Codex and IDEs, `@<skill>` in ChatGPT.

| Skill | For |
| :--- | :--- |
| `$init-project` | set up `.agent-harness/` in a repository |
| `$plan-work` | turn a goal into a plan with completion criteria |
| `$orchestrate` | carry out a plan that is ready |
| `$verify-work` | run the verification gates in `config.yaml` |
| `$doctor` | diagnose the harness itself |
| `$refine-harness` | turn recorded run evidence into one proposal |
| `$apply-refinement` | apply one proposal that was approved |

An eighth Skill, `m1-discovery-fixture`, is present and does nothing by design.

**Whether the host offers any of them is untested (E6).** Registration shows the files
arrive; nothing yet shows they are callable. If `$doctor` does not resolve, that is the
open question showing itself, not a mistake you made.

Installing must leave your repository byte-identical — `git status` before and after.

## 5. Optional role templates

Six TOML files ship at `plugins/agent-harness/adapters/codex/agent-templates/`, one per
role: coordinator, researcher, implementer, reviewer, tester, refiner.

**You do not need them.** The Skills carry the role instructions and work with none
installed. That is the baseline the whole design is built on, not a degraded mode.

What a template adds is a **sandbox mode** — `read-only` for researcher and reviewer,
`workspace-write` for tester. On Codex the role is otherwise held by wording alone, so a
template converts two of the six from a request into a setting.

### Nothing installs them

No Skill copies these files, and none can: `.codex/` and `.claude/` are forbidden write
roots, so a Skill cannot even name the path. A tool that could write a host agent
definition could widen its own permissions for your next session, and you would find out
from a diff, if you looked.

So the copy is yours to make:

```bash
mkdir -p .codex/agents
cp plugins/agent-harness/adapters/codex/agent-templates/researcher.toml .codex/agents/
```

**Project scope, not user scope.** `.codex/agents/` sits in the repository, so the change
appears in `git status` and your team can review it. `~/.codex/agents/` would apply to
every project you touch and show up in no diff — use it only if that is genuinely what you
want, and know that you are opting out of the visibility.

Copy only the roles you want. They are independent.

### Before you copy

Open the file. It is short, and it is about to define an agent that runs in your
repository.

Check that `sandbox_mode` is `read-only` or `workspace-write` and nothing wider, that the
only keys are `name`, `description`, `developer_instructions` and optionally
`sandbox_mode`, and that there is no path, no command and no URL anywhere in it.

`scripts/validate_agent_templates.py` checks exactly that in CI, so a template from this
repository should pass. Read it anyway if you obtained it from a fork — the check runs
where it was written, not where the file came from.

### Removing them

```bash
git rm .codex/agents/researcher.toml
```

Or delete the file, or `git revert` the commit that added it. There is no uninstall step
and nothing tracks state: the file is the installation.

`$doctor` reports which templates it finds, as an observation rather than a verdict — it
does not judge whether installing one was a good idea, because that is your call.

## 6. If something is wrong

Run `$doctor`. Read-only: it inspects, reports, and repairs nothing. A check whose
preconditions are unmet is reported *not applicable* rather than as a failure, so a fresh
installation does not look broken.

If `$doctor` itself does not resolve, you are on the E6 path — record what happened, since
that is the observation this project is still missing.

## 7. Uninstalling

Remove the plugin through the surface that installed it, then deregister the source:

```bash
codex plugin marketplace remove agent-harness
```

Neither step removes `.agent-harness/` from your repository, and neither removes a
template you copied. That is deliberate: those hold your configuration, memory and
choices. Uninstalling a tool is not a request to delete the work done with it.
