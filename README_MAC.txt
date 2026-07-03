Macro Recorder — macOS
======================

This is the source version for Mac. It runs with your system Python 3
(a native .app isn't provided yet). Setup takes about a minute.

1. INSTALL PYTHON 3 (if you don't have it)
   Get it from https://www.python.org/downloads/ and install.

2. RUN THE APP
   Double-click "MacroRecorder.command".
   - The first time, macOS may block it: right-click the file -> Open ->
     Open, to confirm you trust it.
   - It installs the one dependency (pynput) automatically, then launches.

3. GRANT PERMISSIONS (required — macOS blocks input control by default)
   Open  System Settings -> Privacy & Security, and add/enable Terminal
   (or whatever app you launched it from) under BOTH:
     * Accessibility        -> needed to move the mouse / press keys on playback
     * Input Monitoring     -> needed to record your mouse & keyboard
   Quit and relaunch the app after granting these.

USAGE
   Same as Windows: F9 record, F10 play, F11 stop, F8 loop-forever.
   Rebind any of them with the gear (settings) button. See README.md for details.

NOTE
   Auto-update works in this source version (it refreshes macro_recorder.py).
   If you prefer a real double-click .app, that can be produced later with a
   macOS build — ask and it can be added.
