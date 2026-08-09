#!/usr/bin/env python3
# @s5d:component comp.diana.plugin-boundary-gate
"""Validate the plugin marketplace.

Run it locally exactly as CI does:

    python3 scripts/validate-plugins.py

Every check here exists because something already went wrong or would fail
closed later. None of them are stylistic.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS = os.path.join(ROOT, "plugins")
MARKET = os.path.join(ROOT, ".claude-plugin", "marketplace.json")

# Addresses that resolve only while the repo happens to be the skills directory.
# A skill reaching its own script this way breaks the moment it moves, and the
# failure surfaces as FileNotFoundError from python rather than as "this moved".
# `~/.diana/src` on its own is fine — that is a reference to the Diana repo, not
# to the skill itself. So is `~/.claude/skills-registry.yaml`.
FORBIDDEN = [
    (re.compile(r"~/\.claude/skills/"), "use ~/.agents/skills/<name>/ instead"),
    (re.compile(r"~/\.diana/src/skills/"), "use ~/.agents/skills/<name>/ instead"),
]

failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def load_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001 — any failure is a validation failure
        fail(f"{os.path.relpath(path, ROOT)}: cannot parse ({e})")
        return None


def check_manifests() -> dict[str, dict]:
    """Every plugin dir has a manifest whose name matches the directory."""
    found: dict[str, dict] = {}
    for name in sorted(os.listdir(PLUGINS)):
        root = os.path.join(PLUGINS, name)
        if not os.path.isdir(root):
            continue
        manifest_path = os.path.join(root, ".claude-plugin", "plugin.json")
        if not os.path.isfile(manifest_path):
            fail(f"plugins/{name}: missing .claude-plugin/plugin.json")
            continue
        manifest = load_json(manifest_path)
        if manifest is None:
            continue
        if not manifest.get("name"):
            fail(f"plugins/{name}: manifest has no name")
        elif manifest["name"] != name:
            # Diana keys the lockfile by manifest name and materializes by
            # directory name; letting them differ makes provenance ambiguous.
            fail(f"plugins/{name}: manifest name is '{manifest['name']}'")
        found[name] = manifest
    return found


def check_marketplace(plugins: dict[str, dict]) -> None:
    market = load_json(MARKET)
    if market is None:
        return
    listed = {e.get("name"): e for e in market.get("plugins", [])}
    for name in plugins:
        if name not in listed:
            fail(f"{name} is not listed in .claude-plugin/marketplace.json")
    for name, entry in listed.items():
        if name not in plugins:
            fail(f"marketplace.json lists '{name}', which has no plugin directory")
            continue
        source = entry.get("source")
        if source != f"./plugins/{name}":
            fail(f"marketplace.json: {name} source is '{source}'")


FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)
FM_KEY = re.compile(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$")


def frontmatter_keys(text: str) -> dict[str, str] | None:
    """Top-level keys of the YAML frontmatter block, or None if there is none.

    Deliberately a small parser rather than PyYAML: this runs in the plugin
    repositories, where the whole point is that validating content needs no
    toolchain. Nested keys are ignored — only the top level is contractual.
    """
    match = FRONTMATTER.match(text)
    if match is None:
        return None
    keys: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line[:1] in (" ", "\t", "#") or not line.strip():
            continue
        key = FM_KEY.match(line)
        if key:
            keys[key.group(1)] = key.group(2).strip().strip("\"'")
    return keys


def check_skills(plugins: dict[str, dict]) -> None:
    """Skill names are unique, and every skill carries a usable contract.

    The uniqueness rule and the contract rule fail the same way at runtime —
    the skill is simply not there — which is why both are hard failures rather
    than warnings. `sync()` reports a duplicate as a collision and links
    neither. `rebuild_registry()` deliberately degrades a skill with broken
    frontmatter to name-only rather than dropping it, so a missing description
    never surfaces as an error: the skill stays installed and stops being
    routable, because `skill-route` matches on name, description and triggers.
    A plugin must not be able to ship that quietly.
    """
    owner: dict[str, str] = {}
    total = 0
    for name in plugins:
        skills_dir = os.path.join(PLUGINS, name, "skills")
        if not os.path.isdir(skills_dir):
            notes.append(f"{name}: no skills/ directory")
            continue
        for skill in sorted(os.listdir(skills_dir)):
            skill_dir = os.path.join(skills_dir, skill)
            if not os.path.isdir(skill_dir) or skill.startswith("."):
                continue
            manifest = os.path.join(skill_dir, "SKILL.md")
            if not os.path.isfile(manifest):
                # `plugin add` counts a skill by its directory, so this one is
                # installed and linked, and then invisible to every consumer.
                fail(f"{name}/{skill}: directory has no SKILL.md")
                continue
            total += 1
            if skill in owner:
                # sync() reports this as a collision and links neither, so the
                # skill silently disappears rather than being overwritten.
                fail(f"skill '{skill}' is claimed by both {owner[skill]} and {name}")
            else:
                owner[skill] = name

            with open(manifest, encoding="utf-8", errors="replace") as handle:
                keys = frontmatter_keys(handle.read())
            if keys is None:
                fail(f"{name}/{skill}/SKILL.md: no YAML frontmatter block")
                continue
            for required in ("name", "description"):
                if not keys.get(required):
                    fail(f"{name}/{skill}/SKILL.md: frontmatter has no {required}")
            declared = keys.get("name")
            if declared and declared != skill:
                # The link is created under the directory name; discovery routes
                # on the declared name. When they disagree, `Skill(<name>)`
                # resolves to nothing.
                fail(
                    f"{name}/{skill}/SKILL.md: declares name '{declared}', "
                    f"directory is '{skill}'"
                )
    notes.append(f"{total} skills across {len(plugins)} plugins")


def check_no_links() -> None:
    """No symlinks and no gitlinks anywhere under plugins/.

    s5d fingerprinting fails closed on both and does not attest submodule
    contents, so either one makes the whole directory ungovernable the moment a
    component declares it.
    """
    out = subprocess.run(
        ["git", "ls-files", "-s", "--", "plugins/"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    ).stdout
    for line in out.splitlines():
        mode, _, rest = line.partition(" ")
        path = rest.split("\t", 1)[-1]
        if mode == "120000":
            fail(f"{path}: symlink (s5d fingerprinting fails closed on these)")
        elif mode == "160000":
            fail(f"{path}: gitlink (submodules are not attested)")


def check_paths() -> None:
    for dirpath, dirnames, filenames in os.walk(PLUGINS):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except (UnicodeDecodeError, OSError):
                continue
            for pattern, hint in FORBIDDEN:
                if pattern.search(text):
                    rel = os.path.relpath(path, ROOT)
                    fail(f"{rel}: contains {pattern.pattern} — {hint}")


def main() -> int:
    if not os.path.isdir(PLUGINS):
        print("no plugins/ directory — nothing to validate")
        return 0

    plugins = check_manifests()
    check_marketplace(plugins)
    check_skills(plugins)
    check_no_links()
    check_paths()

    for note in notes:
        print(f"  {note}")
    if failures:
        print(f"\n{len(failures)} failure(s):", file=sys.stderr)
        for f in failures:
            print(f"  ✗ {f}", file=sys.stderr)
        return 1
    print("\nplugins valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
