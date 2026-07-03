"""
Macro Recorder — a tiny TinyTask-style mouse + keyboard macro recorder.

- Records mouse movement, clicks, scrolls and every key press/release with timing.
- Mouse recording can be toggled off to capture keyboard-only macros.
- Plays them back at adjustable speed and repeat count.
- Small, borderless, always-on-top overlay you can drag anywhere.
- Customizable global hotkeys (defaults below) so you can control it even
  when another window is focused:
      F9  = start / stop recording
      F10 = play / stop playback
      F11 = stop everything
- Save / open macros as .json files.  Settings persist in config.json.

Requires: pynput  (pip install pynput)
"""

import json
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

from pynput import mouse, keyboard


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "record_mouse": True,
    "hotkeys": {
        "toggle_record": "<f9>",
        "toggle_play": "<f10>",
        "stop_all": "<f11>",
    },
}

ACTIONS = [
    ("toggle_record", "Record"),
    ("toggle_play", "Play"),
    ("stop_all", "Stop"),
]

MODIFIER_NAMES = {
    "ctrl_l": "ctrl", "ctrl_r": "ctrl",
    "alt_l": "alt", "alt_r": "alt", "alt_gr": "alt",
    "shift_l": "shift", "shift_r": "shift",
    "cmd_l": "cmd", "cmd_r": "cmd",
}


# ---------------------------------------------------------------------------
# Key (de)serialization so events can be saved to / loaded from JSON
# ---------------------------------------------------------------------------
def key_to_obj(key):
    """Convert a pynput key into a JSON-serializable dict."""
    if isinstance(key, keyboard.Key):
        return {"special": key.name}
    # KeyCode: has .char and/or .vk
    return {"char": key.char, "vk": key.vk}


def obj_to_key(obj):
    """Rebuild a pynput key from a saved dict."""
    if "special" in obj:
        return getattr(keyboard.Key, obj["special"])
    if obj.get("char") is not None:
        return keyboard.KeyCode.from_char(obj["char"])
    return keyboard.KeyCode.from_vk(obj["vk"])


def single_key_str(key):
    """A hotkey-style string for one key, e.g. Key.f9 -> '<f9>', 'a' -> 'a'."""
    if isinstance(key, keyboard.Key):
        return f"<{key.name}>"
    if key.char is not None:
        return key.char.lower()
    return f"<{key.vk}>"


def final_key_of(hotkey_str):
    """The last (trigger) key of a hotkey chord, e.g. '<ctrl>+<f5>' -> '<f5>'."""
    return hotkey_str.split("+")[-1]


def pretty_hotkey(hotkey_str):
    """Human-friendly hotkey label, e.g. '<ctrl>+<f5>' -> 'Ctrl + F5'."""
    parts = []
    for p in hotkey_str.split("+"):
        p = p.strip("<>")
        parts.append(p.upper() if len(p) <= 3 else p.capitalize())
    return " + ".join(parts)


