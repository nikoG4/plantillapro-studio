from __future__ import annotations

import json
from pathlib import Path

from .models import TemplateProject, project_from_dict, project_to_dict


def save_project(project: TemplateProject, path: str | Path) -> None:
    Path(path).write_text(json.dumps(project_to_dict(project), indent=2, ensure_ascii=False), encoding="utf-8")


def load_project(path: str | Path) -> TemplateProject:
    return project_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
