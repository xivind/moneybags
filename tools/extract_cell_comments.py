"""
Extract cell comments from old budget spreadsheets into a review sheet.

The original Google Sheets budgets stored several purchases in one cell as a
formula (e.g. ``=34+850+90+456``) and explained each amount in the cell
comment (e.g. ``850 = Bikeshop``). The Moneybags importer split every formula
into one transaction per amount, but the comments were not imported, so the
transactions all got the generic "Import - Google Sheets" payee.

This script is READ-ONLY. It never touches the database. It reads one or
more .xlsx files and writes a single review workbook with one row per amount,
paired with the matching line from the cell comment, so payees can be fixed
manually in Moneybags without hovering over cells one by one.

Google Sheets files (.gsheet) are only links; download them first via
File -> Download -> Microsoft Excel (.xlsx).

Usage:
    python tools/extract_cell_comments.py FILE.xlsx [FILE.xlsx ...] -o review.xlsx
    python tools/extract_cell_comments.py Budsjett_2013.xlsx --year 2013

Match statuses in the output:
    match            Amount from the formula found in the comment
    amount_differs   One amount and one comment line left over in the cell,
                     paired up although the numbers differ
    sum_of_lines     One amount in the cell is split into several comment
                     lines (followed by one part_of_sum row per line)
    no_comment_line  Amount from the formula with no line in the comment
    comment_only     Comment line with an amount that is not in the formula
    no_amount        Comment line without any amount
    formula_unparsed Formula is not a simple sum; only the comment is listed
    no_comment       Actual (Resultat) amount in a cell without any comment
"""

import argparse
import re
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

MONTH_PREFIXES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "mai": 5, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "okt": 10, "oct": 10, "nov": 11,
    "des": 12, "dec": 12,
}

ROW_TYPES = {"budsjett": "Budsjett", "resultat": "Resultat"}

# Labels that describe a row, not a category
NON_CATEGORY_LABELS = ("budsjett", "resultat", "differanse", "avvik", "totalt")

SECTION_LABELS = ("utgifter", "inntekter")

# An amount like 850, 3.400, 123.456, 3 400 or 1500,50
_AMOUNT = r"\d{1,3}(?:[.\s ]\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?"
_SEP = r"\s*(?:kr\.?|,-)?\s*[=:]\s*"
_LEADING_AMOUNT = re.compile(rf"^\s*(?:kr\.?\s*)?({_AMOUNT}){_SEP}(.*?)\s*$", re.IGNORECASE)
_TRAILING_AMOUNT = re.compile(rf"^\s*(.*?)\s*[=:]\s*(?:kr\.?\s*)?({_AMOUNT})\s*(?:kr\.?|,-)?\s*$", re.IGNORECASE)
_SIMPLE_SUM = re.compile(r"\d+(?:\.\d+)?(?:\+\d+(?:\.\d+)?)*")

# Month labels as shown in the Moneybags Budget & Actuals view
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# year + month + section + category locate the cell in Moneybags;
# cell points back to the original spreadsheet
OUTPUT_COLUMNS = [
    ("file", 28), ("sheet", 12), ("year", 6), ("month", 7),
    ("section", 10), ("category", 26), ("row_type", 10), ("amount", 10),
    ("description", 40), ("match", 16), ("payee", 22), ("note", 22),
    ("cell", 7), ("cell_formula", 30), ("cell_comment", 60),
]


def parse_amount(text: str) -> int:
    """Convert '3.400', '123 456' or '1500,50' to an integer (decimals dropped)."""
    text = text.strip().replace(" ", " ")
    if re.fullmatch(r"\d{1,3}(?:[.\s]\d{3})+(?:,\d{1,2})?", text):
        text = re.sub(r"[.\s]", "", text)
    return int(float(text.replace(",", ".")))


def clean_comment(text: str) -> list[str]:
    """
    Split a comment into lines, dropping blanks and boilerplate.

    Handles both kinds of Google Sheets annotations exported to .xlsx:
    notes end with a '\t-Author' signature line, and comments (threaded
    comments in Excel) come with a '[Threaded comment]' header and
    'Comment:' / 'Reply:' markers before each message.
    """
    lines = []
    raw_lines = (text or "").splitlines()
    if raw_lines and raw_lines[0].strip() == "[Threaded comment]":
        raw_lines = raw_lines[1:]
        if raw_lines and raw_lines[0].lstrip().startswith("Your version of Excel"):
            raw_lines = raw_lines[1:]
    for line in raw_lines:
        if re.match(r"^\t+-", line) or re.fullmatch(r"\s*(Comment|Reply):\s*", line):
            continue
        line = line.strip()
        if line and not re.fullmatch(r"[-_=*\s]+", line):
            lines.append(line)
    return lines


