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

**Pick the account.** `gws auth list` shows five; the default is personal `voroninr@gmail.com`. Work files go to the matching work account (`rvoronin@quandex.com`, `rv@system5.dev`, `roman.vor@svsg.co`, `roman.voronin@workersbenefitfund.com`) — pass the same `--account <email>` on every call below (`ACCT` in the snippets).

## Modes

### Upload new file
```bash
FILE="path/to/file.mp4"
NAME="display-name.mp4"
DESC="optional description"
ACCT="voroninr@gmail.com"
MIME=$(file --mime-type -b "$FILE")
ID=$(gws drive files create --account "$ACCT" \
  --json "$(jq -nc --arg n "$NAME" --arg d "$DESC" --arg m "$MIME" '{name:$n, mimeType:$m, description:$d}')" \
  --upload "$FILE" \
  --params '{"supportsAllDrives": true}' \
  | jq -r .id)

gws drive permissions create --account "$ACCT" \
  --params "{\"fileId\":\"$ID\"}" \
  --json '{"role":"reader","type":"anyone"}'

echo "https://drive.google.com/file/d/$ID/view"
```

### Update existing file (same ID, same share link)
```bash
gws drive files update --account "$ACCT" \
  --params "{\"fileId\":\"$ID\"}" \
  --upload "$FILE"
echo "https://drive.google.com/file/d/$ID/view"
```

## Notes
- Without `--params '{"supportsAllDrives": true}'`, shared-drive uploads fail silently with a 404.
- Anyone-with-link is `{"role":"reader","type":"anyone"}`. Domain-only and other permission shapes: [Drive sharing guide](https://developers.google.com/workspace/drive/api/guides/manage-sharing).
- The view URL works for any MIME type. For inline embed use `https://drive.google.com/file/d/$ID/preview`.
- `gws --upload` is a multipart upload (the only upload flag in `gws --help`); size limits and resumable uploads: [Drive upload guide](https://developers.google.com/workspace/drive/api/guides/manage-uploads).

## Verification

```bash
gws drive files get --account "$ACCT" --params "{\"fileId\":\"$ID\", \"fields\":\"id,name,size,mimeType,permissions\"}"
```
