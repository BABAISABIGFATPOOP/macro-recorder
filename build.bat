@echo off
REM Build a standalone Windows .exe with PyInstaller.
REM Output: dist\MacroRecorder.exe
py -m pip install --quiet pyinstaller pynput pillow
py make_icon.py
py -m PyInstaller --noconfirm --clean ^
  --onefile --windowed --name MacroRecorder ^
  --icon "%~dp0icon.ico" ^
  --add-data "%~dp0icon.ico;." --add-data "%~dp0icon.png;." ^
  "%~dp0macro_recorder.py"
echo.
echo Built dist\MacroRecorder.exe
