# Security model

**M1 placeholder.** Written in M5.

Will document the threat model and controls in operational terms. The full
analysis is in `docs/PRD.md` §19.

Already enforced in M1:

- runtime code cannot reach the network (`check_no_network.py`)
- nothing writes to user-scope configuration (`test_experiment_hygiene.py`)
- experiment artifacts carry booleans, never environment values (`SEC-22`)
- no credential-shaped strings anywhere in the repository
- the mutating Skill keeps two independent approval gates
