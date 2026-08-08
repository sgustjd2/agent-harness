# Initialization checklist

Phase A before showing the proposal, Phase B before and after writing. Any "no" stops
the run — this Skill changes a repository, so an unchecked box is a file someone did not
agree to.

## Before proposing

- [ ] The repository was **inspected before anything was proposed**. No file was created,
      modified, or deleted during inspection.
- [ ] Existing `.agent-harness/` content was read, and each target classified as
      create / unchanged / append / conflict.
- [ ] Project type was inferred conservatively, and every inference is listed as an
      assumption rather than a fact.
- [ ] Whether this is a Git repository was determined; if not, `vcs: none` is proposed
      and manual rollback is stated.
- [ ] **Every target path is shown exactly**, with its action, reason, and overwrite risk.
- [ ] Verification gates are proposed, none enabled, each with a `Not Run` status.
- [ ] **No command was executed** — not to detect a tool, not to check a version.

## Approval

- [ ] Approval is **specific to this proposal**, given after it was displayed.
- [ ] Explicit Skill invocation was **not** treated as mutation approval.
- [ ] A general "go ahead" given before the proposal was shown was not treated as
      approval either.
- [ ] Targets were **re-checked immediately before writing**.
- [ ] If anything changed since the proposal, the run **stopped** and re-proposed.
      **Stale approval is rejected, not reused**: an approval refers to the state it was
      shown for, so once that state moves it approves nothing.

## While writing

- [ ] Only paths under `.agent-harness/`, plus append-only marker blocks in `CLAUDE.md`
      and `AGENTS.md`, were touched.
- [ ] **No existing non-empty file was overwritten.**
- [ ] No configuration was silently merged.
- [ ] No marker block was duplicated; an existing block was updated in place, and only
      when its content would actually change.
- [ ] The marker block stays under 2 KiB.
- [ ] Nothing was deleted.
- [ ] **Git ignore policy**: ignores were written to `.agent-harness/.gitignore`, the
      self-contained file, and the repository's own root `.gitignore` was left alone.
      Its four lines are `runs/`, `proposals/`, `*.tmp`, `.migration-backup/` — with
      `runs/` omitted only when the user set `runs.commit_evidence: true`, and the leak
      tradeoff stated when they do.
- [ ] No package installed, no plugin installed, no marketplace registered, no network
      access, no agent template copied.
- [ ] **No user-scope path was written** — `~/.claude/`, `~/.codex/`, `~/.agents/`.
- [ ] No source, build config, package manifest, CI workflow, plugin manifest,
      marketplace catalog, or anything under `.git/` was touched.
- [ ] No secret, token, or absolute user path was written into any generated file.

## Idempotency

- [ ] Existing valid files were reported **unchanged**, not rewritten.
- [ ] Only missing approved files were created.
- [ ] A second run against the result produces **no diff**. That is the actual test —
      run it twice and compare.

## Reporting

- [ ] Every path is reported as created, unchanged, skipped, conflicted, or failed.
- [ ] Conflicts name the file and why, not just a count.
- [ ] **Success is not claimed when any required file failed to write.** A partial
      initialization is a defect: clean up what this run created, report the cause and
      the manual steps, and say the repository is not initialized.
