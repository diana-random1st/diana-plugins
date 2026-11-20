---
name: router
description: "Manage Vodafone Smart Router (Huawei HG8247X6) via telnet WAP CLI. Use when: 'router', 'роутер', 'wan status', 'connected devices', 'wifi', 'port mapping', 'reboot router', 'dhcp', 'optical', 'firewall'."
---

# router — Huawei HG8247X6 Telnet Management

Home router, WAP CLI over telnet at 192.168.1.1 (LAN only, `TELNETWanEnable="0"`).
Every call goes through one script; do not hand-write expect or telnet sessions.

```bash
R=~/.agents/skills/router/scripts/router.py
$R devices                                   # DHCP clients: IP, MAC, SSID/LAN port, host
$R devices --json
$R run "display sysinfo"                     # any WAP CLI command, verbatim
$R run "display waninfo all" "display optic" # several commands, one session
$R run "display ?"                           # help: list subcommands
```

The script logs in, runs `su`, answers `---- More` pages, and quits. Credentials:
vault `ROUTER_TELNET_USER` / `ROUTER_TELNET_PASSWORD`, read by the script. Never put
them in a command, and never extract them from anywhere to get past the secguard hook.

Exit codes: 0 ok · 2 unreachable or timed out (`--timeout 20` for long output) ·
3 login/su failed · 4 another telnet session is open (one allowed; `--wait-session`
retries once after 60 s) · 5 the router rejected a command (`ERROR::...`).

## Command reference (checked on this firmware 2026-11-19)

| What | Command |
|------|---------|
| System info (CPU, memory, time) | `display sysinfo` (`display version`, `display deviceInfo` for firmware/model) |
| Connected devices | `$R devices` (= `display dhcp server user all`); `display user device` adds IPv6 and SSID. NOT `display connection all`: that is the NAT conntrack table |
| WAN status | `display waninfo all` (`display waninfo all detail` for IPs, gateway, DNS) |
| WiFi networks | `display wifi information`; associated clients `display wlan stainfo` |
| WiFi settings of one SSID | `display wlan config wlaninst N` (N = 1-8). Prints the WiFi key: send to /dev/null or filter, do not show it |
| Optical fiber (TX/RX power, temp) | `display optic` |
| LAN DHCP | `display dhcp server pool all`, `display dhcp server static` |
| Port forwarding | `display upnp mapping`; static rules `display nat port mapping internal-ip <LAN IP>` (syntax from `?`, output not checked) |
| DNS | `display dnsserver static domain` (static entries only) |
| MAC filter | `display lan mac filter`, `display wifi filter` |
| Firewall | `display firewall level`, `display firewall rule` |
| ARP / neighbours | `display ip neigh` |
| Routing table | `display ip route` |

Not on this firmware: `display wifi basicset`, `display lan info`, `display dns server`,
`display wifi macfilter`, `display upnp`, `display arp`, `display route`, `display vlan`.
Discover others with `$R run "X ?"`.

## Management — ASK ROMAN FIRST

| What | Command | Effect |
|------|---------|--------|
| Reboot | `$R run reset --allow-reboot` | every device offline ~2 min; the script refuses `reset`/`reboot`/`restore` without the flag |
| Save config | `$R run save` | |
| Packet capture | `trafficdump` | read-only |

## Troubleshooting

| Exit / symptom | Fix |
|----------------|-----|
| 2, connection refused | router rebooting or telnet disabled; wait 2 min after a reboot |
| 3 | credentials changed: compare with `~/src/archive/huawei-router-mcp/hw_ctree.xml` |
| 4 | a stale session; wait ~60 s or `--wait-session` |
| 5 | wrong command or missing parameter; `$R run "<command> ?"` shows the syntax |

## Related files

- Config backup: `~/src/archive/huawei-router-mcp/hw_ctree.xml` (modified), `hw_ctree_original.xml` (original)
- Huawei `$2...$` password decrypt/encrypt: `~/src/archive/huawei-router-mcp/huawei_decrypt.py`
- Old HTTP-scraping MCP server (archived, unused): `~/src/archive/huawei-router-mcp/server.py`