class MacroRecorder:
    def __init__(self):
        # --- config ---
        self.config = self._load_config()

        # --- state ---
        self.events = []            # recorded events
        self.recording = False
        self.playing = False
        self._record_start = 0.0
        self._last_time = 0.0
        self._stop_playback = threading.Event()
        self._queue = queue.Queue()  # cross-thread messages -> main/UI thread
        self._filter_keys = set()    # trigger-key strings to never record

        self._mouse_listener = None
        self._kbd_listener = None
        self._mouse_ctl = mouse.Controller()
        self._kbd_ctl = keyboard.Controller()
        self._hotkeys = None
        self._settings_win = None

        # --- UI ---
        self._build_ui()

        # --- global hotkeys (always running) ---
        self._apply_hotkeys()

        self.root.after(30, self._pump)

    # ------------------------------------------------------------- config io
    def _load_config(self):
        cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy of defaults
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg["record_mouse"] = saved.get("record_mouse", cfg["record_mouse"])
            cfg["hotkeys"].update(saved.get("hotkeys", {}))
        except (OSError, ValueError):
            pass
        return cfg

    def _save_config(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except OSError:
            pass

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.root = tk.Tk()
        self.root.title("Macro Recorder")
        self.root.overrideredirect(True)      # borderless, TinyTask-like
        self.root.attributes("-topmost", True)  # always above everything
        self.root.configure(bg="#1e1e1e")
        self.root.geometry("+120+120")

        bar = tk.Frame(self.root, bg="#1e1e1e", bd=1, relief="solid",
                       highlightbackground="#444", highlightthickness=1)
        bar.pack()

        # title / drag handle
        title = tk.Frame(bar, bg="#2b2b2b")
        title.pack(fill="x")
        handle = tk.Label(title, text="⠿ Macro Recorder", bg="#2b2b2b",
                          fg="#bbbbbb", font=("Segoe UI", 8, "bold"), padx=6)
        handle.pack(side="left")
        close = tk.Label(title, text="✕", bg="#2b2b2b", fg="#bbbbbb",
                         font=("Segoe UI", 9, "bold"), padx=6, cursor="hand2")
        close.pack(side="right")
        close.bind("<Button-1>", lambda e: self.quit())
        for w in (title, handle):
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)

        # buttons row
        row = tk.Frame(bar, bg="#1e1e1e")
        row.pack(padx=4, pady=(4, 2))

        def mk(txt, cmd, fg="#e0e0e0"):
            b = tk.Button(row, text=txt, command=cmd, width=3, fg=fg,
                          bg="#333", activebackground="#444",
                          activeforeground=fg, relief="flat",
                          font=("Segoe UI Symbol", 11), bd=0)
            b.pack(side="left", padx=2)
            return b

        self.btn_rec = mk("●", lambda: self._queue.put(("cmd", "toggle_record")), "#ff5555")
        self.btn_play = mk("▶", lambda: self._queue.put(("cmd", "toggle_play")), "#55cc66")
        self.btn_stop = mk("■", lambda: self._queue.put(("cmd", "stop_all")))
        mk("🖫", self.save)          # save
        mk("🖿", self.open)          # open
        mk("⚙", self.open_settings)  # settings / hotkeys

        # options row
        opt = tk.Frame(bar, bg="#1e1e1e")
        opt.pack(padx=4, pady=(0, 2))

        self.record_mouse_var = tk.BooleanVar(value=self.config["record_mouse"])
        tk.Checkbutton(opt, text="Mouse", variable=self.record_mouse_var,
                       command=self._on_mouse_toggle, bg="#1e1e1e", fg="#ccc",
                       selectcolor="#333", activebackground="#1e1e1e",
                       activeforeground="#fff", font=("Segoe UI", 8),
                       bd=0, highlightthickness=0).pack(side="left", padx=(0, 8))

        tk.Label(opt, text="Repeat", bg="#1e1e1e", fg="#999",
                 font=("Segoe UI", 8)).pack(side="left")
        self.repeat_var = tk.StringVar(value="1")
        tk.Spinbox(opt, from_=1, to=9999, width=4, textvariable=self.repeat_var,
                   font=("Segoe UI", 8)).pack(side="left", padx=(2, 8))
        tk.Label(opt, text="Speed", bg="#1e1e1e", fg="#999",
                 font=("Segoe UI", 8)).pack(side="left")
        self.speed_var = tk.StringVar(value="1.0")
        tk.Spinbox(opt, values=("0.25", "0.5", "1.0", "2.0", "4.0"), width=4,
                   textvariable=self.speed_var, font=("Segoe UI", 8)).pack(side="left", padx=2)

        # status bar
        self.status = tk.StringVar()
        tk.Label(bar, textvariable=self.status, bg="#1e1e1e", fg="#888",
                 font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=6, pady=(0, 4))
        self._set_ready_status()

        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def _set_ready_status(self):
        hk = self.config["hotkeys"]
        self.status.set(
            f"Ready · {pretty_hotkey(hk['toggle_record'])} rec · "
            f"{pretty_hotkey(hk['toggle_play'])} play · "
            f"{pretty_hotkey(hk['stop_all'])} stop")

    # ------------------------------------------------------------- dragging
    def _start_drag(self, e):
        self._dx, self._dy = e.x, e.y

    def _on_drag(self, e):
        x = self.root.winfo_pointerx() - self._dx
        y = self.root.winfo_pointery() - self._dy
        self.root.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------ hotkeys
    def _apply_hotkeys(self):
        """(Re)start the global hotkey listener from the current config."""
        if self._hotkeys is not None:
            try:
                self._hotkeys.stop()
            except Exception:
                pass
        mapping = {}
        for action, hk in self.config["hotkeys"].items():
            mapping[hk] = (lambda a=action: self._queue.put(("cmd", a)))
        self._hotkeys = keyboard.GlobalHotKeys(mapping)
        self._hotkeys.start()
        # keys we must never record into a macro (the hotkey triggers)
        self._filter_keys = {final_key_of(hk) for hk in self.config["hotkeys"].values()}

    def _on_mouse_toggle(self):
        self.config["record_mouse"] = self.record_mouse_var.get()
        self._save_config()

    # ------------------------------------------------------- main-thread pump
    def _pump(self):
        """Process cross-thread messages on the Tk main thread."""
        try:
            while True:
                kind, val = self._queue.get_nowait()
                if kind == "cmd":
                    getattr(self, val)()
                elif kind == "status":
                    self.status.set(val)
        except queue.Empty:
            pass
        self.root.after(30, self._pump)

    def _set_status(self, text):
        self._queue.put(("status", text))

    # --------------------------------------------------------------- record
    def toggle_record(self):
        if self.recording:
            self.stop_all()
        else:
            self.start_record()

    def start_record(self):
        if self.playing:
            return
        self.events = []
        self.recording = True
        self._record_start = time.perf_counter()
        self._last_time = self._record_start
        self.btn_rec.config(text="◉")
        mode = "mouse + keyboard" if self.config["record_mouse"] else "keyboard only"
        self._set_status(f"● Recording ({mode})…")

        if self.config["record_mouse"]:
            self._mouse_listener = mouse.Listener(
                on_move=self._on_move, on_click=self._on_click, on_scroll=self._on_scroll)
            self._mouse_listener.start()
        self._kbd_listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release)
        self._kbd_listener.start()

    def _delay(self):
        now = time.perf_counter()
        d = now - self._last_time
        self._last_time = now
        return d

    def _is_hotkey(self, key):
        return single_key_str(key) in self._filter_keys

    def _on_move(self, x, y):
        if self.recording:
            self.events.append(["move", self._delay(), x, y])

    def _on_click(self, x, y, button, pressed):
        if self.recording:
            self.events.append(["click", self._delay(), x, y, button.name, pressed])

    def _on_scroll(self, x, y, dx, dy):
        if self.recording:
            self.events.append(["scroll", self._delay(), x, y, dx, dy])

    def _on_press(self, key):
        if self.recording and not self._is_hotkey(key):
            self.events.append(["kpress", self._delay(), key_to_obj(key)])

    def _on_release(self, key):
        if self.recording and not self._is_hotkey(key):
            self.events.append(["krelease", self._delay(), key_to_obj(key)])

    def _stop_recording(self):
        self.recording = False
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._kbd_listener:
            self._kbd_listener.stop()
            self._kbd_listener = None
        self.btn_rec.config(text="●")

    # ----------------------------------------------------------------- play
    def toggle_play(self):
        if self.playing:
            self.stop_all()
        else:
            self.start_play()

    def start_play(self):
        if self.recording or self.playing:
            return
        if not self.events:
            self._set_status("Nothing recorded yet.")
            return
        try:
            repeat = max(1, int(self.repeat_var.get()))
        except ValueError:
            repeat = 1
        try:
            speed = max(0.05, float(self.speed_var.get()))
        except ValueError:
            speed = 1.0

        self.playing = True
        self._stop_playback.clear()
        self.btn_play.config(text="⏸")
        self._set_status(f"▶ Playing ×{repeat} @ {speed}×")
        threading.Thread(target=self._play_worker, args=(repeat, speed),
                         daemon=True).start()

    def _play_worker(self, repeat, speed):
        try:
            for i in range(repeat):
                if self._stop_playback.is_set():
                    break
                for ev in self.events:
                    if self._stop_playback.is_set():
                        break
                    kind, delay = ev[0], ev[1]
                    if delay > 0:
                        # wait in small slices so Stop is responsive
                        remaining = delay / speed
                        while remaining > 0 and not self._stop_playback.is_set():
                            chunk = min(0.02, remaining)
                            time.sleep(chunk)
                            remaining -= chunk
                    self._replay(kind, ev)
        finally:
            self._queue.put(("cmd", "_playback_done"))

    def _replay(self, kind, ev):
        try:
            if kind == "move":
                self._mouse_ctl.position = (ev[2], ev[3])
            elif kind == "click":
                _, _, x, y, btn, pressed = ev
                self._mouse_ctl.position = (x, y)
                b = getattr(mouse.Button, btn)
                if pressed:
                    self._mouse_ctl.press(b)
                else:
                    self._mouse_ctl.release(b)
            elif kind == "scroll":
                _, _, x, y, dx, dy = ev
                self._mouse_ctl.position = (x, y)
                self._mouse_ctl.scroll(dx, dy)
            elif kind == "kpress":
                self._kbd_ctl.press(obj_to_key(ev[2]))
            elif kind == "krelease":
                self._kbd_ctl.release(obj_to_key(ev[2]))
        except Exception:
            pass  # ignore a single bad event, keep playing

    def _playback_done(self):
        self.playing = False
        self.btn_play.config(text="▶")
        self._set_ready_status()

    # ----------------------------------------------------------------- stop
    def stop_all(self):
        if self.recording:
            self._stop_recording()
            self._set_status(f"Stopped · {len(self.events)} events recorded")
        if self.playing:
            self._stop_playback.set()

    # ------------------------------------------------------------ save/open
    def save(self):
        if not self.events:
            messagebox.showinfo("Macro Recorder", "Nothing to save yet.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("Macro", "*.json")],
            title="Save macro")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.events, f)
            self._set_status(f"Saved {len(self.events)} events")

    def open(self):
        path = filedialog.askopenfilename(
            filetypes=[("Macro", "*.json")], title="Open macro")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.events = json.load(f)
            self._set_status(f"Loaded {len(self.events)} events")

    # --------------------------------------------------------- settings win
    def open_settings(self):
        if self._settings_win is not None and tk.Toplevel.winfo_exists(self._settings_win):
            self._settings_win.lift()
            return

        win = tk.Toplevel(self.root)
        self._settings_win = win
        win.title("Settings")
        win.attributes("-topmost", True)
        win.configure(bg="#1e1e1e")
        win.resizable(False, False)

        tk.Label(win, text="Global hotkeys", bg="#1e1e1e", fg="#ddd",
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=2,
                                                     padx=12, pady=(12, 2), sticky="w")
        tk.Label(win, text="Click a button, then press the key(s) you want.",
                 bg="#1e1e1e", fg="#888", font=("Segoe UI", 8)).grid(
                     row=1, column=0, columnspan=2, padx=12, sticky="w")

        self._hk_buttons = {}
        for i, (action, label) in enumerate(ACTIONS):
            tk.Label(win, text=label, bg="#1e1e1e", fg="#ccc",
                     font=("Segoe UI", 9)).grid(row=2 + i, column=0, padx=(12, 6),
                                                pady=4, sticky="w")
            b = tk.Button(win, text=pretty_hotkey(self.config["hotkeys"][action]),
                          width=16, bg="#333", fg="#e0e0e0", relief="flat",
                          activebackground="#444", activeforeground="#fff",
                          font=("Segoe UI", 9),
                          command=lambda a=action: self._capture_hotkey(a))
            b.grid(row=2 + i, column=1, padx=(0, 12), pady=4)
            self._hk_buttons[action] = b

        tk.Button(win, text="Reset to defaults", bg="#2b2b2b", fg="#bbb",
                  relief="flat", activebackground="#3a3a3a", font=("Segoe UI", 8),
                  command=self._reset_hotkeys).grid(
                      row=2 + len(ACTIONS), column=0, columnspan=2, pady=(6, 12))

        win.protocol("WM_DELETE_WINDOW", self._close_settings)

    def _close_settings(self):
        if self._settings_win is not None:
            self._settings_win.destroy()
            self._settings_win = None

    def _capture_hotkey(self, action):
        """Listen for the next key chord and assign it to `action`."""
        btn = self._hk_buttons[action]
        btn.config(text="press keys…  (Esc = cancel)", bg="#4a3a00")
        held = set()

        def finish(new_hotkey):
            listener.stop()
            if new_hotkey is not None:
                self.config["hotkeys"][action] = new_hotkey
                self._save_config()
                self.root.after(0, self._apply_hotkeys)
                self.root.after(0, self._set_ready_status)
            self.root.after(0, lambda: btn.config(
                text=pretty_hotkey(self.config["hotkeys"][action]), bg="#333"))

        def on_press(key):
            name = getattr(key, "name", None)
            if name == "esc":
                finish(None)
                return False
            if name in MODIFIER_NAMES:
                held.add(MODIFIER_NAMES[name])
                return  # wait for the non-modifier trigger key
            mods = [m for m in ("ctrl", "alt", "shift", "cmd") if m in held]
            chord = "+".join([f"<{m}>" for m in mods] + [single_key_str(key)])
            finish(chord)
            return False

        def on_release(key):
            name = getattr(key, "name", None)
            if name in MODIFIER_NAMES:
                held.discard(MODIFIER_NAMES[name])

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()

    def _reset_hotkeys(self):
        self.config["hotkeys"] = json.loads(json.dumps(DEFAULT_CONFIG["hotkeys"]))
        self._save_config()
        self._apply_hotkeys()
        self._set_ready_status()
        for action, b in self._hk_buttons.items():
            b.config(text=pretty_hotkey(self.config["hotkeys"][action]))

    # ----------------------------------------------------------------- quit
    def quit(self):
        self._stop_playback.set()
        self.recording = False
        try:
            self._hotkeys.stop()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    MacroRecorder().run()
