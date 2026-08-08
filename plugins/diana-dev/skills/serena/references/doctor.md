# Serena doctor

Use this read-only procedure when symbol tools return errors/empty results, after
switching projects, or before work that depends heavily on semantic navigation.
It diagnoses; it never installs or edits configuration.

## 1. Detect project languages

Run from the project root. Prefer tracked root markers, then a bounded search:

```bash
git ls-files | grep -E \
  '^(Cargo\.toml|package\.json|tsconfig\.json|pyproject\.toml|setup\.py|requirements\.txt|build\.gradle|settings\.gradle|.+\.xcodeproj|.+\.xcworkspace|Package\.swift)' \
  | head -30
```

If the directory is not a Git repository or the result is incomplete:

```bash
find . -maxdepth 3 \
  \( -name Cargo.toml -o -name package.json -o -name tsconfig.json \
     -o -name pyproject.toml -o -name setup.py -o -name requirements.txt \
     -o -name 'build.gradle*' -o -name settings.gradle.kts \
     -o -name '*.xcodeproj' -o -name '*.xcworkspace' -o -name Package.swift \) \
  2>/dev/null | head -30
```

| Marker | Language | LSP binary |
| --- | --- | --- |
| `Cargo.toml` | Rust | `rust-analyzer` |
| TypeScript dependency or `tsconfig.json` | TypeScript/JavaScript | `typescript-language-server` |
| `pyproject.toml`, `setup.py`, `requirements.txt` | Python | `pyright-langserver` or `pyright` |
| Xcode project/workspace or `Package.swift` | Swift | `sourcekit-lsp` |
| Gradle Kotlin markers | Kotlin | `kotlin-language-server` |

If no recognized marker exists, report that result and stop. Do not guess.

## 2. Verify each detected LSP

```bash
command -v rust-analyzer && rust-analyzer --version
command -v typescript-language-server && typescript-language-server --version
command -v pyright-langserver && pyright-langserver --version
command -v pyright && pyright --version
xcrun --find sourcekit-lsp 2>/dev/null
command -v kotlin-language-server && kotlin-language-server --version
```

Run only checks for detected languages. A missing binary is not evidence that
Serena MCP itself is disconnected.

Offer, but do not run, an appropriate install command:

| LSP | Suggested command after explicit approval |
| --- | --- |
| Rust | `rustup component add rust-analyzer` |
| TypeScript | `bun add -g typescript typescript-language-server` |
| Python | `uv tool install pyright` |
| Swift | install/repair current Xcode toolchain; SourceKit-LSP ships with Xcode |
| Kotlin | `brew install kotlin-language-server` |

## 3. Verify Serena and gateway separately

```bash
command -v serena && serena --version
diana gateway status
diana gateway list | grep serena
claude mcp list 2>&1 | grep diana-gw-serena
```

Expected final MCP state is Connected. If the gateway is disconnected, report
that as the deeper integration issue and route to `usage.md` troubleshooting.
Do not modify `~/.diana/mcp.json` during doctor mode.

## 4. Report

```text
Project languages: rust, python
LSP:
  PASS rust-analyzer <version>
  FAIL pyright-langserver - not found
Serena CLI: PASS <version>
Gateway/MCP: FAIL diana-gw-serena disconnected
Suggested installs (not run): uv tool install pyright
```

Never report a global PASS when any detected language, Serena binary, or gateway
check is UNKNOWN/FAIL.
