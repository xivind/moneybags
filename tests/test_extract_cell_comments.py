"""
Tests for tools/extract_cell_comments.py

Uses a small synthetic workbook; no real budget data.
"""

from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment

from tools.extract_cell_comments import (
    clean_comment,
    extract_from_workbook,
    formula_terms,
    main,
    match_terms,
    parse_amount,
    parse_comment_line,
    year_from_filename,
)

SIG = "\n\t-Test Person"


def test_parse_amount_thousand_separators():
    assert parse_amount("850") == 850
    assert parse_amount("2.200") == 2200
    assert parse_amount("158.250") == 158250
    assert parse_amount("2 200") == 2200
    assert parse_amount("1500,50") == 1500


def test_clean_comment_drops_signature_and_separators():
    text = "420 = Gym" + SIG + "\n----\n700 = Rent" + SIG
    assert clean_comment(text) == ["420 = Gym", "700 = Rent"]


def test_parse_comment_line_variants():
    assert parse_comment_line("2.200 = Common costs") == (2200, "Common costs")
    assert parse_comment_line("850: Bike shop") == (850, "Bike shop")
    assert parse_comment_line("Bike shop = 850") == (850, "Bike shop")
    assert parse_comment_line("Electricity") == (None, "Electricity")


def test_formula_terms_matches_importer_splitting():
    assert formula_terms("=((1200+300)+45)+7") == [1200, 300, 45, 7]
    assert formula_terms(2200) == [2200]
    assert formula_terms("=55615.0") == [55615]
    assert formula_terms(None) == []
    assert formula_terms("=SUM(F1:Q1)") is None
    assert formula_terms("=100-20") is None


def test_match_terms_pairs_by_amount_in_order():
    rows = match_terms([34, 850, 90, 34], ["34 = Misc A", "850 = Bike shop", "90 = Sunglasses", "34 = Misc B"])
    assert [(r["amount"], r["description"], r["match"]) for r in rows] == [
        (34, "Misc A", "match"),
        (850, "Bike shop", "match"),
        (90, "Sunglasses", "match"),
        (34, "Misc B", "match"),
    ]


def test_match_terms_single_leftover_is_amount_differs():
    rows = match_terms([100, 9990], ["100 = Cable", "9.999 = Laptop"])
    assert rows[1]["match"] == "amount_differs"
    assert rows[1]["description"] == "Laptop"
    assert "9999" in rows[1]["note"]


def test_match_terms_one_amount_split_in_comment():
    rows = match_terms([1500], ["1.000 = Salary", "500 = Grant"])
    assert rows[0]["match"] == "sum_of_lines"
    assert rows[0]["description"] == "Salary + Grant"
    assert [r["match"] for r in rows[1:]] == ["part_of_sum", "part_of_sum"]


def test_match_terms_reports_unmatched():
    rows = match_terms([10, 20, 30], ["99 = Something", "Note without amount"])
    statuses = [r["match"] for r in rows]
    assert statuses.count("no_comment_line") == 3
    assert "comment_only" in statuses
    assert "no_amount" in statuses


def _make_hovedark(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Hovedark"
    months = ["Januar", "Februar", "Mars", "April", "Mai", "Juni",
              "Juli", "August", "September", "Oktober", "November", "Desember"]
    ws["E5"] = "Totalt"
    for i, name in enumerate(months):
        ws.cell(5, 6 + i, name)
    ws["C10"] = "Utgifter"
    ws["C11"] = "Housing"
    ws["D11"] = "Budsjett"
    ws["E11"] = '=IF((SUM(F11:Q11)=0), "", SUM(F11:Q11))'
    ws["F11"] = 2000
    ws["F11"].comment = Comment("2.000 = Common costs" + SIG, "x")
    ws["D12"] = "Resultat"
    ws["E12"] = '=IF((SUM(F12:Q12)=0), "", SUM(F12:Q12))'
    ws["F12"] = "=(1950+120)+40"
    ws["F12"].comment = Comment("1.950 = Common costs\n120 = Electricity\n40 = Light bulbs" + SIG, "x")
    ws["G12"] = 1950          # no comment -> listed as no_comment
    ws["H12"] = 0             # zero -> not imported, not listed
    ws["C20"] = "Inntekter"
    ws["C21"] = "Salary"
    ws["D21"] = "Budsjett"
    ws["D22"] = "Resultat"
    ws["F22"] = 1500
    ws["F22"].comment = Comment("1.000 = Employer\n500 = Grant" + SIG, "x")
    ws["C30"] = "Totale utgifter"
    ws["D30"] = "Budsjett"
    ws["D31"] = "Resultat"
    ws["F31"] = 999           # total row -> not listed
    wb.save(path)


def test_extract_from_workbook(tmp_path):
    path = tmp_path / "Budget_2013.xlsx"
    _make_hovedark(path)
    rows = extract_from_workbook(path, 2013)

    actuals = [r for r in rows if r["row_type"] == "Resultat"]
    f12 = [(r["category"], r["section"], r["month"], r["amount"], r["description"], r["match"])
           for r in actuals if r["cell"] == "F12"]
    assert f12 == [
        ("Housing", "Utgifter", 1, 1950, "Common costs", "match"),
        ("Housing", "Utgifter", 1, 120, "Electricity", "match"),
        ("Housing", "Utgifter", 1, 40, "Light bulbs", "match"),
    ]

    g12 = [r for r in actuals if r["cell"] == "G12"]
    assert len(g12) == 1 and g12[0]["match"] == "no_comment" and g12[0]["amount"] == 1950

    assert not [r for r in rows if r["cell"] in ("H12", "F31")]

    f22 = [r for r in rows if r["cell"] == "F22"]
    assert f22[0]["category"] == "Salary"
    assert f22[0]["section"] == "Inntekter"
    assert f22[0]["match"] == "sum_of_lines"

    budget = [r for r in rows if r["cell"] == "F11"]
    assert budget[0]["row_type"] == "Budsjett" and budget[0]["match"] == "match"


def test_main_writes_review(tmp_path):
    path = tmp_path / "Budget_2013.xlsx"
    _make_hovedark(path)
    out = tmp_path / "review.xlsx"
    assert main([str(path), "-o", str(out)]) == 0

    ws = load_workbook(out).active
    header = [c.value for c in ws[1]]
    assert header[:4] == ["file", "sheet", "year", "month"]
    assert "payee" in header
    data = [dict(zip(header, r)) for r in ws.iter_rows(min_row=2, values_only=True)]
    assert {r["year"] for r in data} == {2013}


def test_year_from_filename(tmp_path):
    assert year_from_filename(tmp_path / "Budsjett og resultat 2013.xlsx") == 2013
    assert year_from_filename(tmp_path / "budget.xlsx") is None