def parse_comment_line(line: str) -> tuple[int | None, str]:
    """Return (amount, description) for one comment line. Amount is None if absent."""
    m = _LEADING_AMOUNT.match(line)
    if m:
        return parse_amount(m.group(1)), m.group(2)
    m = _TRAILING_AMOUNT.match(line)
    if m and m.group(1):
        return parse_amount(m.group(2)), m.group(1)
    return None, line


def formula_terms(value) -> list[int] | None:
    """
    Split a cell value into amounts the same way the importer did.

    Returns a list of ints, [] for empty cells, or None when the value is not
    a plain number or simple sum (so it cannot be matched term by term).
    """
    if value is None or value == "":
        return []
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return [int(value)]
    text = str(value).strip()
    if text.startswith("="):
        text = text[1:]
    text = text.replace("(", "").replace(")", "").replace(" ", "")
    if not text:
        return []
    if not _SIMPLE_SUM.fullmatch(text):
        return None
    return [int(float(part)) for part in text.split("+")]


def match_terms(terms: list[int], comment_lines: list[str]) -> list[dict]:
    """
    Pair formula amounts with comment lines by amount, in formula order.

    Never guesses beyond one leftover amount and one leftover line in the same
    cell; everything else is reported with its status for manual review.
    """
    parsed = [parse_comment_line(line) for line in comment_lines]
    used = [False] * len(parsed)
    rows = []

    for term in terms:
        for i, (amount, description) in enumerate(parsed):
            if not used[i] and amount == term:
                used[i] = True
                rows.append({"amount": term, "description": description, "match": "match"})
                break
        else:
            rows.append({"amount": term, "description": None, "match": "no_comment_line"})

    leftover_terms = [r for r in rows if r["match"] == "no_comment_line"]
    leftover_lines = [i for i, (amount, _) in enumerate(parsed) if not used[i] and amount is not None]
    if (len(leftover_terms) == 1 and len(leftover_lines) > 1
            and sum(parsed[i][0] for i in leftover_lines) == leftover_terms[0]["amount"]):
        # One amount in the cell, split into several lines in the comment
        for i in leftover_lines:
            used[i] = True
            rows.append({"amount": parsed[i][0], "description": parsed[i][1], "match": "part_of_sum",
                         "note": f"part of {leftover_terms[0]['amount']}"})
        leftover_terms[0]["description"] = " + ".join(parsed[i][1] for i in leftover_lines)
        leftover_terms[0]["match"] = "sum_of_lines"
    elif len(leftover_terms) == 1 and len(leftover_lines) == 1:
        i = leftover_lines[0]
        used[i] = True
        leftover_terms[0]["description"] = parsed[i][1]
        leftover_terms[0]["match"] = "amount_differs"
        leftover_terms[0]["note"] = f"comment says {parsed[i][0]}"

    for i, (amount, description) in enumerate(parsed):
        if not used[i]:
            rows.append({
                "amount": amount,
                "description": description,
                "match": "comment_only" if amount is not None else "no_amount",
            })
    return rows


def _text(value) -> str:
    """Text of a label cell; formulas and numbers are not labels."""
    if not isinstance(value, str) or value.lstrip().startswith("="):
        return ""
    return value.strip()


def find_month_columns(ws) -> tuple[int | None, dict[int, int]]:
    """Find the header row with month names. Returns (row, {column: month})."""
    best_row, best = None, {}
    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 30)):
        found = {}
        for cell in row:
            name = _text(cell.value).lower()
            if len(name) >= 3 and name[:3] in MONTH_PREFIXES:
                found[cell.column] = MONTH_PREFIXES[name[:3]]
        if len(found) > len(best):
            best_row, best = row[0].row, found
    if len(best) < 6:
        return None, {}
    return best_row, best


def describe_row(ws, row: int, label_cols: range, header_row: int | None) -> dict:
    """Work out category, row type and section for a row from its label columns."""
    def labels(r):
        return [_text(ws.cell(r, c).value) for c in label_cols if _text(ws.cell(r, c).value)]

    row_type = None
    for label in labels(row):
        if label.lower() in ROW_TYPES:
            row_type = ROW_TYPES[label.lower()]

    category = None
    stop = header_row or 0
    for r in range(row, max(stop, row - 4), -1):
        for label in labels(r):
            low = label.lower()
            if low.startswith(NON_CATEGORY_LABELS) or low in SECTION_LABELS:
                continue
            category = label
            break
        if category or (r != row and any(l.lower() in SECTION_LABELS for l in labels(r))):
            break

    section = None
    for r in range(row, stop, -1):
        for label in labels(r):
            if label.lower() in SECTION_LABELS:
                section = label
                break
        if section:
            break

    return {"category": category, "row_type": row_type, "section": section}


