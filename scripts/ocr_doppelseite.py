"""OCR einer gescannten Doppelseite: linke und rechte Haelfte untereinander setzen und neu erkennen.

Aufruf: ocr_doppelseite.py ORDNER SEITE [TEILUNG=0.5]
Ueberschreibt pNNNN.txt/.tsv im OCR-Ordner (Original als .orig gesichert).
"""
import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import farzona_review as r  # noqa: E402

ENV = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ.get("PATH", ""))


def main():
    ordner, seite = sys.argv[1], int(sys.argv[2])
    teil = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    datei = next(x["datei"] for x in csv.DictReader(open(r.OUT / "baende.csv", encoding="utf-8")) if x["ordner"] == ordner)
    tmp = r.OUT / "_tmp" / f"dop_{seite}"
    subprocess.run(["pdftoppm", "-f", str(seite), "-l", str(seite), "-r", "600", "-gray", "-png", "-singlefile",
                    str(r.SRC / datei), str(tmp)], env=ENV, check=True)
    im = Image.open(f"{tmp}.png")
    w, h = im.size
    links, rechts = im.crop((0, 0, int(w * teil), h)), im.crop((int(w * teil), 0, w, h))
    neu = Image.new("L", (max(links.width, rechts.width), 2 * h), 255)
    neu.paste(links, (0, 0))
    neu.paste(rechts, (0, h))
    neu.save(f"{tmp}_st.png", dpi=(600, 600))
    ziel = r.OUT / ordner / f"p{seite:04d}"
    for ext in (".txt", ".tsv"):
        if Path(f"{ziel}{ext}").exists() and not Path(f"{ziel}{ext}.orig").exists():
            shutil.copy(f"{ziel}{ext}", f"{ziel}{ext}.orig")
    subprocess.run(["tesseract", f"{tmp}_st.png", str(ziel), "-l", "tgk", "--psm", "4", "txt", "tsv"], env=ENV, check=True,
                   capture_output=True)
    print(Path(f"{ziel}.txt").read_text(encoding="utf-8")[:600])


if __name__ == "__main__":
    main()
