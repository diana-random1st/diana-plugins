---
name: maintaining-macos-health
version: 1.2.0
description: Use for macOS disk-pressure recovery, cleanup planning, alerting, sustained-CPU incidents, or Mole-based safe uninstall workflows on developer machines.
---

# Maintaining macOS Health

Pick the route first:
- incident triage or "free space now": [references/triage.md](./references/triage.md) and [references/cleanup-tiers.md](./references/cleanup-tiers.md)
- non-deletable boundaries: [references/never-touch.md](./references/never-touch.md)
- Mole safety model: [references/mole-techniques.md](./references/mole-techniques.md)
- alerting, restore, or troubleshooting: [references/alerting.md](./references/alerting.md)
- a process burning CPU for hours: [references/alerting.md](./references/alerting.md) — CPU incident lifecycle, `assets/mac-health-action` dispatcher, `CPU_*` thresholds in `assets/config.sh`

Non-negotiable rules:
1. Scan first, delete later; for incident cleanup, build the candidate list before applying anything.
2. No hand-written apply-phase `rm`; use the sanctioned helper under `assets/apply-cleanup-selection.py`.
3. `mo purge` and `mo clean` always start with `--dry-run`.
4. Respect `never-touch.md`, Time Machine via `tmutil`, and the no-swap-deletion rule.
5. Any tier-5+ or sudo cleanup needs explicit user confirmation before execution.
6. Alerting is notification-only; do not turn alerts into automatic cleanup. CPU actions are read-only investigations; "Stop Process…" always re-confirms, revalidates the PID, and sends SIGTERM before SIGKILL.
7. If an item is unfamiliar or risky, resolve what it is before presenting it as a deletion candidate.
