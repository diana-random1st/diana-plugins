# Managed Serena update

## Contents

- [Authorization and baseline](#authorization-and-baseline)
- [Resolve the target](#resolve-the-target)
- [Upgrade](#upgrade)
- [Compatibility and gateway checks](#compatibility-and-gateway-checks)
- [Pin or rollback](#pin-or-rollback)

Use only after an explicit request to upgrade Serena. Do not upgrade all uv tools
or opt into a prerelease unless the request explicitly says so.

## Authorization and baseline

Resolve the actual binary and create local state files:

```bash
SERENA_BIN="$(command -v serena)"
STATE_DIR="$HOME/.diana/state"
mkdir -p "$STATE_DIR"

"$SERENA_BIN" --version | tee "$STATE_DIR/serena-version-before.txt"
"$SERENA_BIN" start-mcp-server --help 2>&1 \
  | head -80 > "$STATE_DIR/serena-cli-before.txt"
```

If no pin exists, initialize it from the verified current version before making
the change. Preserve the exact version string and confirm how the package encodes
it before using it for rollback.

## Resolve the target

For latest stable, preview resolution without `--prerelease=allow`:

```bash
uv tool install -p 3.13 serena-agent@latest --dry-run
```

For an explicitly requested version:

```bash
uv tool install -p 3.13 serena-agent@<VERSION> --dry-run
```

Show the current-to-target delta and stop if resolution is ambiguous. Add the
prerelease option only after explicit opt-in.

## Upgrade

For current stable within the existing managed tool:

```bash
uv tool upgrade serena-agent
"$SERENA_BIN" --version
```

If the user selected an exact version, install exactly that resolved version with
the canonical uv tool command rather than upgrading to an unspecified latest.

## Compatibility and gateway checks

```bash
"$SERENA_BIN" start-mcp-server --help 2>&1 \
  | head -80 > "$STATE_DIR/serena-cli-after.txt"
diff -u "$STATE_DIR/serena-cli-before.txt" \
  "$STATE_DIR/serena-cli-after.txt" || true
```

Inspect changes to:

- the `start-mcp-server` subcommand;
- required Diana flags such as context and project-from-CWD behavior;
- default transport/port/project behavior;
- renamed or newly required arguments.

Then verify the existing integration:

```bash
diana gateway reload
diana gateway status
claude mcp list 2>&1 | grep diana-gw-serena
```

Do not rewrite `~/.diana/mcp.json` merely to make a failing upgrade appear green.
Report the incompatibility and offer rollback or a separately reviewed config fix.

## Pin or rollback

Only after `diana-gw-serena` is visibly Connected:

```bash
"$SERENA_BIN" --version | head -1 \
  > "$STATE_DIR/serena-pinned-version"
```

If compatibility or connectivity fails, read the previous verified version from
the saved pin, show the breaking CLI diff, and obtain/confirm the intended
rollback. Then reinstall that exact version, reload the gateway, and verify it
again. Do not call rollback successful until the old version and Connected state
are both observed.

Report:

```text
Serena: <before> -> <after or rolled-back version>
CLI compatibility: PASS | FAIL <details>
Gateway: PASS Connected | FAIL <state>
Pin: unchanged | updated to <version>
Rollback: not needed | completed | failed
```
