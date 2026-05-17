from __future__ import annotations

from app.core.filename_utils import sanitize_filename


def test_sanitize_windows_filename():
    assert sanitize_filename('CON<>:"/\\|?* .') == "CON_"
    assert sanitize_filename("  Alumno  Uno  ") == "Alumno Uno"
    assert sanitize_filename("") == "archivo"

