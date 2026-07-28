from __future__ import annotations
from PIL import Image
from app.core.imposition import apply_numbering, build_imposed_pages, compute_layout, paginate_rows, render_imposed_page
from app.core.models import ExportSettings, FillMode, NumberingSettings, OrderMode, PageSize


def test_numbering_generates_rows_without_input():
    settings = NumberingSettings(enabled=True, start=7, count=3, step=2, digits=4)
    assert [row["numero"] for row in apply_numbering([], settings)] == ["0007", "0009", "0011"]


def test_grid_layout_is_calculated_from_physical_piece_size():
    settings = ExportSettings(
        dpi=100, page_size=PageSize.CUSTOM, custom_width_px=1000, custom_height_px=1200,
        use_original_piece_size=False, piece_width_mm=50.8, piece_height_mm=63.5,
        margin_left_mm=12.7, margin_top_mm=12.7, margin_right_mm=12.7, margin_bottom_mm=12.7,
        gap_x_mm=2.54, gap_y_mm=2.54, fill_mode=FillMode.GRID,
    )
    layout = compute_layout(settings, (200, 250))
    assert (layout.columns, layout.rows, layout.slots_per_page) == (4, 4, 16)


def test_vertical_only_uses_one_column():
    settings = ExportSettings(
        dpi=100, page_size=PageSize.CUSTOM, custom_width_px=800, custom_height_px=1000,
        use_original_piece_size=False, piece_width_mm=50.8, piece_height_mm=45.72,
        gap_y_mm=5.08, fill_mode=FillMode.VERTICAL_ONLY,
        margin_left_mm=0, margin_top_mm=0, margin_right_mm=0, margin_bottom_mm=0,
    )
    layout = compute_layout(settings, (200, 180))
    assert layout.columns == 1
    assert layout.rows == 5


def test_cut_stack_places_top_position_in_sequence_across_pages():
    rows = [{"numero": str(i)} for i in range(1, 11)]
    pages = paginate_rows(rows, slots_per_page=5, order_mode=OrderMode.CUT_STACK)
    assert [[item["numero"] if item else None for item in page] for page in pages] == [
        ["1", "3", "5", "7", "9"], ["2", "4", "6", "8", "10"],
    ]
    assert [page[0]["numero"] for page in pages] == ["1", "2"]


def test_render_imposed_page(tmp_path):
    image_path = tmp_path / "base.png"
    Image.new("RGB", (200, 100), "white").save(image_path)
    settings = ExportSettings(
        dpi=100, page_size=PageSize.CUSTOM, custom_width_px=500, custom_height_px=350,
        use_original_piece_size=True, margin_left_mm=0, margin_top_mm=0,
        margin_right_mm=0, margin_bottom_mm=0, gap_x_mm=2.54, gap_y_mm=2.54,
        fill_mode=FillMode.GRID, order_mode=OrderMode.CUT_STACK,
        numbering=NumberingSettings(enabled=True, start=1, count=6),
    )
    layout, pages, prepared = build_imposed_pages(image_path, [], settings)
    assert layout.slots_per_page == 6
    assert len(prepared) == 6 and len(pages) == 1
    image = render_imposed_page(image_path, [], layout, pages[0])
    assert image.size == (500, 350)
