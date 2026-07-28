from app.core.models import ExportSettings, FillMode, NumberingSettings, OrderMode, TemplateProject, project_from_dict, project_to_dict

def test_new_settings_round_trip():
    project = TemplateProject(export=ExportSettings(
        fill_mode=FillMode.VERTICAL_ONLY,
        order_mode=OrderMode.CUT_STACK,
        piece_width_mm=65,
        numbering=NumberingSettings(enabled=True, start=1001, count=50, digits=6),
    ))
    restored = project_from_dict(project_to_dict(project))
    assert restored.export.fill_mode == FillMode.VERTICAL_ONLY
    assert restored.export.order_mode == OrderMode.CUT_STACK
    assert restored.export.numbering.start == 1001
    assert restored.export.numbering.digits == 6
