# Evidence template

The report format for `verify-work`. Headings are the contract; the prose under them
adapts to what happened.

Every status shown below is `Not Run`. That is deliberate — this document is read before
anything has run, and a template containing a worked `Passed` example is a sentence
someone can copy into a report describing a run that never happened.

## Format

    # Verification
    
    Overall: <Passed|Failed|Blocked|Not Run>
    
    ## Gates
    
    ### <gate-id>
    - Kind: <test|lint|typecheck|build|security|custom>
    - Required: <true|false>
    - Command: ["<argv>", "<argv>"]
    - Working directory: <repository-relative path>
    - Status: Not Run
    - Exit code: <integer, or - when the process never started>
    - Timeout: <not reached | exceeded after Ns | n/a>
    - Evidence summary: <bounded excerpt or concise reason>
    
    ## Required-gate summary
    
    ## Optional-gate failures
    
    ## Blockers
    
    ## Redactions
    
    ## Recommended next action

## Field meanings

| Field | Note |
| :--- | :--- |
| Overall | computed from **required** gates only; see the execution contract |
| Kind | the configured gate kind |
| Required | whether the overall result depends on this gate |
| Command | the **argv array**, exactly as configured — never a reconstructed shell string |
| Working directory | repository-relative; never an absolute user path |
| Status | `Not Run`, `Passed`, `Failed`, or `Blocked` |
| Exit code | the observed code; `-` when the process never started |
| Timeout | whether the bound was reached, and after how long |
| Evidence summary | bounded: a failure reason, the relevant tail, or a test summary |

## Section meanings

**Required-gate summary** — which required gates ran and how each ended. If any did not
pass, state plainly that the work is **unverified** and name them.

**Optional-gate failures** — optional gates that did not pass. These never flip the
overall result on their own, and they are never omitted. An empty section says "none",
it is not deleted.

**Blockers** — every gate that could not safely start, each with its reason: invalid
configuration, unavailable executable, unsafe working directory, argv that could not be
represented safely, missing execution capability, or stale approval.

**Redactions** — whether anything secret-shaped was removed. Word it as *"potential
secret-like values were redacted"*; do not claim the output is certainly clean.

**Recommended next action** — the single next step, and who takes it.

## Illustrative fragment

Illustrative only. Nothing here was executed.

    # Verification
    
    Overall: Not Run
    
    ## Gates
    
    ### py-test
    - Kind: test
    - Required: true
    - Command: ["python", "-m", "pytest", "-q"]
    - Working directory: .
    - Status: Not Run
    - Exit code: -
    - Timeout: n/a
    - Evidence summary: awaiting execution approval for the displayed gate set
    
    ## Required-gate summary
    1 required gate configured, 0 executed. Verification status: unverified.
    
    ## Optional-gate failures
    None.
    
    ## Blockers
    None yet — execution has not been approved.
    
    ## Redactions
    None; no output has been produced.
    
    ## Recommended next action
    Review the gate set above and approve it if it is correct.
