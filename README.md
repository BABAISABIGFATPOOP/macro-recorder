# Macro Recorder

A tiny, TinyTask-style macro recorder for Windows that records **both mouse and
keyboard** and replays them. The overlay is small, borderless, draggable, and
**always stays on top of every other window**.

![overlay](docs/overlay.png)

## Features

- Records mouse movement, clicks, scroll, and every key press/release with timing
- **Toggle mouse recording** off (the **Mouse** checkbox) to capture keyboard-only macros
- **Loop forever** (the **∞ Loop** checkbox) — replays until you hit stop
- Plays back at adjustable **speed** (0.25×–4×) and **repeat** count (1–9999)
- Always-on-top, borderless overlay you can drag anywhere on screen
- **Auto-update** — checks GitHub on startup and installs the newest version by itself
- Save / open macros as `.json` files
- **Customizable global hotkeys** — work even when another app is focused. Defaults:

  | Key | Action |
  |-----|--------|
  | `F9`  | Start / stop recording |
  | `F10` | Play / stop playback |
  | `F11` | Stop everything |
  | `F8`  | Start / stop **loop-forever** playback |

  Click the **⚙** button to rebind any of them: press the key (or a chord like
  `Ctrl + F5`) you want, and it saves automatically. Settings persist in
  `config.json`. Function keys work best — a normal typing key used as a hotkey
  can't also appear inside a recorded macro.

## Download

Grab the latest build from the
[**Releases** page](https://github.com/BABAISABIGFATPOOP/macro-recorder/releases/latest):

- **Windows** — `MacroRecorder-Windows.zip`. Unzip and double-click
  `MacroRecorder.exe`. No Python needed.
- **macOS** — `MacroRecorder-Mac.zip`. Unzip and double-click
  `MacroRecorder.command` (see `README_MAC.txt` inside for the one-time
  permission setup). Requires Python 3.

## Run from source

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
| ⚙ | Settings — rebind hotkeys |

Drag the app by its title bar; close it with the **✕**.

## Auto-update

On startup the app quietly checks this GitHub repo for a newer version (by
comparing its `__version__`). If one exists it **installs it automatically** —
downloads the new `macro_recorder.py`, keeps a `.bak` of the old one, and
restarts itself to apply it. The restart is deferred until the app is idle, so
it never interrupts an active recording or playback.

From the **⚙** Settings panel you can:

- **Check for updates on startup** — turn the automatic check off entirely.
- **Install updates automatically** — turn this off to be *asked first* before
  each update instead of it applying silently.
- **Check for updates now** — trigger a check on demand.

> Publishing a new version is just bumping `__version__` and pushing to `main`.
> Every running copy pulls it on its next launch.

## Notes

- Playback replays the *exact* screen coordinates that were recorded, so keep
  target windows in the same place for reliable results.
- The `F9`/`F10`/`F11` hotkeys are never captured into a macro.
- On some systems you may need to run once as administrator so playback can send
  input to elevated windows.
