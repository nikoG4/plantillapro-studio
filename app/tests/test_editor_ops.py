from __future__ import annotations

from app.core.editor_ops import Bounds, align_items, distribute_items, snap_delta
from app.core.models import ShapeElement


def shape(id_: str, x: int, y: int, w: int = 100, h: int = 60) -> ShapeElement:
    return ShapeElement(id=id_, x=x, y=y, width=w, height=h)


def test_align_selected_edges_and_centers() -> None:
    items = [shape("a", 10, 20, 100, 40), shape("b", 80, 90, 40, 80)]
    align_items(items, "left")
    assert [item.x for item in items] == [10, 10]
    items[0].x, items[1].x = 10, 80
    align_items(items, "hcenter")
    assert items[0].x + items[0].width / 2 == items[1].x + items[1].width / 2
    align_items(items, "bottom")
    assert items[0].y + items[0].height == items[1].y + items[1].height


def test_distribute_horizontal_equal_gaps() -> None:
    items = [shape("a", 0, 0, 50, 20), shape("b", 100, 0, 50, 20), shape("c", 250, 0, 50, 20)]
    distribute_items(items, "horizontal")
    gap1 = items[1].x - (items[0].x + items[0].width)
    gap2 = items[2].x - (items[1].x + items[1].width)
    assert gap1 == gap2


def test_snap_delta_to_canvas_center_and_other_object() -> None:
    selected = Bounds(10, 20, 110, 80)
    dx, dy, guides = snap_delta(selected, 139, 0, (500, 400), [], tolerance=6)
    assert dx == 140
    assert ("v", 250.0) in guides

    other = shape("target", 300, 150, 100, 80)
    dx, dy, guides = snap_delta(selected, 188, 128, (500, 400), [other], tolerance=6)
    assert ("v", 300.0) in guides
    assert ("h", 150.0) in guides
