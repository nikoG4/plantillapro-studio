from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Bounds:
    left: float
    top: float
    right: float
    bottom: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    @property
    def cx(self) -> float:
        return (self.left + self.right) / 2

    @property
    def cy(self) -> float:
        return (self.top + self.bottom) / 2


def item_bounds(item: object) -> Bounds:
    return Bounds(float(item.x), float(item.y), float(item.x + item.width), float(item.y + item.height))


def selection_bounds(items: Iterable[object]) -> Bounds:
    values = list(items)
    if not values:
        return Bounds(0, 0, 0, 0)
    return Bounds(
        min(item.x for item in values),
        min(item.y for item in values),
        max(item.x + item.width for item in values),
        max(item.y + item.height for item in values),
    )


def align_items(items: Iterable[object], mode: str) -> None:
    values = list(items)
    if len(values) < 2:
        return
    bounds = selection_bounds(values)
    for item in values:
        if mode == "left":
            item.x = round(bounds.left)
        elif mode == "hcenter":
            item.x = round(bounds.cx - item.width / 2)
        elif mode == "right":
            item.x = round(bounds.right - item.width)
        elif mode == "top":
            item.y = round(bounds.top)
        elif mode == "vcenter":
            item.y = round(bounds.cy - item.height / 2)
        elif mode == "bottom":
            item.y = round(bounds.bottom - item.height)


def distribute_items(items: Iterable[object], axis: str) -> None:
    values = list(items)
    if len(values) < 3:
        return
    if axis == "horizontal":
        values.sort(key=lambda item: item.x)
        left = values[0].x
        right = values[-1].x + values[-1].width
        total = sum(item.width for item in values)
        gap = (right - left - total) / (len(values) - 1)
        cursor = float(left)
        for item in values:
            item.x = round(cursor)
            cursor += item.width + gap
    else:
        values.sort(key=lambda item: item.y)
        top = values[0].y
        bottom = values[-1].y + values[-1].height
        total = sum(item.height for item in values)
        gap = (bottom - top - total) / (len(values) - 1)
        cursor = float(top)
        for item in values:
            item.y = round(cursor)
            cursor += item.height + gap


def snap_delta(
    selected: Bounds,
    proposed_dx: float,
    proposed_dy: float,
    canvas_size: tuple[int, int],
    others: Iterable[object],
    tolerance: float = 6.0,
) -> tuple[float, float, list[tuple[str, float]]]:
    moved = Bounds(
        selected.left + proposed_dx,
        selected.top + proposed_dy,
        selected.right + proposed_dx,
        selected.bottom + proposed_dy,
    )
    x_targets = [0.0, canvas_size[0] / 2, float(canvas_size[0])]
    y_targets = [0.0, canvas_size[1] / 2, float(canvas_size[1])]
    for item in others:
        b = item_bounds(item)
        x_targets.extend([b.left, b.cx, b.right])
        y_targets.extend([b.top, b.cy, b.bottom])

    x_sources = [moved.left, moved.cx, moved.right]
    y_sources = [moved.top, moved.cy, moved.bottom]
    dx_adjust, x_guide = _best_adjustment(x_sources, x_targets, tolerance)
    dy_adjust, y_guide = _best_adjustment(y_sources, y_targets, tolerance)
    guides: list[tuple[str, float]] = []
    if x_guide is not None:
        guides.append(("v", x_guide))
    if y_guide is not None:
        guides.append(("h", y_guide))
    return proposed_dx + dx_adjust, proposed_dy + dy_adjust, guides


def _best_adjustment(sources: list[float], targets: list[float], tolerance: float) -> tuple[float, float | None]:
    best: tuple[float, float] | None = None
    for source in sources:
        for target in targets:
            diff = target - source
            if abs(diff) <= tolerance and (best is None or abs(diff) < abs(best[0])):
                best = (diff, target)
    return best if best is not None else (0.0, None)
