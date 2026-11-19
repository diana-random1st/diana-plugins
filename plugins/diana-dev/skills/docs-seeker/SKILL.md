---
name: docs-seeker
description: Use when you need current technical documentation, release notes, API references, or repository docs from primary sources.
---

# Docs Seeker

Find and summarize technical documentation without guessing.

1. **Pin the target.** Exact library, product, site or repo, plus the version or date scope.
2. **Sources, in order:**
   - context7 through the `docs` skill: versioned library docs.
   - The vendor's own `llms.txt` / `llms-full.txt` at the docs root (format: https://llmstxt.org/), e.g. https://docs.djangoproject.com/llms.txt. Many doc sites also serve one page as Markdown: Apple HIG takes `.md` on the page URL (https://developer.apple.com/design/human-interface-guidelines/layout.md).
   - Repository docs and releases:
     ```bash
     gh release view -R <owner>/<repo> --json tagName,publishedAt,body
     gh api repos/<owner>/<repo>/contents/<docs-path> --jq '.[].path'
     ```
   - WebFetch on the official page; JS-heavy page or remote PDF → `jina-reader`.
   - Web search restricted to the official domain, last.
3. **"Latest" or "current"** → verify live, report the access date and the exact URL.
4. **Sources conflict** → show the conflict, do not average it away.
5. **Parallel reads** only for independent sources (one subagent per source set), and only when the host allows it.
