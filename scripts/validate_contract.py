#!/usr/bin/env python3
"""Validate the required top-level fields of Codex adapter JSON artifacts."""

import argparse
import json
import sys
from pathlib import Path


REQUIRED = {
    "plan": {
        "plan_id",
        "issue_revision",
        "base_sha",
        "summary",
        "planned_files",
        "implementation_steps",
        "validation_commands",
        "assumptions",
        "risks",
        "requested_permissions",
        "stop_conditions",
    },
    "execution": {
        "run_id",
        "plan_id",
        "base_sha",
        "head_sha",
        "changed_files",
        "commands",
        "exit_codes",
        "tests",
        "scope_result",
        "assumptions",
        "remaining_risks",
        "status",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=sorted(REQUIRED))
    parser.add_argument("artifact")
    args = parser.parse_args()
    data = json.loads(Path(args.artifact).read_text(encoding="utf-8"))
    missing = sorted(REQUIRED[args.kind] - data.keys())
    unexpected = sorted(data.keys() - REQUIRED[args.kind])
    if missing or unexpected:
        print(json.dumps({"result": "FAIL", "missing": missing, "unexpected": unexpected}))
        return 1
    if args.kind == "execution" and data["status"] not in {"PASS", "PARTIAL", "BLOCKED", "FAIL"}:
        print(json.dumps({"result": "FAIL", "reason": "invalid status"}))
        return 1
    print(json.dumps({"result": "PASS", "kind": args.kind, "artifact": args.artifact}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
