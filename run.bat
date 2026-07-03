@echo off
REM Launch the Macro Recorder. Installs pynput on first run if missing.
py -c "import pynput" 2>nul || py -m pip install -r "%~dp0requirements.txt"
py "%~dp0macro_recorder.py"
