@echo off
REM Build a standalone Windows .exe with PyInstaller.
REM Output: dist\MacroRecorder.exe
py -m pip install --quiet pyinstaller pynput
py -m PyInstaller --noconfirm --clean ^
  --onefile --windowed --name MacroRecorder ^
  "%~dp0macro_recorder.py"
echo.
echo Built dist\MacroRecorder.exe
