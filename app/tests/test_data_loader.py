from __future__ import annotations

from openpyxl import Workbook

from app.core.data_loader import load_csv, load_txt, load_xlsx, rows_from_pasted_text


def test_load_txt_names(tmp_path):
    path = tmp_path / "nombres.txt"
    path.write_text("Ana\n\nLuis\n", encoding="utf-8")
    assert load_txt(path) == [{"nombre": "Ana"}, {"nombre": "Luis"}]


def test_load_csv_with_headers(tmp_path):
    path = tmp_path / "datos.csv"
    path.write_text("nombre,curso\nAna,1A\nLuis,2B\n", encoding="utf-8")
    rows = load_csv(path)
    assert rows[0]["nombre"] == "Ana"
    assert rows[1]["curso"] == "2B"


def test_load_xlsx(tmp_path):
    path = tmp_path / "datos.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["nombre", "curso"])
    ws.append(["Ana", "1A"])
    wb.save(path)
    rows = load_xlsx(path)
    assert rows == [{"nombre": "Ana", "curso": "1A"}]


def test_pasted_plain_names_create_nombre_column():
    rows = rows_from_pasted_text("AGUILAR BENITEZ, GISSELLY FIORELLA\nALFONZO CORRALES, LUCAS BENJAMIN")
    assert list(rows[0].keys()) == ["nombre"]
    assert rows[0]["nombre"].startswith("AGUILAR")

