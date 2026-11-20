---
name: jina-reader
description: "Read a page through Jina Reader (r.jina.ai) when WebFetch fails — JS-heavy sites, remote PDFs, noisy pages. Triggers: 'can\\'t read page', 'javascript site', 'jina'."
---

# Jina Reader

Use after WebFetch fails: "JavaScript required", a captcha, an empty or truncated body, a remote PDF.

Prefix the URL with `https://r.jina.ai/`. Keyless; returns Markdown with title and source URL:

```
WebFetch(url="https://r.jina.ai/https://example.com/article", prompt="…")
```

WebFetch cannot send headers. To pick a CSS selector or the output format, fetch with Python (header list: https://github.com/jina-ai/reader):

```bash
python3 -c "import urllib.request as u,sys;print(u.urlopen(u.Request('https://r.jina.ai/'+sys.argv[1],headers={'X-Target-Selector':'article','X-Return-Format':'markdown','User-Agent':'Mozilla/5.0'}),timeout=60).read().decode())" 'https://example.com/article'
```

Facts:
- `s.jina.ai` (search) returns 401 without an API key, and the vault has no Jina key: search with WebSearch instead.
- Keyless calls are rate-limited and may serve a cached copy; check the date for live content.
- A page that needs Roman's login → `browser-cdp`, not Jina.
