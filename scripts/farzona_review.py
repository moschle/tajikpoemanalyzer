#!/usr/bin/python3
"""Pruefblaetter: je 12 Seiten (6x2) mit Seitennummer + Kurzbericht der Zerlegung je Seite.
Aufruf: farzona_review.py ORDNER VON BIS     -> _tmp/stich/rv_<kurz>_<von>.png + rv_<kurz>_<von>.txt
Kurzbericht je Seite:  S.83 (25): F7 | N«Шабест рӯшан» 18 | T«ФАТВОИ ТАҶДИД»«Дар дилам» 40  [Ü = Uebersetzung]
  F = Fortsetzung vom Vorgaenger (Zeilen auf dieser Seite), N = neues Gedicht, T = neues Gedicht mit Titel."""
import csv, json, os, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
SRC = Path.home() / "Documents/Akademisch/MA/vergleichsgruppe/Farzona Tadschikistan"
OUT = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona"
ST = OUT / "_tmp/stich"; ST.mkdir(parents=True, exist_ok=True)
ENV = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ.get("PATH", ""))
W, H = 255, 385

def words(t, n=3):
    return " ".join(t.split()[:n])[:28]

def main():
    ordner = sys.argv[1]
    if sys.argv[2] == "liste":                      # farzona_review.py ORDNER liste 14,15,17
        alle = [int(x) for x in sys.argv[3].split(",")]
        von, bis = 0, len(alle) - 1
    else:
        von, bis = int(sys.argv[2]), int(sys.argv[3])
        alle = None
    datei = next(r["datei"] for r in csv.DictReader(open(OUT / "baende.csv", encoding="utf-8")) if r["ordner"] == ordner)
    poems = [json.loads(l) for l in open(OUT / "gedichte" / f"{ordner}.jsonl", encoding="utf-8")]
    kurz = ordner.replace("ФАРЗОНАИ_", "").replace("ФАРЗОНА_", "")[:6]
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 22)
    except Exception:
        font = None
    for s in range(von, bis + 1, 12):
        pages = alle[s:s + 12] if alle else list(range(s, min(s + 12, bis + 1)))
        sheet = Image.new("L", (W * 6 + 25, H * 2 + 10), 255)
        d = ImageDraw.Draw(sheet)
        rep = []
        for k, p in enumerate(pages):
            subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-scale-to-y", str(H), "-scale-to-x", "-1", "-gray",
                            "-png", "-singlefile", str(SRC / datei), str(ST / f"tile{os.getpid()}")], env=ENV, check=True)
            im = Image.open(ST / f"tile{os.getpid()}.png")
            im.thumbnail((W - 5, H))
            x, y = (k % 6) * (W + 5), (k // 6) * (H + 10)
            sheet.paste(im, (x, y))
            d.rectangle((x, y, x + 52, y + 26), fill=0)
            d.text((x + 4, y + 1), str(p), fill=255, font=font)
            teile, total = [], 0
            for pm in poems:
                idx = [i for i, lp in enumerate(pm["lpages"]) if lp == p and pm["lines"][i]]
                if not idx:
                    continue
                total += len(idx)
                u = "Ü" if pm.get("uebersetzung") else ""
                if pm["page"] < p or (pm["lpages"] and min(lp for lp, l in zip(pm["lpages"], pm["lines"]) if l) < p):
                    teile.append(f"F{len(idx)}")
                elif pm["title"]:
                    teile.append(f"{u}T«{words(pm['title'], 4)}»«{words(pm['lines'][idx[0]])}» {len(idx)}")
                else:
                    teile.append(f"{u}N«{words(pm['lines'][idx[0]])}» {len(idx)}")
            rep.append(f"S.{p} ({total}): " + (" | ".join(teile) if teile else "—"))
        name = f"rv_{kurz}_{'L' if alle else ''}{s:03d}"
        sheet.save(ST / f"{name}.png")
        (ST / f"{name}.txt").write_text("\n".join(rep), encoding="utf-8")
        print(name)

if __name__ == "__main__":
    main()
