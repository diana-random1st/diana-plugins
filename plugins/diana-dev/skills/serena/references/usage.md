# Diana and Serena usage

## Components

| Component | Verify |
| --- | --- |
| `serena-agent` CLI installed by uv | `command -v serena && serena --version` |
| Diana Gateway Serena upstream | `diana gateway list | grep serena` |
| Claude MCP entry | `claude mcp list | grep diana-gw-serena` |
| Opt-in launch flag | `diana claude --help | grep serena` |

Paths vary by installation. Read live command output and current configuration;
do not assume a remembered binary or home-directory path.

## Daily launch

```bash
diana claude --serena
diana claude --serena -- --resume <session-id>
diana claude
```

`--serena` applies the Serena-oriented system-prompt override. Without it, the
MCP tools may still be available, but adherence to symbolic navigation is lower.

Prefer semantic tools for symbol discovery, references, and targeted reads.
After edits, rediscover affected symbols rather than reusing line/column
coordinates returned before the edit.

## Connectivity troubleshooting

```bash
diana gateway status
diana gateway list | grep serena
diana gateway reload
claude mcp list 2>&1 | grep diana-gw-serena
```

If the gateway connects but symbol tools fail, run doctor mode from the project
root; per-language LSP health is independent of MCP registration.

If a recent upgrade broke startup flags, use the managed update/rollback
procedure rather than repeatedly editing gateway configuration.

## Historical heatmap boundary

Older Diana integration notes described an `edit-heatmap` hook and
`~/.diana/state/file-edit-heatmap.jsonl`. The current `diana dev hook --help`
does not expose that command. Treat the heatmap as unavailable until runtime
help/source and a live event verify a replacement; do not invoke the stale hook
or promise that the log is being populated.

## Architecture constraints

- Never cache `(line, column)` coordinates from Serena responses across edits.
- Never wrap Serena write operations such as symbol replacement or rename; let
  Serena own their protocol and document synchronization.
- Never build a second VFS/document-sync layer in Diana.
- Never introduce a long-lived LSP-dedup daemon without new evidence and a new
  architecture decision.
- Keep product capability separate from process model; Serena integration does
  not justify an unrelated always-on Diana service.

The governing decision is
`.s5d/packages/decision.serena-integration-vs-rewrite__20260519.s5d.yaml`.
