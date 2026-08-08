# Evidence template

The report format for `verify-work`. Headings are the contract; the prose under them
adapts to what happened.

Every example below is `Not Run` / `unverified`. That is deliberate — this document is
read before anything has run, and a template containing a worked `pass` is a sentence
someone can copy into a report describing a run that never happened.

## Format

    # Verification
    
    Verification status: <passed|failed|unverified>
    Overall: <derived one-line summary, optional>
    
    ## Gates
    
    ### <gate-id>
    - Kind: <test|lint|typecheck|build|security|custom>
    - Required: <true|false>
    - Command: ["<argv>", "<argv>"]
    - Working directory: <repository-relative path>
    - Started: <yes|no>
    - Exit code: <integer, or - when unavailable>
    - Duration: <Ns, or - when the host does not expose it>
    - Classification: <pass|fail|error|timeout|skipped|flaky>
    - Timeout: <not reached | exceeded after Ns | n/a>
    - Evidence summary: <bounded excerpt or concise reason>
    
    ## Required-gate summary
    
    ## Optional-gate failures
    
    ## Blockers
    
    ## Redactions
    
    ## Recommended next action

## Two layers, two vocabularies

**`Blocked`** is a pre-execution state and never appears as a Classification. A gate is
blocked when no process was ever attempted: no configured gates, stale approval,
configuration that never became executable, an unsafe repository path, argv the host
cannot represent safely, or no execution capability. Those go in **Blockers**, with
`Started: no` and no classification.

**Classification** describes what a process did once one was attempted:

| Classification | Meaning |
| :--- | :--- |
| `pass` | started, exit code 0 |
| `fail` | started normally, exit code non-zero |
| `error` | executable not found, permission denied, or otherwise unable to execute |
| `timeout` | started, exceeded its timeout, terminated because of it |
| `skipped` | selected, then deliberately not run — budget exhaustion or a PRD-defined skip |
| `flaky` | `rerun-once`, first attempt `fail`, rerun disagreed — **never** promoted to `pass` |

A gate rerun under `flaky_policy: rerun-once` produces **two** gate entries, one per
attempt, each with its own exit code and excerpt.

## verification_status

| Value | Condition |
| :--- | :--- |
| `passed` | every required gate is `pass` |
| `failed` | any required gate is `fail`, `error`, or `timeout` |
| `unverified` | any required gate is `skipped`, `flaky`, pre-execution `Blocked`, or never ran |

`failed` and `unverified` are not interchangeable. `failed` means the checks ran and
something is wrong with the work. `unverified` means the checks established nothing, so
the work's state is simply unknown — which is the more dangerous one to report as if it
were success.

`Overall` is optional and **derived**. It never replaces `verification_status` or the
per-gate classifications.

## Field meanings

| Field | Note |
| :--- | :--- |
| Command | the **argv array**, exactly as configured — never a reconstructed shell string |
| Working directory | repository-relative; never an absolute user path |
| Started | whether a process launch was attempted |
| Exit code | the observed code; `-` when no process ran or none was produced |
| Duration | when the host exposes it |
| Classification | one of the six above; absent for a pre-execution `Blocked` gate |
| Timeout | whether the bound was reached, and after how long |
| Evidence summary | bounded: a failure reason, the relevant tail, or a test summary |

## Section meanings

**Required-gate summary** — each required gate and its classification. If
`verification_status` is not `passed`, state plainly whether the work is *failed* or
*unverified*, and name the gates responsible.

**Optional-gate failures** — optional gates not classified `pass`. These never change
`verification_status`, and are never omitted. An empty section says "none".

**Blockers** — gates that never reached a process launch, each with its reason. These are
layer 1, not classifications.

**Redactions** — word it as *"potential secret-like values were redacted"*; do not claim
the output is certainly clean.

**Recommended next action** — the single next step, and who takes it.

## Illustrative fragment

Illustrative only. Nothing here was executed.

    # Verification
    
    Verification status: unverified
    Overall: awaiting execution approval
    
    ## Gates
    
    ### py-test
    - Kind: test
    - Required: true
    - Command: ["python", "-m", "pytest", "-q"]
    - Working directory: .
    - Started: no
    - Exit code: -
    - Duration: -
    - Classification: -
    - Timeout: n/a
    - Evidence summary: awaiting execution approval for the displayed gate set
    
    ## Required-gate summary
    1 required gate configured, 0 attempted. Verification status: unverified —
    nothing has been established about this work.
    
    ## Optional-gate failures
    None.
    
    ## Blockers
    None yet — execution has not been approved.
    
    ## Redactions
    None; no output has been produced.
    
    ## Recommended next action
    Review the gate set above and approve it if it is correct.
