#!/usr/bin/env python3
"""Deterministic marketplace catalog generation -- Candidate C only (PKG-9, TST-017).

Reads marketplace/marketplace.source.json and emits the host-native catalogs.
Generation is deterministic: same input, byte-identical output, every time. That is
what lets golden-file tests catch drift between the source and the generated files.

M1.1 STATUS: Candidate C is the PROVISIONAL IMPLEMENTATION STRATEGY. Both native
catalogs are generated from marketplace/marketplace.source.json and are byte-compared
in CI, so neither is hand-maintained (PRIN-10, PKG-9).

That is an implementation choice, not an architecture decision. DEC-P14 remains
Proposed: selecting a candidate requires host evidence from ATS-022, and Candidate B
cannot be chosen at all until every mandatory host surface is positively verified.
Candidate C was adopted provisionally because it is the only option that avoids two
hand-edited catalogs while that evidence is still missing.

Usage:
    generate_marketplaces.py --check      compare against on-disk catalogs, exit 1 on drift
    generate_marketplaces.py --write DIR  write generated catalogs under DIR
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import REPO_ROOT, Report, atomic_write_text, load_json  # noqa: E402

SOURCE = "marketplace/marketplace.source.json"
CLAUDE_OUT = ".claude-plugin/marketplace.json"
CODEX_OUT = ".agents/plugins/marketplace.json"


def render(source: dict) -> dict[str, str]:
    """Produce both catalogs from the canonical source. Pure function -- no I/O, no clock.

    The canonical source carries semantic concepts; this function maps them onto each
    host's published field names:

        installation_availability -> OpenAI policy.installation
        authentication_timing     -> OpenAI policy.authentication
        source_path               -> Claude 'source' string, OpenAI 'source' object

    Claude publishes no equivalent of the OpenAI policy fields, so they are NOT emitted
    into the Claude catalog. Emitting them would assert a contract Claude does not define.

    Every value is read from the canonical source with `[...]`, never `.get(..., default)`.
    A missing concept must fail loudly here rather than be silently defaulted -- that
    silent default is precisely how DEF-001 shipped an invalid catalog.
    """
    meta = source["marketplace"]
    plugins = source["plugins"]

    claude = {
        "name": meta["name"],
        "description": meta["description"],
        "owner": meta["owner"],
        "plugins": [
            {
                "name": p["name"],
                # Claude documents `source` as a repo-relative string.
                "source": p["source_path"],
                "description": p["description"],
                "version": p["version"],
                "category": p["category"],
            }
            for p in plugins
        ],
    }
    codex = {
        "name": meta["name"],
        "interface": {"displayName": meta["display_name"]},
        "plugins": [
            {
                "name": p["name"],
                # OpenAI documents TWO local forms: this object, and a plain string
                # path. Both are valid; the host accepted both and resolved them
                # identically. Emitting the object is a LOCAL CHOICE, not a vendor
                # requirement -- it names the source type explicitly, leaves room for
                # non-local types later, and maps field-for-field from the canonical
                # model. M1.3 justified this by calling the string form undocumented,
                # which was wrong; the choice stands on its own merits.
                "source": {"source": "local", "path": p["source_path"]},
                "description": p["description"],
                "version": p["version"],
                "category": p["category"],
                "policy": {
                    "installation": p["installation_availability"],
                    "authentication": p["authentication_timing"],
                },
            }
            for p in plugins
        ],
    }
    # sort_keys=False keeps field order stable and readable; indent fixed at 2.
    return {
        CLAUDE_OUT: json.dumps(claude, indent=2, ensure_ascii=False) + "\n",
        CODEX_OUT: json.dumps(codex, indent=2, ensure_ascii=False) + "\n",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="compare generated output to disk")
    group.add_argument("--write", metavar="DIR", help="write generated catalogs under DIR")
    args = parser.parse_args()

    report = Report("generate_marketplaces")
    source = load_json(REPO_ROOT / SOURCE, report)
    if source is None:
        return report.finish()

    rendered = render(source)

    # Determinism: rendering twice must produce identical bytes (TST-017).
    if render(source) != rendered:
        report.fail("CATALOG_DRIFT", REPO_ROOT / SOURCE, "generation is not deterministic")
        return report.finish()

    if args.write:
        out_root = pathlib.Path(args.write)
        for rel, text in rendered.items():
            # atomic_write_text pins newline="\n". Writing with the platform default
            # would emit CRLF on Windows and LF elsewhere, so the same input would
            # produce different bytes per platform and drift detection would be noise.
            atomic_write_text(out_root / rel, text)
        print(f"OK   generate_marketplaces (wrote {len(rendered)} catalogs under {out_root})")
        return 0

    # Byte comparison, reading raw so a line-ending change is caught rather than hidden
    # by universal-newline translation.
    for rel, text in rendered.items():
        on_disk = REPO_ROOT / rel
        if not on_disk.is_file():
            report.fail("FILE_MISSING", on_disk, "catalog missing")
            continue
        actual = on_disk.read_bytes()
        expected = text.encode("utf-8")
        if actual != expected:
            hint = ""
            if actual.replace(b"\r\n", b"\n") == expected.replace(b"\r\n", b"\n"):
                hint = " (content matches; line endings differ -- see .gitattributes)"
            report.fail(
                "CATALOG_DRIFT", on_disk,
                "differs from what the canonical source renders" + hint +
                ". This file is generated: edit marketplace/marketplace.source.json, "
                "then regenerate (PKG-9)",
            )
    report.note(
        "Candidate C is the PROVISIONAL implementation strategy: catalogs are generated, "
        "not hand-maintained. DEC-P14 remains Proposed until host evidence is recorded."
    )
    return report.finish()


if __name__ == "__main__":
    sys.exit(main())
