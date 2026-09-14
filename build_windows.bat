@echo off
setlocal
cd /d "%~dp0"
python -m pip install -r requirements.txt
python -m PyInstaller ^
  --noconfirm ^
  --windowed ^
  --name PlantillaProStudio ^
  --icon "assets\plantillapro_logo.ico" ^
  --add-data "assets;assets" ^
  --add-data "app\qml;app\qml" ^
  --hidden-import PySide6.QtQuick ^
  --hidden-import PySide6.QtQuickControls2 ^
  main.py
echo.
echo EXE generado en dist\PlantillaProStudio\PlantillaProStudio.exe
endlocal
