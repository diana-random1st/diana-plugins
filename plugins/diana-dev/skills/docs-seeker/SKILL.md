---
name: docs-seeker
description: Use when you need current technical documentation, release notes, API references, or repository docs from primary sources.
---

# Docs Seeker

Use this skill to find and summarize technical documentation without guessing.

Core route:
1. Identify the exact library, product, site, or repository, plus the requested version or date scope.
2. Prefer primary sources in this order: official docs, official `llms.txt`, official repository docs/examples, then carefully labeled fallback research.
3. If the request is for the latest or current behavior, verify it live and report the access date and the exact source used.
4. If sources conflict, surface the conflict instead of averaging them into one answer.
5. Use [WORKFLOWS.md](./WORKFLOWS.md) for the full discovery flow and these direct references as needed:
   - [references/tool-selection.md](./references/tool-selection.md)
   - [references/documentation-sources.md](./references/documentation-sources.md)
   - [references/error-handling.md](./references/error-handling.md)
   - [references/best-practices.md](./references/best-practices.md)
   - [references/performance.md](./references/performance.md)
   - [references/limitations.md](./references/limitations.md)
6. Parallelize only when the host permits it and the work is genuinely separable into independent source reads.
