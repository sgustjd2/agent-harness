#!/usr/bin/env python3
"""No network access from runtime code (FR-024, SEC-01, TST-006).

Static check: nothing under plugins/agent-harness/ may import a networking module
or reference a network-capable helper. This is what lets the product claim no hidden
network access and no telemetry by default -- a claim a security reviewer can verify
without running anything.

M1 ships no runtime Python yet, so this check mainly guards the boundary going forward.
"""

from __future__ import annotations

import ast
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _common import PLUGIN_ROOT, Report, main  # noqa: E402

NETWORK_MODULES = {
    "socket", "ssl", "http", "http.client", "urllib", "urllib.request", "urllib3",
    "ftplib", "smtplib", "poplib", "imaplib", "telnetlib", "xmlrpc", "asyncio.streams",
    "requests", "httpx", "aiohttp", "websockets",
}

# Shelling out to a fetcher would sidestep the import check.
NETWORK_COMMANDS = ("curl ", "wget ", "nc -", "Invoke-WebRequest", "Invoke-RestMethod")

# Telemetry must not exist even as an opt-in switch in the MVP (SEC-02).
TELEMETRY_MARKERS = ("telemetry", "analytics", "phone_home", "usage_report")

NEGATION_MARKERS = ("must not", "does not", "no telemetry", "never", "0건", "forbidden", "without")


def _root_module(name: str) -> str:
    return name.split(".")[0]


def check(plugin_root: pathlib.Path = PLUGIN_ROOT) -> int:
    report = Report("check_no_network")

    py_files = sorted(plugin_root.rglob("*.py"))
    for path in py_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            report.fail(path, f"syntax error, cannot verify imports: {exc}")
            continue
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name in NETWORK_MODULES or _root_module(name) in NETWORK_MODULES:
                    report.fail(
                        path,
                        f"line {node.lineno}: imports networking module {name!r}; runtime code "
                        "must make no network access (FR-024)",
                    )

    for path in sorted(plugin_root.rglob("*")):
        if not path.is_file() or path.suffix not in (".md", ".py", ".yaml", ".yml", ".json"):
            continue
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
        ):
            low = line.lower()
            if any(marker in low for marker in NEGATION_MARKERS):
                continue
            for command in NETWORK_COMMANDS:
                if command.lower() in low:
                    report.fail(path, f"line {lineno}: network command {command.strip()!r}")
            for marker in TELEMETRY_MARKERS:
                if marker in low:
                    report.fail(
                        path,
                        f"line {lineno}: telemetry marker {marker!r}; no telemetry exists in "
                        "the MVP, not even as an opt-in switch (SEC-02)",
                    )

    report.note(f"scanned {len(py_files)} runtime Python file(s) under the plugin root")
    return report.finish()


if __name__ == "__main__":
    main(check)
