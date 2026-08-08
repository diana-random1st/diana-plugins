# XLSX workflow

## Core invariants

- zero formula errors: no `#REF!`, `#DIV/0!`, `#VALUE!`, `#N/A`, or `#NAME?`
- existing templates override generic formatting advice
- derived values belong in formulas, not Python-calculated constants

## Choose the tool

Use `pandas` for:
- reading and analyzing sheet data
- multi-sheet exports from dataframes
- bulk reshaping and joins

Use `openpyxl` for:
- preserving workbook structure
- formulas
- comments and assumptions
- styling, widths, merges, and sheet-level edits

## Analyze a workbook

- load the relevant sheet or all sheets
- inspect structure, datatypes, blanks, and key formulas
- if formula outputs matter, compare the formula view with recalculated values before drawing conclusions

## Create or edit a workbook

Recommended sequence:
1. load or create the workbook
2. add raw inputs first
3. add formulas for derived values
4. apply formatting only after the data shape is stable
5. save
6. recalculate
7. fix any reported errors

Recalculation:

```bash
python skills/xlsx/recalc.py output.xlsx
```

Optional timeout:

```bash
python skills/xlsx/recalc.py output.xlsx 30
```

## Formula discipline

- use cell references instead of embedding growth rates, margins, or multipliers directly into formulas
- test a few sample references before filling a whole table
- watch for off-by-one ranges, cross-sheet typos, and division by zero
- do not open with `data_only=True` and then save unless you explicitly want to destroy formulas

Examples:

```python
ws["B10"] = "=SUM(B2:B9)"
ws["C5"] = "=(C4-C2)/C2"
ws["D20"] = "=AVERAGE(D2:D19)"
```

## Financial workbook conventions

Unless the existing template says otherwise:
- blue text for hardcoded inputs
- black text for formulas
- green text for intra-workbook links
- red text for external links
- yellow fill for key assumptions
- parentheses for negatives
- explicit units in headers such as `Revenue ($mm)`

Every hardcoded assumption should be easy to trace. Use comments or adjacent notes in this format:

```text
Source: <system or document>, <date>, <specific reference>, <URL if useful>
```

## Verification

After recalculation:
- inspect the JSON result from `recalc.py`
- fix every error location it reports
- spot-check important formulas and totals manually
- visually inspect formatting, widths, frozen panes, and any presentation sheets

Do not call the workbook done until the recalc result is clean and the visible workbook still matches the intended template.