def extract_from_workbook(path: Path, year: int | None) -> list[dict]:
    """
    Return one output row per amount / comment line for every commented cell.

    Actual (Resultat) cells without a comment are listed too, with match
    "no_comment", so every imported transaction appears in the review.
    """
    wb = load_workbook(path, data_only=False)
    rows = []
    for ws in wb.worksheets:
        header_row, month_cols = find_month_columns(ws)
        first_month_col = min(month_cols) if month_cols else ws.max_column + 1
        label_cols = range(1, first_month_col)

        for sheet_row in ws.iter_rows():
            for cell in sheet_row:
                month = month_cols.get(cell.column)
                comment_lines = clean_comment(cell.comment.text) if cell.comment else []

                if not comment_lines:
                    if month is None or cell.value in (None, ""):
                        continue
                    context = describe_row(ws, cell.row, label_cols, header_row)
                    terms = formula_terms(cell.value)
                    category = context["category"] or ""
                    # Zero cells were not imported, totals are computed rows
                    if (context["row_type"] != "Resultat" or not terms or not any(terms)
                            or category.lower().startswith("total")):
                        continue
                    matched = [{"amount": t, "description": None, "match": "no_comment"} for t in terms]
                    rows.extend(_output_row(path, ws, year, month, cell, context, item, [])
                                for item in matched)
                    continue

                context = describe_row(ws, cell.row, label_cols, header_row)
                if month is None:
                    # A note on a label or summary cell: list it, don't match it
                    terms = []
                else:
                    terms = formula_terms(cell.value)

                if terms is None:
                    matched = [{"amount": a, "description": d, "match": "formula_unparsed"}
                               for a, d in map(parse_comment_line, comment_lines)]
                else:
                    matched = match_terms(terms, comment_lines)

                rows.extend(_output_row(path, ws, year, month, cell, context, item, comment_lines)
                            for item in matched)
    return rows


def _output_row(path, ws, year, month, cell, context, item, comment_lines) -> dict:
    return {
        "file": path.name,
        "sheet": ws.title,
        "year": year,
        "month": MONTH_NAMES[month - 1] if month else None,
        "cell": cell.coordinate,
        "section": context["section"],
        "category": context["category"],
        "row_type": context["row_type"],
        "amount": item["amount"],
        "description": item["description"],
        "match": item["match"],
        "payee": None,
        "note": item.get("note"),
        "cell_formula": None if cell.value is None else str(cell.value),
        "cell_comment": "\n".join(comment_lines) or None,
    }


def year_from_filename(path: Path) -> int | None:
    m = re.search(r"(?<!\d)(19|20)\d{2}(?!\d)", path.stem)
    return int(m.group(0)) if m else None


def write_review(rows: list[dict], output: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Kommentarer"
    ws.append([name for name, _ in OUTPUT_COLUMNS])
    for row in rows:
        ws.append([row[name] for name, _ in OUTPUT_COLUMNS])
    for i, (_, width) in enumerate(OUTPUT_COLUMNS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("files", nargs="+", type=Path, help=".xlsx files to read")
    parser.add_argument("-o", "--output", type=Path, default=Path("cell_comments_review.xlsx"),
                        help="review workbook to write (default: cell_comments_review.xlsx)")
    parser.add_argument("--year", type=int,
                        help="year for all files (default: taken from each file name)")
    args = parser.parse_args(argv)

    all_rows = []
    for path in args.files:
        if path.suffix.lower() == ".gsheet":
            print(f"{path.name}: .gsheet is only a link; download it as .xlsx first", file=sys.stderr)
            continue
        year = args.year or year_from_filename(path)
        rows = extract_from_workbook(path, year)
        counts = {}
        for r in rows:
            counts[r["match"]] = counts.get(r["match"], 0) + 1
        summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
        print(f"{path.name} (year {year}): {len(rows)} rows ({summary})")
        all_rows.extend(rows)

    if not all_rows:
        print("No comments found.", file=sys.stderr)
        return 1
    write_review(all_rows, args.output)
    print(f"Wrote {len(all_rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
