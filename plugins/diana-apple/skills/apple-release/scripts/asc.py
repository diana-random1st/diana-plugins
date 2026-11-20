#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyjwt[crypto]", "requests"]
# ///
"""Read-only App Store Connect API CLI over the two existing per-team clients.

Wraps, does not replace:
  pregmate  ~/.cache/asc/asc.py              call(method, path) -> (status, json);
            vault appstore-key-id-pregmate, appstore-issuer-id-pregmate, appstore-p8-pregmate
  hapt      ~/.appstoreconnect/asc_helper.py api(method, path) -> json, raises on >= 400;
            vault appstore-issuer-id + the KID and .p8 file hard-coded in that helper
Both read their credentials inside the process when imported; nothing is printed or logged.

Usage:
  asc.py --team pregmate|hapt get PATH [--fields a,b]
  asc.py --team T builds [--app ID] [--version X.Y.Z] [--limit N]
  asc.py --team T beta-groups [--app ID]
  asc.py --team T profiles [--name SUBSTRING]

--app is required (the hapt helper's APP_ID is Vacuum's). Personal-team apps: Hapt Touch
6759039802, Vacuum 6775836339, PageRelay 6791978091, TailMap 6752828909; otherwise pass it
(find it with `get /v1/apps --fields bundleId,name`).

Examples:
  S=~/.diana/plugins/marketplaces/diana-plugins/plugins/diana-apple/skills/apple-release/scripts/asc.py
  $S --team pregmate get /v1/apps --fields bundleId,name
  $S --team pregmate builds --app 1234567890 --version 1.14.1
  $S --team hapt beta-groups
  $S --team pregmate profiles --name Watch

Output: JSON. `get` without --fields prints the raw response; with --fields, a list of
{id, <fields>} from `data`. builds -> version, build, processingState, uploadedDate.

Exit codes:
  0  HTTP 2xx
  1  HTTP >= 400 (status, code and `detail` only on stderr), or network failure
  2  usage error, missing credential or client, missing Python dependency
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

BASE = "https://api.appstoreconnect.apple.com"
CLIENTS = {
    "pregmate": Path.home() / ".cache/asc/asc.py",
    "hapt": Path.home() / ".appstoreconnect/asc_helper.py",
}


class HttpError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(f"HTTP {status}: {detail}")
        self.status = status


class SetupError(Exception):
    pass


class VaultClient:
    """Same interface as the hapt helper (api() raises RuntimeError("NNN body") on >= 400),
    signed with ES256 from vault entries read in-process; nothing is printed."""

    def __init__(self, kid_name: str, iss_name: str, p8_name: str):
        def vault(name: str) -> str:
            try:
                return subprocess.run(["diana", "system", "vault", "get", name], capture_output=True,
                                      text=True, check=True, timeout=30).stdout.strip()
            except subprocess.CalledProcessError:
                raise SetupError(f"vault entry {name!r} is missing; create it with "
                                 f"`diana system vault set {name}`") from None
        self._kid, self._iss, self._p8 = vault(kid_name), vault(iss_name), vault(p8_name)

    def api(self, method: str, path: str) -> dict:
        import time

        import jwt
        import requests

        now = int(time.time())
        token = jwt.encode({"iss": self._iss, "iat": now, "exp": now + 900, "aud": "appstoreconnect-v1"},
                           self._p8, algorithm="ES256", headers={"kid": self._kid, "typ": "JWT"})
        r = requests.request(method, BASE + path, headers={"Authorization": f"Bearer {token}"}, timeout=60)
        if r.status_code >= 400:
            raise RuntimeError(f"{r.status_code} {r.text}")
        return r.json()


def load_client(team: str):
    path = CLIENTS[team]
    if not path.is_file():
        raise SetupError(f"{team} client {path} not found; apple-release SKILL.md step 2 names it")
    spec = importlib.util.spec_from_file_location(f"asc_client_{team}", path)
    if spec is None or spec.loader is None:
        raise SetupError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except subprocess.CalledProcessError as exc:
        name = exc.cmd[-1] if isinstance(exc.cmd, list) else "?"
        raise SetupError(f"vault entry {name!r} is missing or unreadable for team {team}; "
                         f"create it with `diana system vault set {name}`") from None
    except FileNotFoundError as exc:
        if team == "hapt":
            # The helper's hard-coded .p8 is gone from disk (seen 2026-11-19). Hapt was reached
            # before with the shared vault entries appstore-key-id/-issuer-id/-p8 (Runway setup).
            return VaultClient("appstore-key-id", "appstore-issuer-id", "appstore-p8")
        raise SetupError(f"{team} client {path.name} needs {exc.filename}, which is missing") from None
    except ImportError as exc:
        raise SetupError(f"{exc}; run this script directly or with `uv run --script` so the "
                         "inline dependencies are installed") from None
    return mod


def error_detail(payload: object) -> str:
    if isinstance(payload, dict):
        errs = payload.get("errors") or []
        if errs and isinstance(errs[0], dict):
            e = errs[0]
            return f"{e.get('code', '')} {e.get('detail') or e.get('title') or ''}".strip()
    return "no error detail"


def requester(team: str, mod):
    def get(path: str) -> dict:
        path = path.removeprefix(BASE)
        if not path.startswith("/"):
            path = "/" + path
        if team == "pregmate":
            status, body = mod.call("GET", path)
            if status >= 400:
                raise HttpError(status, error_detail(body))
            return body
        try:
            return mod.api("GET", path)
        except RuntimeError as exc:
            m = re.match(r"(\d{3}) (.*)", str(exc), re.DOTALL)
            if not m:
                raise
            text = m.group(2)
            try:
                detail = error_detail(json.loads(text))
            except ValueError:
                d = re.search(r'"detail"\s*:\s*"([^"]*)"', text)
                detail = d.group(1) if d else "no error detail"
            raise HttpError(int(m.group(1)), detail) from None

    return get


def project(body: dict, fields: list[str]) -> list[dict]:
    rows = []
    data = body.get("data") or []
    for item in [data] if isinstance(data, dict) else data:
        attrs = item.get("attributes") or {}
        rows.append({"id": item.get("id"), **{f: attrs.get(f) for f in fields}})
    return rows


def need_app(args, mod) -> str:
    # No default from the helper: its APP_ID 6775836339 is Vacuum, not Hapt (checked 2026-11-19).
    app = args.app
    if not app:
        raise SetupError("pass --app ID (find it with `get /v1/apps --fields bundleId,name`)")
    return str(app)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--team", required=True, choices=sorted(CLIENTS))
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("get", help="GET any API path")
    g.add_argument("path")
    g.add_argument("--fields", help="comma-separated attributes to keep from data[]")
    b = sub.add_parser("builds", help="newest builds of an app")
    b.add_argument("--app")
    b.add_argument("--version", help="marketing version X.Y.Z")
    b.add_argument("--limit", type=int, default=20)
    bg = sub.add_parser("beta-groups", help="TestFlight groups of an app")
    bg.add_argument("--app")
    p = sub.add_parser("profiles", help="provisioning profiles")
    p.add_argument("--name", default="", help="case-insensitive name substring")
    args = ap.parse_args()

    try:
        mod = load_client(args.team)
        get = requester(args.team, mod)
        if args.cmd == "get":
            body = get(args.path)
            out = project(body, args.fields.split(",")) if args.fields else body
        elif args.cmd == "builds":
            q = (f"/v1/builds?filter[app]={need_app(args, mod)}&sort=-uploadedDate&limit={args.limit}"
                 "&include=preReleaseVersion&fields[builds]=version,processingState,uploadedDate,preReleaseVersion"
                 "&fields[preReleaseVersions]=version")
            if args.version:
                q += f"&filter[preReleaseVersion.version]={args.version}"
            body = get(q)
            versions = {i["id"]: (i.get("attributes") or {}).get("version")
                        for i in body.get("included") or [] if i.get("type") == "preReleaseVersions"}
            out = []
            for item in body.get("data") or []:
                attrs = item.get("attributes") or {}
                rel = ((item.get("relationships") or {}).get("preReleaseVersion") or {}).get("data") or {}
                out.append({"id": item.get("id"), "version": versions.get(rel.get("id")),
                            "build": attrs.get("version"), "processingState": attrs.get("processingState"),
                            "uploadedDate": attrs.get("uploadedDate")})
        elif args.cmd == "beta-groups":
            body = get(f"/v1/apps/{need_app(args, mod)}/betaGroups?limit=200"
                       "&fields[betaGroups]=name,isInternalGroup,publicLinkEnabled")
            out = project(body, ["name", "isInternalGroup", "publicLinkEnabled"])
        else:
            body = get("/v1/profiles?limit=200&fields[profiles]=name,profileType,profileState,expirationDate")
            rows = project(body, ["name", "profileType", "profileState", "expirationDate"])
            out = [r for r in rows if args.name.lower() in (r["name"] or "").lower()]
    except HttpError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except SetupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: network failure talking to {BASE}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
