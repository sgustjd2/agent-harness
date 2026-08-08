# Candidate C -- canonical source, generated native catalogs

One host-neutral source is maintained. `scripts/generate_marketplaces.py` emits both
native catalogs deterministically; generated files are never hand-edited (PKG-9), and
golden-file tests block drift (TST-017).

Per PRD §10.3 this is the default choice unless Candidate B is fully verified.
