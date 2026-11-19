---
name: serena
description: "Operate Diana's Serena integration: symbolic-code navigation, per-project LSP diagnosis, gateway troubleshooting, and managed serena-agent upgrades. Triggers: /serena, /serena-doctor, /serena-howto, /serena-update, serena doctor, serena howto, serena upgrade, lsp health, где heatmap."
allowed-tools: Bash
---

# Serena

**State on 2026-11-18 (re-check, do not trust):** `serena` CLI 1.5.1 is installed (`~/.local/bin/serena`), but `diana gateway list` has no Serena upstream, `claude mcp list` has no `diana-gw-serena`, and `diana claude --help` has no `--serena` flag. Symbol tools are therefore unavailable in sessions; re-adding the upstream is an external change that needs Roman's approval. The official Claude plugin source sits at `~/.claude/plugins/marketplaces/claude-plugins-official/external_plugins/serena` (not enabled).

Choose one mode; do not load or execute the other procedures unless needed:

| Intent | Read |
| --- | --- |
| Learn the integration or launch symbolic workflow | `references/usage.md` |
| Diagnose empty/erroring symbol tools or missing LSPs | `references/doctor.md` |
| Upgrade `serena-agent` with compatibility and rollback checks | `references/update.md` |

1. Separate Serena MCP connectivity from language-server health; one can pass while the other fails.
2. Re-detect project languages and binaries in the current workspace; do not reuse cached health claims.
3. Never install an LSP or upgrade Serena unless the request explicitly authorizes that external change.
4. Before an upgrade, record version and CLI help; after it, diff the CLI and verify the gateway before updating the pin.
5. Never cache Serena line/column coordinates across edits, wrap Serena write operations, build a parallel VFS, or introduce an LSP-dedup daemon without a new architecture decision.
6. Report observed versions, connectivity, missing dependencies, and any degraded behavior explicitly.
