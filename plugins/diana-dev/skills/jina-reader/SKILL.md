---
name: jina-reader
description: "Web content extraction via Jina Reader for JS-heavy sites, PDFs, and pages where WebFetch fails. Triggers: 'can\\'t read page', 'javascript site', 'jina'."
---

# Jina Reader

Advanced web research via Jina Reader (r.jina.ai) for JS-heavy sites, PDFs, and noisy pages.

## Invocation

**Trigger phrases:**
- "can't read this page"
- "javascript required"
- "read this PDF from URL"
- "clean version of this page"
- "jina read"

## Core Function

Convert complex URLs, PDFs, and JS-heavy sites into clean, LLM-friendly Markdown.

## Usage Patterns

### Basic Web Page

Prepend `https://r.jina.ai/` to any URL:

```
https://r.jina.ai/https://example.com/article
```

### Search

Use the search endpoint for summarized results:

```
https://s.jina.ai/?q=YOUR_QUERY
```

### PDF from URL

Prepend to a direct PDF link:

```
https://r.jina.ai/https://example.com/document.pdf
```

## Optimization Headers

When using WebFetch with Jina URLs, consider these implicit optimizations:

| Header | Description | Example |
|--------|-------------|---------|
| `X-Target-Selector` | CSS selector for relevant part only | `article`, `.main-content` |
| `X-With-Generated-Alt` | AI-generated image descriptions | `true` |
| `X-With-Links-Summary` | List of all links at document end | `true` |
| `X-Return-Format` | Output format | `markdown` (default), `text` |

## When to Use (Instead of Standard WebFetch)

1. **SPA/JavaScript Required** - Site needs JS to render content
2. **Soft Paywall** - Aggressive anti-bot measures
3. **Noisy Pages** - Ads, popups, navigation clutter
4. **PDF from URL** - Need text extraction from remote PDF
5. **Image Descriptions** - Need to understand visual content

## Fallback Protocol

If standard WebFetch returns:
- "JavaScript required"
- "Captcha"
- Empty or minimal content
- Timeout on complex page

**Immediately retry** with Jina prefix:

```python
# Pseudocode
result = WebFetch(url, prompt)
if result.failed or result.empty:
    jina_url = f"https://r.jina.ai/{url}"
    result = WebFetch(jina_url, prompt)
```

## Examples

### Reading a JS-Heavy Article

```
WebFetch(
    url="https://r.jina.ai/https://medium.com/@author/article-slug",
    prompt="Summarize the main points"
)
```

### PDF Text Extraction

```
WebFetch(
    url="https://r.jina.ai/https://example.com/whitepaper.pdf",
    prompt="Extract key findings from this research paper"
)
```

### Targeted Content Extraction

For token efficiency, target specific selectors:

```
# LinkedIn profile (hypothetical - target main content)
https://r.jina.ai/https://linkedin.com/in/username

# Twitter/X thread
https://r.jina.ai/https://x.com/user/status/123456
```

## Limitations

- Rate limits apply
- Some sites may still block
- Large documents may be truncated
- Real-time content may be cached

## Integration Notes

This skill augments WebFetch, not replaces it. Use standard WebFetch first; fall back to Jina on failure.
