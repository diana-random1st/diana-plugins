---
name: gdrive-share
description: "Upload a file to Google Drive via the gws CLI, set anyone-with-link viewer access, and return the share URL. Can also update an existing file by ID."
triggers: ["upload to drive", "share via drive", "gdrive link", "put on google drive", "залей на гуглдрайв"]
user-invocable: true
allowed-tools: Bash
---

# gdrive-share

Wraps the `gws` Google Workspace CLI for the common case: "upload this file, give me a public-readable link".

## Prereq

`gws` CLI must be installed and authenticated (`/opt/homebrew/bin/gws`). If `gws drive files list` fails, the user must `gws auth login` first.

## Modes

### Upload new file
```bash
FILE="path/to/file.mp4"
NAME="display-name.mp4"
DESC="optional description"
ID=$(gws drive files create \
  --json "$(jq -nc --arg n "$NAME" --arg d "$DESC" '{name:$n, mimeType:"video/mp4", description:$d}')" \
  --upload "$FILE" \
  --params '{"supportsAllDrives": true}' \
  | jq -r .id)

gws drive permissions create \
  --params "{\"fileId\":\"$ID\"}" \
  --json '{"role":"reader","type":"anyone"}'

echo "https://drive.google.com/file/d/$ID/view"
```

### Update existing file (same ID, same share link)
```bash
gws drive files update \
  --params "{\"fileId\":\"$ID\"}" \
  --upload "$FILE"
echo "https://drive.google.com/file/d/$ID/view"
```

## Notes
- Detect MIME by extension or call `file --mime-type -b "$FILE"`.
- Without `--params '{"supportsAllDrives": true}'`, shared-drive uploads fail silently with a 404.
- Anyone-with-link is `{"role":"reader","type":"anyone"}`. For domain-only use `{"type":"domain", "domain":"example.com", "role":"reader"}`.
- The view URL works for any MIME type. For inline embed use `https://drive.google.com/file/d/$ID/preview`.
- Quota: Drive accepts up to 5 TiB per file. For large files use resumable upload (`--upload` handles it transparently for ≤256 MB; bigger may need `gws drive files create --upload-resumable`).

## Verification

```bash
gws drive files get --params "{\"fileId\":\"$ID\", \"fields\":\"id,name,size,mimeType,permissions\"}"
```
