"""
Generate the app icon: a red 'record' dot with a mouse cursor on the app's dark
rounded-square theme. Produces icon.png (window) and icon.ico (exe, multi-size).

Usage:  py make_icon.py
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
S = 256                      # master size; rendered 4x then downsampled for smooth edges
SS = S * 4


def rounded(draw, box, radius, **kw):
    draw.rounded_rectangle(box, radius=radius, **kw)


def render():
    img = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # dark rounded background + subtle border (matches the overlay theme)
    pad = int(SS * 0.06)
    rounded(d, [pad, pad, SS - pad, SS - pad], radius=int(SS * 0.22),
            fill=(30, 30, 30, 255), outline=(70, 70, 70, 255), width=int(SS * 0.012))

    # big red record dot, slightly up-left of centre
    cx, cy, r = int(SS * 0.44), int(SS * 0.42), int(SS * 0.26)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 70, 70, 255))
    # darker ring for depth
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(150, 30, 30, 255),
              width=int(SS * 0.016))
    # small highlight
    hr = int(r * 0.34)
    d.ellipse([cx - r + int(r*0.28), cy - r + int(r*0.28),
               cx - r + int(r*0.28) + hr, cy - r + int(r*0.28) + hr],
              fill=(255, 150, 150, 180))

    # mouse cursor arrow, lower-right, pointing up-left
    ox, oy = int(SS * 0.52), int(SS * 0.5)
    sc = SS * 0.0016
    pts = [(0, 0), (0, 168), (46, 126), (78, 196), (110, 182),
           (78, 116), (140, 116)]
    poly = [(ox + x * sc, oy + y * sc) for x, y in pts]
    d.polygon(poly, fill=(245, 245, 245, 255))
    # outline the cursor so it stays crisp on the red
    d.line(poly + [poly[0]], fill=(20, 20, 20, 255), width=int(SS * 0.014),
           joint="curve")

    return img.resize((S, S), Image.LANCZOS)


def main():
    icon = render()
    png = os.path.join(ROOT, "icon.png")
    ico = os.path.join(ROOT, "icon.ico")
    icon.save(png)
    icon.save(ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                          (64, 64), (128, 128), (256, 256)])
    print("wrote", png, "and", ico)


if __name__ == "__main__":
    main()
