#!/usr/bin/env python3
"""Run WAP CLI commands on the home router (Vodafone Smart Router, Huawei HG8247X6).

One telnet session per call: login, `su`, each command in turn, `quit`.
"---- More" pages are answered automatically.

Credentials come from $ROUTER_TELNET_USER / $ROUTER_TELNET_PASSWORD or from the
vault entries of the same names, read inside this process and handed to expect
through its environment. They never reach argv, stdout or logs.

Examples:
  router.py run "display sysinfo"
  router.py run "display waninfo all" "display dns server"
  router.py devices            # DHCP clients: IP, MAC, hostname
  router.py devices --json

Exit codes: 0 ok, 1 usage/credentials, 2 router unreachable or timed out,
3 login failed, 4 another telnet session holds the router (one allowed;
--wait-session retries once after 60 s), 5 the router rejected a command
(`ERROR::...`; output is still printed, other commands still run).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

HOST = "192.168.1.1"
VAULT_USER, VAULT_PASS = "ROUTER_TELNET_USER", "ROUTER_TELNET_PASSWORD"
DESTRUCTIVE = re.compile(r"^\s*(reset|reboot|restore)\b", re.IGNORECASE)
EXIT_UNREACHABLE, EXIT_LOGIN, EXIT_SESSION, EXIT_REJECTED = 2, 3, 4, 5
REJECTED = "ERROR::"  # e.g. ERROR::Command is not existed
MORE = "---- More ( Press 'Q' to break ) ----"

# Commands and credentials reach expect through its environment, never argv.
# Every `expect` below uses the unbraced multi-argument form. A one-line
# `expect { pat {} timeout {...} }` is read as ONE glob pattern (expect only
# treats a braced list as patterns when it spans lines), so it silently waits
# out the timeout and matches nothing; outputs then shift by one step.
EXPECT_SCRIPT = r"""
set timeout $env(RT_TIMEOUT)
match_max 1000000
log_user 0
spawn telnet $env(RT_HOST)
expect "Login:" {} "exceeds" { exit 4 } timeout { exit 2 } eof { exit 2 }
send "$env(RT_USER)\r"
expect -re {P.ssw.rd:} {} timeout { exit 2 } eof { exit 2 }
send -- "$env(RT_PASS)\r"
expect "WAP>" {} "exceeds" { exit 4 } "Login:" { exit 3 } timeout { exit 3 } eof { exit 3 }
send "su\r"
expect "SU_WAP>" {} timeout { exit 3 } eof { exit 3 }
set i 0
foreach cmd [split $env(RT_CMDS) "\n"] {
  send -- "$cmd\r"
  # `X ?` prints help as soon as `?` arrives and `?` is not echoed: sync on the text before it.
  set echo [string trim [lindex [split $cmd "?"] 0]]
  if {$echo ne ""} { expect -exact $echo {} timeout { exit 2 } eof { exit 2 } }
  set out ""
  expect \
    -exact "---- More" { append out $expect_out(buffer); send " "; exp_continue } \
    "SU_WAP>" { append out $expect_out(buffer) } \
    timeout { puts "<<<BEGIN $i>>>\n$out\n<<<TIMEOUT $i>>>"; exit 2 } \
    eof { puts "<<<BEGIN $i>>>\n$out\n<<<TIMEOUT $i>>>"; exit 2 }
  puts "<<<BEGIN $i>>>\n$out\n<<<END $i>>>"
  incr i
}
# `quit` from SU only returns to WAP>; the second one closes the session.
send "quit\r"
expect "WAP>" {} timeout {} eof { exit 0 }
send "quit\r"
expect eof {} timeout {}
exit 0
"""


def die(msg: str, code: int = 1) -> None:
    print(f"router: {msg}", file=sys.stderr)
    sys.exit(code)


def credential(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    try:
        out = subprocess.run(["diana", "system", "vault", "get", name],
                             capture_output=True, text=True, timeout=30, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        die(f"no {name}: set ${name} or store it with `diana system vault set {name}`")
    value = out.stdout.strip()
    if not value:
        die(f"vault returned an empty {name}")
    return value


def clean(raw: str, cmd: str) -> str:
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", raw).replace("\r", "").replace("\x07", "")
    text = re.sub(r"[ \t]*\x08+[ \t]*", "", text)
    text = text.replace(MORE, "").replace("---- More", "")
    lines = text.split("\n")
    if lines and cmd in lines[0]:  # telnet echo of the command
        lines = lines[1:]
    if lines and lines[-1].strip().endswith("SU_WAP>"):
        lines = lines[:-1]
    return "\n".join(ln.rstrip() for ln in lines).strip("\n")


def run_session(cmds: list[str], timeout: int) -> tuple[int, list[str]]:
    env = dict(os.environ, RT_HOST=HOST, RT_TIMEOUT=str(timeout), RT_CMDS="\n".join(cmds),
               RT_USER=credential(VAULT_USER), RT_PASS=credential(VAULT_PASS))
    proc = subprocess.run(["expect", "-c", EXPECT_SCRIPT], env=env, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, check=False,
                          timeout=timeout * (len(cmds) + 4) + 30)
    blocks = re.findall(r"<<<BEGIN (\d+)>>>\n(.*?)\n<<<(?:END|TIMEOUT) \1>>>",
                        proc.stdout, re.DOTALL)
    return proc.returncode, [clean(body, cmds[int(i)]) for i, body in blocks]


def execute(cmds: list[str], timeout: int, wait_session: bool) -> list[str]:
    code, outputs = run_session(cmds, timeout)
    if code == EXIT_SESSION and wait_session:
        print("router: telnet session busy, retrying in 60 s", file=sys.stderr)
        time.sleep(60)
        code, outputs = run_session(cmds, timeout)
    if code == EXIT_SESSION:
        die("the number of sessions exceeds the specifications: another telnet session "
            "is open; wait ~60 s or pass --wait-session", EXIT_SESSION)
    if code == EXIT_LOGIN:
        die(f"login or su failed on {HOST}: check vault {VAULT_USER}/{VAULT_PASS}", EXIT_LOGIN)
    if code != 0:
        for cmd, out in zip(cmds, outputs):
            print(f"### {cmd}\n{out}")
        die(f"{HOST} unreachable or timed out (raise --timeout for long output)",
            EXIT_UNREACHABLE)
    return outputs


def parse_devices(text: str) -> list[dict]:
    """Rows of `display dhcp server user all`.

    Columns: Index, User Port (SSIDn / LANn), IP, Host Name (cut to ~6 chars,
    may be empty), HW Addr, Expire-time.
    """
    row_re = re.compile(
        r"^\s*\d+\s+(?P<port>\S+)\s+(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+(?P<host>.*?)\s*"
        r"(?P<mac>[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})\s+(?P<expire>.*)$")
    rows = []
    for line in text.splitlines():
        m = row_re.match(line)
        if m:
            rows.append({"ip": m["ip"], "mac": m["mac"].lower(), "host": m["host"],
                         "port": m["port"], "expire": m["expire"].strip()})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeout", type=int, default=10, help="seconds per expect step")
    ap.add_argument("--wait-session", action="store_true",
                    help="if another session holds the router, retry once after 60 s")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run WAP CLI commands verbatim, in one session")
    r.add_argument("commands", nargs="+")
    r.add_argument("--allow-reboot", action="store_true",
                   help="required for reset/reboot/restore; ask Roman first")
    d = sub.add_parser("devices", help="DHCP clients (display dhcp server user all)")
    d.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.cmd == "run":
        risky = [c for c in args.commands if DESTRUCTIVE.match(c)]
        if risky and not args.allow_reboot:
            die(f"{risky[0]!r} disconnects every device for ~2 min: "
                "confirm with Roman, then pass --allow-reboot")
        outputs = execute(args.commands, args.timeout, args.wait_session)
        many = len(args.commands) > 1
        for cmd, out in zip(args.commands, outputs):
            print(f"### {cmd}\n{out}" if many else out)
        rejected = [c for c, o in zip(args.commands, outputs) if REJECTED in o]
        if rejected:
            die(f"router rejected: {', '.join(rejected)} (list commands with `X ?`)",
                EXIT_REJECTED)
    else:
        out = execute(["display dhcp server user all"], args.timeout, args.wait_session)[0]
        rows = parse_devices(out)
        if args.json:
            json.dump(rows, sys.stdout, indent=1)
            print()
        else:
            for row in rows:
                print(f"{row['ip']:<16} {row['mac']:<18} {row['port']:<6} {row['host']}")
            print(f"({len(rows)} devices)")


if __name__ == "__main__":
    main()
