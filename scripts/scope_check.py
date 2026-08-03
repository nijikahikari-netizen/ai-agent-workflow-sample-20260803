#!/usr/bin/env python3
"""Fail closed when a Git diff exceeds the human-approved change scope."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path, PurePosixPath
from typing import Any


@dataclass
class Change:
    status: str
    path: str
    old_path: str | None = None
    untracked: bool = False
    binary: bool = False
    symlink: bool = False


def normalize_path(raw_path: str) -> str:
    path = raw_path.replace("\\", "/")
    if not path or path.startswith("/") or re.match(r"^[A-Za-z]:", path):
        raise ValueError(f"absolute or empty path is not allowed: {raw_path!r}")
    parts = PurePosixPath(path).parts
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"non-canonical path is not allowed: {raw_path!r}")
    return "/".join(parts)


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def parse_name_status(raw: bytes) -> list[Change]:
    fields = raw.decode("utf-8", errors="surrogateescape").split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    changes: list[Change] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if status.startswith(("R", "C")):
            if index + 1 >= len(fields):
                raise ValueError("truncated rename/copy record in git diff output")
            old_path = normalize_path(fields[index])
            new_path = normalize_path(fields[index + 1])
            index += 2
            changes.append(Change(status=status, path=new_path, old_path=old_path))
        else:
            if index >= len(fields):
                raise ValueError("truncated path record in git diff output")
            path = normalize_path(fields[index])
            index += 1
            changes.append(Change(status=status, path=path))
    return changes


def _is_binary(repo: Path, base: str, change: Change) -> bool:
    if change.status.startswith("D"):
        return False
    if change.untracked:
        candidate = repo / change.path
        try:
            return b"\0" in candidate.read_bytes()[:8192]
        except OSError:
            return False
    raw = _git(repo, "diff", "--numstat", f"{base}...HEAD", "--", change.path)
    return any(line.startswith(b"-\t-\t") for line in raw.splitlines())


def _is_symlink(repo: Path, change: Change) -> bool:
    candidate = repo / change.path
    if candidate.is_symlink():
        return True
    if change.untracked:
        return False
    mode = _git(repo, "ls-files", "-s", "--", change.path).split(maxsplit=1)
    return bool(mode and mode[0] == b"120000")


def collect_changes(repo: Path, base: str) -> list[Change]:
    tracked = parse_name_status(
        _git(repo, "diff", "--name-status", "-z", "--find-renames", f"{base}...HEAD")
    )
    untracked_raw = _git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    untracked_paths = untracked_raw.decode("utf-8", errors="surrogateescape").split("\0")
    changes = tracked + [
        Change(status="?", path=normalize_path(path), untracked=True)
        for path in untracked_paths
        if path
    ]
    for change in changes:
        change.binary = _is_binary(repo, base, change)
        change.symlink = _is_symlink(repo, change)
    return changes


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def evaluate_changes(changes: list[Change], policy: dict[str, Any]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    planned = set(policy.get("planned_files", []))
    for change in changes:
        paths = [change.path] + ([change.old_path] if change.old_path else [])
        reasons: set[str] = set()
        if change.status.startswith("D") and not policy.get("allow_deletions", False):
            reasons.add("deletion_not_allowed")
        if change.status.startswith(("R", "C")):
            reasons.add("rename_or_copy_not_allowed")
        if change.untracked and not policy.get("allow_untracked", False):
            reasons.add("untracked_not_allowed")
        if change.binary and not policy.get("allow_binary", False):
            reasons.add("binary_not_allowed")
        if change.symlink and not policy.get("allow_symlinks", False):
            reasons.add("symlink_not_allowed")
        for path in paths:
            if _matches(path, policy.get("prohibited_paths", [])):
                reasons.add("prohibited_path")
            if _matches(path, policy.get("approval_required_paths", [])):
                reasons.add("additional_approval_required")
            if not _matches(path, policy.get("allowed_paths", [])):
                reasons.add("outside_allowed_paths")
            if path not in planned:
                reasons.add("not_in_approved_plan")
        for reason in sorted(reasons):
            violations.append({"path": change.path, "reason": reason})
    return violations


def run(repo: Path, base: str, policy_path: Path) -> dict[str, Any]:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    changes = collect_changes(repo, base)
    violations = evaluate_changes(changes, policy)
    return {
        "schema_version": "1.0",
        "base": base,
        "head": _git(repo, "rev-parse", "HEAD").decode().strip(),
        "result": "PASS" if not violations else "FAIL",
        "changes": [asdict(change) for change in changes],
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--policy", default=".ai/scope-policy.json")
    parser.add_argument("--output")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    try:
        result = run(repo, args.base, (repo / args.policy).resolve())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "schema_version": "1.0",
            "base": args.base,
            "result": "ERROR",
            "changes": [],
            "violations": [{"path": "<scope-check>", "reason": str(exc)}],
        }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
