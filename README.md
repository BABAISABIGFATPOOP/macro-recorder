# Macro Recorder

A tiny, TinyTask-style macro recorder for Windows that records **both mouse and
keyboard** and replays them. The overlay is small, borderless, draggable, and
**always stays on top of every other window**.

![overlay](docs/overlay.png)

## Features

- Records mouse movement, clicks, scroll, and every key press/release with timing
- Plays back at adjustable **speed** (0.25×–4×) and **repeat** count (1–9999)
- Always-on-top, borderless overlay you can drag anywhere on screen
- Save / open macros as `.json` files
- **Global hotkeys** — work even when another app is focused:

  | Key | Action |
  |-----|--------|
  | `F9`  | Start / stop recording |
  | `F10` | Play / stop playback |
  | `F11` | Stop everything |

## Setup

Requires [Python 3.9+](https://python.org).

```sh
pip install -r requirements.txt
python macro_recorder.py
```

Or just double-click **`run.bat`** — it installs `pynput` on first run and
launches the app.

## Overlay buttons

| Button | Meaning |
|--------|---------|
| ● | Record (turns to ◉ while recording) |
| ▶ | Play (turns to ⏸ while playing) |
| ■ | Stop |
| 🖫 | Save macro to file |
| 🖿 | Open macro from file |

Drag the app by its title bar; close it with the **✕**.

## Notes

- Playback replays the *exact* screen coordinates that were recorded, so keep
  target windows in the same place for reliable results.
- The `F9`/`F10`/`F11` hotkeys are never captured into a macro.
- On some systems you may need to run once as administrator so playback can send
  input to elevated windows.
