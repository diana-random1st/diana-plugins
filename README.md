# diana-plugins

Content plugins for [Diana](https://github.com/diana-random1st/diana): skills,
agents, slash commands, hook manifests and MCP server declarations.

Everything here is **content, not code** — no Rust, no build step, nothing that
requires a Diana release to work. That is the point, and it is enforced: this
repository's CI runs against the last *released* `diana` binary, never a branch
build, so a change here that needs an unreleased capability fails instead of
quietly creating a pair of commits that must ship together.

## Install

Through Diana:

```bash
diana plugin marketplace add github:diana-random1st/diana-plugins
diana plugin add diana-dev
diana plugin sync
```

Or natively, since the layout is the Claude Code marketplace format:

```bash
claude plugin marketplace add diana-random1st/diana-plugins
```

Diana materializes skills as symlinks into `~/.agents/skills` and records what
is installed, and at which commit, in `~/.diana/plugins.lock`. It never
overwrites: a name already taken by a real directory, or by a symlink pointing
elsewhere, is reported as a collision and left alone.

## Plugins

| Plugin | Skills | What it is |
|---|---|---|
| `diana-dev` | 17 | Review, debug, deploy, framework guidance, browser and docs research |
| `diana-apple` | 6 | Signing, notarization, store submission, the macOS host itself |
| `diana-docs` | 5 | Document toolchain — pdf, docx, xlsx, notebooklm, gdrive |

Bootstrap plugins (`diana-core`, `diana-media`) are **not** here. They ship
inside the Diana pkg because a fresh machine may have no network, and a
bootstrap set that depends on one is not a bootstrap set.

## Contributing

`python3 scripts/validate-plugins.py` — the same command CI runs. It rejects:

- **symlinks and gitlinks** anywhere under `plugins/`, because s5d fingerprinting
  fails closed on both and does not attest submodule contents;
- `~/.claude/skills/` and `~/.diana/src/skills/` in skill content, because those
  resolve only while a particular repo happens to be the skills directory — after
  a move the failure surfaces as a Python `FileNotFoundError` rather than as
  "this skill moved". Use `~/.agents/skills/<name>/`;
- a skill name claimed by two plugins, because sync treats that as a collision
  and links neither, so the skill silently disappears;
- a manifest name that differs from its directory name, which makes provenance
  ambiguous.

A skill whose content names a client, an account or a machine belongs in
`diana-plugins-private`, whatever category it otherwise looks like.
