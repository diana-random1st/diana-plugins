# Triage — first 5 minutes

When the user reports trouble, or an alert fires, identify which signal class fired before doing anything destructive. The right response differs.

## Table of contents

- [Quick state snapshot](#quick-state-snapshot-always-run-first)
- [Signal classification](#signal-classification)
  - [A. Disk-driven](#a-disk-driven-most-common)
  - [B. Memory-driven](#b-memory-driven)
  - [C. Kernel-panic / watchdog-timeout](#c-kernel-panic--watchdog-timeout-rare-but-severe)
  - [D. JetsamEvent with vm-compressor-space-shortage](#d-jetsamevent-with-vm-compressor-space-shortage)
  - [E. "Mac just feels slow"](#e-mac-just-feels-slow)
- [Decision tree](#decision-tree)
- [What to NOT do at triage](#what-to-not-do-at-triage)

## Quick state snapshot (always run first)

```bash
echo "=== Disk ==="
df -h /System/Volumes/Data
diskutil info /System/Volumes/Data | grep -E "Free|Used|Capacity|Container Free"

echo "=== Memory ==="
memory_pressure | head -20
sysctl vm.swapusage hw.memsize hw.model
vm_stat

echo "=== Recent panics & jetsam ==="
ls -lt /Library/Logs/DiagnosticReports/ 2>/dev/null | head -10
ls -lt /Library/Logs/DiagnosticReports/Retired/ 2>/dev/null | head -5

echo "=== Top RSS processes ==="
ps -axo pid,rss,vsz,pcpu,pmem,command | sort -k2 -n -r | head -15

echo "=== Health-check log if installed ==="
test -f ~/Library/Logs/mac-health/health.log && tail -20 ~/Library/Logs/mac-health/health.log

echo "=== Uptime, load ==="
uptime

echo "=== Recent CPU monitor evidence ==="
test -f ~/Library/Logs/mac-health/health.log && grep ' cpu ' ~/Library/Logs/mac-health/health.log | tail -10
ls -lt ~/Library/Logs/mac-health/cpu-incidents/ 2>/dev/null | head -5
```

## Signal classification

### A. Disk-driven (most common)

Symptoms: `df` shows < 20 % free, user complains "out of space".

- **`pct_free < 10 %`** → CRITICAL. Run Tier 1–4 from `cleanup-tiers.md` immediately. swap extension may already be blocked.
- **`pct_free 10–20 %`** → HIGH. Run Tier 1–3, propose Tier 4. Probably manageable.
- **`pct_free > 20 %`** → user perception issue. Check `du -d1 -h ~ | sort -h | tail -15` and address specifically.

The canonical incident hit ~8 % free, well below the 10 % critical threshold. APFS purgeable can lag — `diskutil info` "Container Free" is the real number.

#### Mole first, manual tiers second

Start every disk-driven cleanup with `mo clean --dry-run` and `mo purge --dry-run` (`~` as cwd). Mole covers the cache/log tiers with its own guards — on 2026-10-01 it found 16.6 GB the manual tiers missed, while hand-built commands broke (`bun pm cache rm` fails outside a project). Hand-built items are only for what Mole does not touch: app-private models (e.g. `~/Library/Application Support/Feynt/models`), `.terraform` provider caches, renamed `target-*` dirs, untracked data dumps.

#### Measuring where the space went — three traps (incident 2026-10-01)

1. **Always `du -x`.** `~/Library/Developer/CoreDevice/DeviceFS` is an fskit `devicefs` mount of connected iPhones; plain `du` reported 272 GB of *phone* storage as local and sent the audit down a false lead. Before naming any directory as a hog, check `mount | grep -v '^/dev/disk3'` for mounts inside it.
2. **`du -sh *` silently drops entries.** Under TCC, entries fail with no output line, so per-entry sums came out far below the parent total (`~/src` 185 GB → listing showed ~85). Measure with a per-entry loop that prints every name, and report `Operation not permitted` dirs (`MobileSync` = iPhone backups, `CloudDocs`, `FileProvider`, `Knowledge`) as **unmeasured**, never as small.
3. **One parallel pass, not a dozen serial ones.** Run a single background scan of all roots (`~/src`, `~/Library/Application Support`, `~/Library/Developer`, `~/.cache`, model dirs, Docker `system df`), then present the full list once. Serial probing made a simple cleanup take an hour.

```bash
for r in ~/src ~/"Library/Application Support" ~/Library/Developer ~/.cache ~/Library/Caches; do
  ( for d in "$r"/* "$r"/.[!.]*; do [ -e "$d" ] || continue
      kb=$(du -skx "$d" 2>/dev/null | cut -f1); echo "${kb:-UNMEASURED}	$d"; done ) &
done; wait
```

Before applying, check what is running (`pgrep -lf "xcodebuild|GradleDaemon|codex|docker"`) and exclude caches in use — e.g. the DerivedData of an active `xcodebuild`.

### B. Memory-driven

Symptoms: Mac slow, beachballs, swap > 6 GB, fans running.

- Check `memory_pressure` output for system-wide memory free percentage.
  - **Critical (< 10 %)** + **swap > 8 GB**: imminent thrashing. Close heavy apps. Stop new work.
  - **Warning (10–25 %)**: heavy load but stable. Monitor.
  - **Normal (> 25 %)**: false alarm.
- A 16–18 GB Mac under heavy AI/Docker is expected to swap 2–4 GB. Don't panic on swap alone; pair with pressure level.
- VM-driven: if `com.apple.Virtualization.VirtualMachine` shows in top RSS (Docker Desktop), check Docker memory limit:
  ```bash
  jq '.MemoryMiB' ~/Library/Group\ Containers/group.com.docker/settings-store.json
  ```
  Rule of thumb: Docker memory ≤ 1/3 of host RAM. On 16–18 GB hosts, > 6 GB allocation is dangerous; 4–5 GB is the safe ceiling.

### C. Kernel-panic / watchdog-timeout (rare but severe)

Symptoms: Mac rebooted unexpectedly. Panic dialog after wake.

```bash
ls -lt /Library/Logs/DiagnosticReports/Retired/*.panic 2>/dev/null
cat /Library/Logs/DiagnosticReports/.contents.panic 2>/dev/null | jq -r '.panic_string' | head -50
```

Look for in `panicString`:
- `watchdog timeout: no checkins from watchdogd in N seconds` → Mac was non-responsive for N seconds. Almost always caused by:
  - **`Compressor Info: ... 100% of segments limit (BAD)`** + **`LOW swap space`** + many swapfiles → memory thrashing (the canonical incident).
  - I/O stall on boot SSD (rare on Apple Silicon healthy NAND).
  - Spinlock deadlock — all cores at the same PC; needs KDK + LLDB to symbolicate.
- The full panic JSON has `processByPid` with each process's `residentMemoryBytes` and `pageFaults` — find the top RSS process. In the canonical incident: `com.apple.Virtualization.VirtualMachine` 9.4 GB RSS, 512 M pageFaults.
- Cross-check Disk free at the time: was it already low? (panic file's `memoryStatus.compressorSize` × 16 KB = compressed pages on hand)

After a panic of this class:
1. Confirm it was a one-off (check Retired/ for prior panics).
2. Run cleanup Tier 1–7 to give breathing room.
3. Install/verify the alerter (`alerting.md`).
4. Discuss reducing Docker memory if a VM was the proximate cause.

### D. JetsamEvent with `vm-compressor-space-shortage`

This is the alerter's loudest signal — it's a leading indicator of (C). Find the file:

```bash
grep -l "vm-compressor-space-shortage" /Library/Logs/DiagnosticReports/JetsamEvent-*.ips 2>/dev/null
```

If exists and recent (last 30 min): system already started killing processes for memory. **Treat as imminent panic risk**:
1. Save user work.
2. Quit Docker Desktop, browser tabs, AI tools.
3. Don't run `mo clean` or anything heavy — that itself thrashes memory.
4. Wait 5 min for system to settle, then proceed with cleanup if still in trouble.

### E. "Mac just feels slow"

Probably memory pressure or thermal throttling. Check:
```bash
sudo powermetrics --samplers cpu_power,thermal -i 1000 -n 5
```
- If thermal pressure shows `Heavy`: close apps, let it cool, check fans.
- Else fall back to memory-driven flow (B).

If the CPU monitor recorded an incident, inspect its snapshot before sampling again. It contains system busy/load plus safe top-process fields (PID, PPID, elapsed time, executable) without command arguments. A per-process advisory is evidence, not permission to kill it: first determine whether the workload is an intentional build, test, indexer, VM, or a stale background tool.

## Decision tree

```
ALERT or USER REPORT
       │
       ▼
   df -h <20%? ──yes──▶ A. Disk-driven (cleanup-tiers.md)
       │
       no
       ▼
   panic in
   last hour? ──yes──▶ C. Read panic, identify top RSS, propose cleanup + alerter
       │
       no
       ▼
   JetsamEvent
   vm-compressor? ──yes──▶ D. Triage immediate, then cleanup
       │
       no
       ▼
   memory_pressure
   not Normal? ──yes──▶ B. Memory-driven, check Docker, top RSS
       │
       no
       ▼
   thermal? ──yes──▶ E. Power/thermal advice
       │
       no
       ▼
   user perception → du audit, propose targeted cleanup
```

## What to NOT do at triage

- Don't run `mo clean` or `mo purge` reflexively. Identify what's hurting first.
- Don't `kill -9` the top RSS process — saving work first matters; a hard kill on Docker can corrupt volumes.
- Don't `sudo rm -rf /private/var/vm/swapfile*` — guaranteed kernel panic.
- Don't blindly empty Trash if the user might still want recently deleted items.
