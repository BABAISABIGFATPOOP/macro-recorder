#!/bin/bash
# Double-click launcher for macOS.
# Runs the Macro Recorder using your system Python 3, installing pynput if needed.
cd "$(dirname "$0")" || exit 1

# Find a Python 3 interpreter
PY="$(command -v python3 || command -v python)"
if [ -z "$PY" ]; then
  osascript -e 'display alert "Python 3 not found" message "Please install Python 3 from python.org, then double-click this again."'
  open "https://www.python.org/downloads/"
  exit 1
fi

# Install pynput if it is missing
"$PY" -c "import pynput" 2>/dev/null || "$PY" -m pip install --user pynput

exec "$PY" macro_recorder.py
