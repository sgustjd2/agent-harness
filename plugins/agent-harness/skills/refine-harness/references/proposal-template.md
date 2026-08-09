# Proposal template

The structural shape of `.agent-harness/proposals/<proposal-id>.md`.

Every value below is an **illustrative placeholder**. Nothing here describes a run that
happened, and no evidence reference below resolves — a template containing a plausible
successful run is a paragraph someone can paste into a proposal describing work nobody
did.

## Frontmatter — authoritative

    ---
    schema_version: 1
    proposal_id: YYYYMMDD-HHMMSS-<slug>
    created: <timestamp>
    status: proposed
    source_runs:
      - YYYYMMDD-HHMMSS-<run-slug>
    applied_at: null
    rollback: null
    items:
      - item_id: I-001
        change_type: <fact|decision|pattern|config|role|workflow|skill>
        target_path: <the only permitted target for that change_type>
        current: <existing text, redacted, or null when there is none>
        current_hash: null
        proposed: <replacement text, redacted>
        evidence_refs:
          - YYYYMMDD-HHMMSS-<run-slug>#E-001
        risk: <low|medium|high>
        conflict: false
    ---

The frontmatter is the **source of truth**. The body below it is a summary for a human.

**Do not restate the full item dataset in the body.** Two independently editable copies of
the same data disagree the first time someone edits one of them, and a reviewer has no way
to tell which they are approving.

## Field notes

| Field | Note |
| :--- | :--- |
| `proposal_id` | `YYYYMMDD-HHMMSS-<slug>`; the filename matches it |
| `status` | always `proposed` on creation, never advanced here |
| `source_runs` | at least one; every `evidence_refs` entry must point into one of these |
| `applied_at` / `rollback` | `null` — this Skill applies nothing |
| `item_id` | `I-001`, `I-002`, … in order |
| `target_path` | validated, normalized, repository-contained, and permitted for the change type |
| `current` | the existing text being replaced, redacted; `null` when the item is purely additive |
| `current_hash` | only a hash already trustworthy without running a command, otherwise `null` — **never invented** |
| `evidence_refs` | `<run-id>#<evidence-id>`; at least one, each resolving to real evidence |
| `risk` | `low` / `medium` / `high`; every `skill` item is `high` |
| `conflict` | `true` for a near duplicate or a contradiction |

## Body

    # Refinement proposal <proposal-id>
    
    Status: proposed — nothing here has been applied.
    
    ## Summary
    <a few sentences: what the source runs showed and what these items would change>
    
    ## Conflicts
    <items marked conflict: true, and what the reviewer must decide — or "none">
    
    ## Redactions
    <"potential secret-like values were redacted" when applicable, or "none">
    
    ## Recommended next action
    Review each item against its evidence. Use apply-refinement only after explicit
    review and approval.

## Illustrative fragment

Illustrative only. The run, the evidence id, and the fact are all placeholders.

    items:
      - item_id: I-001
        change_type: fact
        target_path: .agent-harness/memory/facts.md
        current: null
        current_hash: null
        proposed: <one- to three-sentence project fact, citing a repository path>
        evidence_refs:
          - YYYYMMDD-HHMMSS-<run-slug>#E-002
        risk: low
        conflict: false

A duplicate fact looks different — it proposes updating the existing entry's `sources[]`
and `last_confirmed` rather than adding a second entity:

    items:
      - item_id: I-002
        change_type: fact
        target_path: .agent-harness/memory/facts.md
        current: <the existing fact entry, redacted>
        current_hash: null
        proposed: <the same fact with this run added to sources[] and last_confirmed updated>
        evidence_refs:
          - YYYYMMDD-HHMMSS-<run-slug>#E-004
        risk: low
        conflict: false

And a `skill` item is always high risk, and says plainly that a human applies it:

    items:
      - item_id: I-003
        change_type: skill
        target_path: plugins/agent-harness/skills/<skill-name>/SKILL.md
        current: null
        current_hash: null
        proposed: <upstream change text for a human to open as a pull request>
        evidence_refs:
          - YYYYMMDD-HHMMSS-<run-slug>#E-007
        risk: high
        conflict: false
