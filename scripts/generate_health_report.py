#!/usr/bin/env python3
"""Generate a small, auditable health snapshot for the CAI codebase.

The report deliberately uses only offline checks. CAI's AI endpoint expects a
locally hosted Ollama model and credentials for external services, neither of
which should be treated as available in CI.
"""

from __future__ import annotations

import ast
import compileall
import csv
import hashlib
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
REPORTS = ROOT / "reports"
HISTORY = REPORTS / "project-health-history.csv"
SUMMARY = REPORTS / "project-health.md"


def count_routes(path: Path) -> tuple[int, int]:
    """Return total Flask route decorators and API route decorators."""
    total = api = 0
    for source in path.rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                function = decorator.func
                if not isinstance(function, ast.Attribute) or function.attr != "route":
                    continue
                total += 1
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    route = str(decorator.args[0].value)
                    api += route.startswith("/api/")
    return total, api


def requirement_stats() -> tuple[int, int]:
    names = []
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            names.append(line.split("==", 1)[0].lower())
    duplicates = sum(count - 1 for count in Counter(names).values() if count > 1)
    return len(names), duplicates


def commit_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def source_fingerprint(files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    source_files = sorted(BACKEND.rglob("*.py"))
    compiled = compileall.compile_dir(BACKEND, quiet=1)
    routes, api_routes = count_routes(BACKEND)
    requirements, duplicate_requirements = requirement_stats()
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    row = {
        "timestamp_utc": timestamp,
        "commit": commit_sha(),
        "python_files": len(source_files),
        "flask_routes": routes,
        "api_routes": api_routes,
        "requirements": requirements,
        "duplicate_requirements": duplicate_requirements,
        "compileall": "pass" if compiled else "fail",
        "source_fingerprint": source_fingerprint(source_files),
    }

    fieldnames = list(row)
    write_header = not HISTORY.exists()
    with HISTORY.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    checks = [
        ("Python compilation", row["compileall"].upper()),
        ("Dependency duplicates", "PASS" if not duplicate_requirements else f"WARN ({duplicate_requirements})"),
    ]
    lines = [
        "# CAI Project Health",
        "",
        "This generated snapshot records offline CI checks. It does not call Ollama, Hugging Face, Firebase, or Microsoft OAuth.",
        "",
        f"Last run: `{timestamp}`  ",
        f"Source commit checked: `{row['commit']}`",
        "",
        "## Checks",
        "",
        "| Check | Result |",
        "| --- | --- |",
        *[f"| {name} | {result} |" for name, result in checks],
        "",
        "## Current project snapshot",
        "",
        f"- Python modules: {row['python_files']}",
        f"- Flask routes: {routes} ({api_routes} API routes)",
        f"- Pinned dependencies: {requirements}",
        f"- Source fingerprint: `{row['source_fingerprint']}`",
        "",
        "Historical records: [`project-health-history.csv`](project-health-history.csv).",
    ]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote health snapshot for {timestamp}")
    return 0 if compiled else 1


if __name__ == "__main__":
    sys.exit(main())
