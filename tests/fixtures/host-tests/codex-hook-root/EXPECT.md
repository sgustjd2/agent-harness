# Expected behaviour -- experiment A (ATS-028)

Records presence booleans for `PLUGIN_ROOT`, `PLUGIN_DATA` and the compatibility
variables, plus whether each path stays inside the installed plugin root and data
directory. No model invocation is required, so this runs in CI.

**Constraints (SEC-22):** no real user repository is modified, nothing is written
outside a temporary directory, and no secrets or complete environment dumps are stored.

**Scope limit:** this answers the hook question only. Its result must not be used as
evidence for Skill-context path resolution (experiment B, ATS-020).
