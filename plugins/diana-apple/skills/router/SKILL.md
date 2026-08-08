---
name: router
description: "Manage Vodafone Smart Router (Huawei HG8247X6) via telnet WAP CLI. Use when: 'router', 'роутер', 'wan status', 'connected devices', 'wifi', 'port mapping', 'reboot router', 'dhcp', 'optical', 'firewall'."
---

# router — Huawei HG8247X6 Telnet Management

Manage the home router via telnet WAP CLI (superuser). LAN-only access (`TELNETWanEnable="0"`).

## Connection

**Single command — connect, escalate to SU, run command, exit:**
```bash
expect -c '
  set timeout 10
  log_user 1
  spawn telnet 192.168.1.1
  expect "Login:"
  send "root\r"
  expect "Password:"
  send "admin\r"
  expect "WAP>"
  send "su\r"
  expect "SU_WAP>"
  send "COMMAND_HERE\r"
  expect {
    -exact "---- More" { send " "; exp_continue }
    "SU_WAP>" {}
  }
  send "quit\r"
  expect eof
'
```

**Multiple commands in one session** — chain `send/expect` blocks:
```bash
expect -c '
  set timeout 10
  log_user 1
  spawn telnet 192.168.1.1
  expect "Login:"; send "root\r"
  expect "Password:"; send "admin\r"
  expect "WAP>"; send "su\r"
  expect "SU_WAP>"
  send "COMMAND_1\r"
  expect { -exact "---- More" { send " "; exp_continue } "SU_WAP>" {} }
  send "COMMAND_2\r"
  expect { -exact "---- More" { send " "; exp_continue } "SU_WAP>" {} }
  send "quit\r"
  expect eof
'
```

**Important:** Replace `COMMAND_HERE`, `COMMAND_1`, `COMMAND_2` with actual WAP CLI commands.

## Command Reference

### Monitoring (read-only)

| What | Command |
|------|---------|
| System info (uptime, firmware, model) | `display sysinfo` |
| Connected devices (IP, MAC, hostname) | `display connection all` |
| WAN status (external IP, gateway, DNS) | `display waninfo all` |
| WiFi networks (SSID, channel, clients) | `display wifi information` |
| WiFi settings (SSID, password, encryption) | `display wifi basicset` |
| Optical fiber (TX/RX power, temp) | `display optic` |
| DHCP leases | `display dhcp server user all` |
| LAN configuration | `display lan info` |
| Port forwarding rules | `display nat port mapping` |
| DNS servers | `display dns server` |
| MAC address filter | `display wifi macfilter` |
| Firewall rules | `display firewall rule` |
| UPnP mappings | `display upnp` |
| ARP table | `display arp` |
| Routing table | `display route` |
| VLAN config | `display vlan` |
| All available commands | `?` |
| Subcommands for X | `X ?` (e.g. `display ?`) |

### Management (destructive — CONFIRM FIRST)

| What | Command | Safety |
|------|---------|--------|
| Reboot router | `reset` | **ASK before running** — disconnects all devices ~2min |
| Packet capture | `trafficdump` | Safe, read-only |
| Save config | `save` | Safe |

### Custom commands

Any WAP CLI command can be run verbatim. Use `?` to discover. Use `COMMAND ?` for help on a specific command.

## Pagination

Some commands produce long output with `---- More ( Press 'Q' to break ) ----`. The expect script handles this automatically by sending space to continue. If output is still truncated, increase `set timeout`.

## Session Limits

Router allows max 1 telnet session. If you get "The number of sessions exceeds the specifications", a stale session exists. Wait ~60 seconds for it to time out, or the router auto-cleans idle sessions.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Connection refused | Router rebooting or telnet disabled. Wait 2 min after reboot. |
| Login failed | Credentials: root / admin. If changed, check `~/src/huawei-router-mcp/hw_ctree.xml` |
| Session limit | Wait 60s for stale session timeout |
| Command not found | Run `?` to list all commands. Some need `su` first. |
| Truncated output | Increase `set timeout 30` in expect script |

## Related Files

- **Config backup**: `~/src/huawei-router-mcp/hw_ctree.xml` (modified), `hw_ctree_original.xml` (original)
- **Password tool**: `~/src/huawei-router-mcp/huawei_decrypt.py` — decrypt/encrypt Huawei `$2...$` passwords
- **Old MCP server**: `~/src/huawei-router-mcp/server.py` — HTTP-scraping approach (archived, not in use)
