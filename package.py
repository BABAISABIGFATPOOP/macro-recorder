"""
Build the release zips:
  release/MacroRecorder-Windows.zip  — the standalone .exe + README
  release/MacroRecorder-Mac.zip      — source + double-click launcher + READMEs

Run `build.bat` first so dist/MacroRecorder.exe exists (Windows zip needs it).
Usage:  py package.py
"""

import os
import stat
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
REL = os.path.join(ROOT, "release")
os.makedirs(REL, exist_ok=True)

# (source path, name inside the zip, make executable?)
WINDOWS = [
    (os.path.join(ROOT, "dist", "MacroRecorder.exe"), "MacroRecorder.exe", False),
    (os.path.join(ROOT, "README.md"), "README.md", False),
]
MAC = [
    (os.path.join(ROOT, "macro_recorder.py"), "macro_recorder.py", False),
    (os.path.join(ROOT, "MacroRecorder.command"), "MacroRecorder.command", True),
    (os.path.join(ROOT, "requirements.txt"), "requirements.txt", False),
    (os.path.join(ROOT, "README.md"), "README.md", False),
    (os.path.join(ROOT, "README_MAC.txt"), "README_MAC.txt", False),
]


def make_zip(zip_name, top_folder, files):
    out = os.path.join(REL, zip_name)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for src, name, executable in files:
            if not os.path.exists(src):
                raise SystemExit(f"missing file: {src}")
            arcname = f"{top_folder}/{name}"
            data = open(src, "rb").read()
            info = zipfile.ZipInfo(arcname)
            info.compress_type = zipfile.ZIP_DEFLATED
            # 0755 for executables (Mac launcher), 0644 otherwise
            perm = 0o755 if executable else 0o644
            info.external_attr = (perm | stat.S_IFREG) << 16
            z.writestr(info, data)
    size = os.path.getsize(out) / 1_000_000
    print(f"  {zip_name}  ({size:.1f} MB)")


print("Writing zips to release/ ...")
make_zip("MacroRecorder-Windows.zip", "MacroRecorder", WINDOWS)
make_zip("MacroRecorder-Mac.zip", "MacroRecorder", MAC)
print("Done.")
