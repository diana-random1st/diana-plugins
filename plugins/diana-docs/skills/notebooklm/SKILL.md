---
name: notebooklm
description: "Google NotebookLM — query notebooks, add sources (URL/PDF/Drive/YouTube), generate podcasts, videos, slides, and quizzes, run web research, download artifacts."
triggers: ["notebooklm", "notebook lm", "подкаст из документов", "generate podcast", "audio overview"]
contracts:
  mandatory_tools: [Bash]
  verification: "Sources added with --wait, query returned answer with citations, artifacts downloaded if generated"
  exit_criteria: "NotebookLM result presented with source count, key findings, and notebook ID/alias for follow-up"
  requires_task: false
  requires_memory: false
---

# NotebookLM

All operations go through `nlm` CLI directly. Use noun-first style.

## Auth

If any command returns auth errors: `nlm login` (interactive browser).
Check status: `nlm auth status`.

## Core Workflow

### List notebooks
```bash
nlm notebook list
nlm notebook list --json    # structured output
```

### Query a notebook
```bash
nlm notebook query <id> "What are the key themes?"
nlm notebook query <id> "follow up" --conversation-id <cid>   # multi-turn
nlm notebook query <id> "question" --source-ids <id1,id2>     # specific sources
```

**Important:** `notebook query` works on EXISTING sources. For finding NEW sources, use `research start`.

### Create notebook
```bash
nlm notebook create "My Research"
```

### Add sources
```bash
# URL (web page or YouTube)
nlm source add <notebook-id> --url "https://example.com" --wait

# Multiple URLs (run sequentially)
nlm source add <notebook-id> --url "https://a.com" --wait
nlm source add <notebook-id> --url "https://b.com" --wait

# Local file (PDF, TXT, MP3, WAV, M4A)
nlm source add <notebook-id> --file /path/to/doc.pdf --wait

# Pasted text
nlm source add <notebook-id> --text "Content here" --title "My Notes"

# Google Drive (types: doc, slides, sheets, pdf)
nlm source add <notebook-id> --drive <doc-id> --type doc
```

## Content Generation

All generation requires `--confirm` flag. Optionally: `--source-ids`, `--language <BCP-47>`, `--focus "topic"`.

```bash
# Podcast (audio overview)
nlm audio create <notebook-id> --format deep_dive --length default --confirm
# Formats: deep_dive | brief | critique | debate
# Lengths: short | default | long

# Video
nlm video create <notebook-id> --format explainer --style whiteboard --confirm
# Styles: auto_select | classic | whiteboard | kawaii | anime | watercolor | retro_print | heritage | paper_craft

# Report
nlm report create <notebook-id> --format "Study Guide" --confirm
# Formats: "Briefing Doc" | "Study Guide" | "Blog Post" | "Create Your Own" (needs --prompt)

# Quiz
nlm quiz create <notebook-id> --count 10 --difficulty 3 --confirm

# Flashcards
nlm flashcards create <notebook-id> --difficulty hard --confirm
# Difficulty: easy | medium | hard

# Slide deck
nlm slides create <notebook-id> --format detailed_deck --confirm
# Formats: detailed_deck | presenter_slides

# Infographic
nlm infographic create <notebook-id> --orientation landscape --detail standard --confirm
# Styles: auto_select | sketch_note | professional | bento_grid | editorial | instructional | bricks | clay | anime | kawaii | scientific

# Mind map
nlm mindmap create <notebook-id> --confirm

# Data table (description required)
nlm data-table create <notebook-id> "Extract all dates and events" --confirm
```

**Languages:** BCP-47 codes via `--language` (en, ru, es, fr, de, ja, etc.)

## Download Artifacts

```bash
# Check status first (wait for "completed")
nlm studio status <notebook-id>

# Audio → MP3
nlm download audio <notebook-id> --id <artifact-id> --output podcast.mp3

# Video → MP4
nlm download video <notebook-id> --id <artifact-id>

# Slides → PDF or PPTX
nlm download slide-deck <notebook-id> --id <artifact-id> --format pptx

# Report
nlm download report <notebook-id> --id <artifact-id> --output report.md

# Quiz/Flashcards (formats: json | markdown | html)
nlm download quiz <notebook-id> <artifact-id> --format html
nlm download flashcards <notebook-id> <artifact-id> --format markdown

# Infographic → PNG
nlm download infographic <notebook-id> --id <artifact-id>

# Data table → CSV
nlm download data-table <notebook-id> --id <artifact-id>

# Mind map
nlm download mind-map <notebook-id> --id <artifact-id>
```

## Research (Find New Sources)

```bash
# Start web research (--notebook-id required)
nlm research start "quantum computing 2026" --notebook-id <id>
nlm research start "query" --notebook-id <id> --mode deep    # ~5min, ~40-80 sources
nlm research start "query" --notebook-id <id> --source drive  # search Google Drive

# Check status
nlm research status <notebook-id>
nlm research status <notebook-id> --max-wait 0   # single check, no polling

# Import found sources
nlm research import <notebook-id> <task-id>
nlm research import <notebook-id> <task-id> --indices 0,2,5  # specific ones
```

**Modes:** fast (~30s, ~10 sources) | deep (~5min, ~40-80 sources, web only)

## Aliases (shortcuts for UUIDs)

```bash
nlm alias list
nlm alias set myproject <uuid>
nlm alias get myproject
# Then use alias anywhere: nlm notebook query myproject "question"
```

## Sharing

```bash
nlm share status <notebook-id>
nlm share public <notebook-id>
nlm share private <notebook-id>
nlm share invite <notebook-id> user@email.com --role editor
```

## Export to Google Workspace

```bash
nlm export to-docs <notebook-id> <artifact-id>     # Report → Google Docs
nlm export to-sheets <notebook-id> <artifact-id>   # Data table → Google Sheets
```

## Revise Slides

```bash
nlm slides revise <artifact-id> --slide '1 Make title larger' --slide '3 Remove image' --confirm
```

## Tips

- Always `--confirm` for generation/delete commands
- Audio/video: 1-5 min generation time. Poll with `nlm studio status`
- Use `--wait` when adding sources before querying
- Never use `nlm chat start` (interactive REPL) — use `nlm notebook query` instead
- Use `--json` only when parsing fields programmatically; default output is token-efficient
