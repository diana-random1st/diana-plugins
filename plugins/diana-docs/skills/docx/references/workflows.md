# DOCX workflows

Choose the smallest workflow that fits the task.

## Read or analyze content

Use this when you need text, headings, tracked changes, or structure.

- Prefer markdown extraction first:

```bash
pandoc --track-changes=all input.docx -o review.md
```

- Use raw OOXML only when you need comments, revision tags, embedded media, metadata, or exact run structure.
- For raw OOXML, inspect the archive contents:
  - `word/document.xml`
  - `word/comments.xml`
  - `word/media/`
  - tracked changes via `<w:ins>` and `<w:del>`

## Create a new document

- Read `docx-js.md` first; it is the creation authority.
- Use `docx` for document generation, paragraphs, runs, tables, and export.
- Keep generated code concise and avoid noisy helper scaffolding unless the task needs it.

## Edit an existing document

- Read `ooxml.md` first; it is the editing authority.
- Use the existing Python helpers under `scripts/` when you need structured document manipulation rather than fragile string replacement.
- When direct OOXML access is needed, unpack the `.docx` to a scratch directory, edit there, then repack into a new output file.
- Preserve surrounding unchanged runs wherever possible; do not rewrite whole paragraphs when only a few tokens changed.

## Redline and review workflow

Default here for external or formal documents.

1. Convert the source to markdown with tracked changes visible.
2. Identify all required edits and group them into logical batches.
3. Map target text back to OOXML before scripting changes.
4. Apply only the changed tokens as insertions/deletions when possible.
5. Repack and verify after each meaningful batch, not only at the very end.

Guidelines:
- keep replacements minimal and precise
- preserve unchanged text as unchanged text
- do not rely on markdown line numbers to find XML nodes
- use unique surrounding text, headings, or section labels instead

## Visual verification

Use this when pagination, spacing, figures, or review markup positioning matters.

```bash
soffice --headless --convert-to pdf input.docx
pdftoppm -jpeg -r 150 input.pdf page
```

Then inspect the generated page images for layout regressions, overflow, and accidental formatting changes.

## Dependency notes

- `pandoc` is the preferred text extraction tool.
- LibreOffice is useful for rendering or PDF conversion.
- Poppler tools such as `pdftoppm` are useful for page images.
- Python dependencies for the OOXML helpers should be installed with the local Python environment rather than assumed system-wide.
