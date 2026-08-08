---
name: xlsx
description: Use for spreadsheet reading, creation, editing, or modeling when formulas, formatting, template preservation, and recalculation accuracy matter.
---

# XLSX

Use this skill when the file is a spreadsheet artifact, not just a table dump.

Workflow:
1. Read [references/workflow.md](./references/workflow.md) and choose the narrow path: analyze, create, edit, or model.
2. Preserve existing template conventions exactly when updating a real workbook.
3. Use formulas for derived values; do not hardcode calculations that Excel should own.
4. Use `pandas` for analysis and bulk data shaping, `openpyxl` for workbook structure, formulas, comments, and formatting.
5. If the workbook contains formulas, recalculate with `skills/xlsx/recalc.py` before presenting.
6. Ship with zero Excel formula errors and verify the cells called out by the recalc report.
7. When the workbook is financial, keep assumptions explicit, sources documented, and color/number conventions consistent with the template or the workflow guide.
