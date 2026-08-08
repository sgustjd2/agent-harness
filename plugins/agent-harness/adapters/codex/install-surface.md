# Codex / OpenAI: registration vs installation

**Registering a marketplace is not installing a plugin.** These are separate lifecycle
steps and this file keeps them separate (PRIN-11, FR-028).

## Step 1 — register the marketplace source (Codex CLI)

Verified commands:

| Command | Purpose |
| :--- | :--- |
| `codex plugin marketplace add owner/repo` | register a GitHub repository as a source |
| `codex plugin marketplace add owner/repo --ref main` | pin to a branch or tag |
| `codex plugin marketplace add https://github.com/example/plugins.git --sparse .agents/plugins` | sparse checkout of the catalog directory |
| `codex plugin marketplace add ./local-marketplace-root` | register a local directory |
| `codex plugin marketplace list` | list registered sources |
| `codex plugin marketplace upgrade [name]` | refresh sources |
| `codex plugin marketplace remove name` | deregister a source |

After this step the host knows the plugin **exists**. Nothing is installed, nothing is
enabled, and no Skill is callable yet.

## Step 2 — install and enable the plugin (ChatGPT desktop app)

Open **Plugins** in the ChatGPT desktop app, browse the directory the registered
marketplace exposes, or open the plugin's detail page under **Created by you**, and
install it. It becomes selectable after a restart.

## Open question

**Whether the Codex CLI alone can complete step 2 is unverified (Q-IMPL-011).** No CLI
subcommand for installing a plugin appears in the documentation reviewed, so none is used
or implied anywhere in this repository. `scripts/check_no_install_command.py` enforces
that by blocking the literal string from operational files — which is why this paragraph
describes it rather than quoting it.

If a CLI-only path is confirmed later, record it here with the host version that provided
it, and update the compatibility matrix.

## Fallback — no installation surface available

Where the desktop app cannot be used, the workflow is still available by copying the
Skills into repository scope:

1. Clone the repository.
2. Copy `plugins/agent-harness/skills/` into `$REPO_ROOT/.agents/skills/`.
3. Codex discovers Skills in repository scope; invoke them with the `$` prefix.

**What this costs.** The plugin lifecycle is lost: no version pinning, no `upgrade`, no
`remove`. Updates become a manual re-copy. Say so plainly to anyone choosing this path.

**What this keeps.** `agents/openai.yaml` sits inside the Skill directory, so it is copied
along with the Skill and **Gate A survives** (PKG-10). The mutating Skill stays
non-implicitly-invocable even on this path.

**Who performs the copy.** The user. No Skill copies itself, and nothing writes to
user-scope configuration (SEC-17).
