from __future__ import annotations
from PIL import Image
from app.core.models import FieldStyle, TextField
from app.core.pdf_exporter import export_pdf
from app.core.renderer import _layout_text, load_font, render_template, render_text_template

def test_replace_variables():
    assert render_text_template("Alumno/a: {{nombre}}", {"nombre": "Ana"}) == "Alumno/a: Ana"

def test_render_image_without_crashing(tmp_path):
    image_path = tmp_path / "base.png"
    Image.new("RGB", (600, 400), "white").save(image_path)
    field = TextField(id="1", x=50, y=250, width=500, height=100, style=FieldStyle(font_size=72, auto_fit=True, min_font_size=10))
    assert render_template(image_path, [field], {"nombre": "Nombre de prueba bastante largo"}).size == (600, 400)

def test_text_case_lower_and_title_render_without_crashing(tmp_path):
    image_path = tmp_path / "base.png"
    Image.new("RGB", (400, 200), "white").save(image_path)
    lower = TextField(id="1", x=10, y=20, width=180, height=80, style=FieldStyle(text_case="lower"))
    title = TextField(id="2", x=200, y=20, width=180, height=80, style=FieldStyle(text_case="title"))
    assert render_template(image_path, [lower, title], {"nombre": "ANA MARIA"}).size == (400, 200)

def test_words_per_line_splits_fixed_word_groups():
    style = FieldStyle(words_per_line=2)
    assert _layout_text("JUAN CARLOS PEREZ GOMEZ", load_font(style, 24), 400, style) == ["JUAN CARLOS", "PEREZ GOMEZ"]

def test_export_pdf_with_three_pages(tmp_path):
    from app.core.models import ExportSettings
    image_path = tmp_path / "base.png"; output = tmp_path / "salida.pdf"
    Image.new("RGB", (300, 200), "white").save(image_path)
    field = TextField(id="1", x=20, y=80, width=260, height=60, style=FieldStyle(font_size=36))
    count = export_pdf(image_path, [field], [{"nombre": "Ana"}, {"nombre": "Luis"}, {"nombre": "Mia"}], ExportSettings(dpi=300), output)
    assert count == 3 and output.exists() and output.stat().st_size > 0
