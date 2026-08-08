#!/usr/bin/env python3
"""Deterministic prefix hash for LLM cache diagnostics.

Usage:
    python prefix_hash.py < request.json
    python prefix_hash.py request1.json request2.json  # diff between two

The hash captures (tools + system + first user message) canonicalized with
sort_keys=True. If hash changes between agent steps where it shouldn't —
that's where prefix cache breaks.
"""
import hashlib
import json
import sys
from pathlib import Path


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def prefix_hash(payload: dict) -> tuple[str, int]:
    tools = payload.get("tools") or payload.get("function_definitions") or []
    if isinstance(tools, list):
        tools = sorted(tools, key=lambda t: (t.get("name") or t.get("function", {}).get("name") or ""))

    system = payload.get("system") or ""
    messages = payload.get("messages") or payload.get("input") or []

    if isinstance(system, list):
        system = canonical(system)

    first_user = ""
    for m in messages:
        if isinstance(m, dict) and m.get("role") == "system" and not system:
            system = m.get("content", "")
            if isinstance(system, list):
                system = canonical(system)
            continue
        if isinstance(m, dict) and m.get("role") == "user":
            first_user = m.get("content", "")
            if isinstance(first_user, list):
                first_user = canonical(first_user)
            break

    blob = canonical({"tools": tools, "system": system, "first_user": first_user})
    return hashlib.sha256(blob.encode()).hexdigest()[:16], len(blob)


def load(src) -> dict:
    if src == "-":
        return json.load(sys.stdin)
    return json.loads(Path(src).read_text())


def main():
    args = sys.argv[1:] or ["-"]
    rows = []
    for a in args:
        try:
            h, size = prefix_hash(load(a))
            rows.append((a, h, size))
        except Exception as e:
            print(f"{a}: ERROR {e}", file=sys.stderr)
            continue

    width = max((len(r[0]) for r in rows), default=10)
    for name, h, size in rows:
        print(f"{name:<{width}}  hash={h}  prefix_bytes={size}")

    if len(rows) >= 2:
        unique = {r[1] for r in rows}
        if len(unique) == 1:
            print("\nstable: prefix hash matches across all inputs")
        else:
            print(f"\nUNSTABLE: {len(unique)} distinct prefix hashes — cache will miss")
            sys.exit(2)


if __name__ == "__main__":
    main()
