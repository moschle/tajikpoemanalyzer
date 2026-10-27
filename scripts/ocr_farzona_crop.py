#!/usr/bin/python3
"""Zweiter OCR-Lauf fuer Baende mit Zierrahmen: Seite rendern, Rahmen abschneiden, neu erkennen.
Aufruf: ocr_farzona_crop.py [--test SEITE] [--pages-below KONF]
Ueberschreibt pNNNN.txt/.tsv nur, wenn die neue Konfidenz hoeher ist."""
import csv, os, subprocess, sys, tempfile, shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

SRC = Path.home() / "Documents/Akademisch/MA/vergleichsgruppe/Farzona Tadschikistan"
OUT = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona"
# Rand in Prozent: links, oben, rechts, unten
CROP = {
    "ФАРЗОНА_НАЙСОН": (0.16, 0.11, 0.15, 0.16),
    "ФАРЗОНА_МӮҲРИ_ГУЛИ_МИНО": (0.13, 0.06, 0.11, 0.09),   # 27.10.: Rahmenreste links bei 0.10
}
ENV = dict(os.environ, PATH="/opt/homebrew/bin:/usr/local/bin:" + os.environ.get("PATH", ""), OMP_THREAD_LIMIT="1")

def conf(tsv):
    vals = []
    with open(tsv, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            try:
                c = float(row["conf"])
            except (KeyError, ValueError, TypeError):
                continue
            if c >= 0 and (row.get("text") or "").strip():
                vals.append(c)
    return (sum(vals) / len(vals) if vals else 0.0), len(vals)

def run(job):
    pdf, ordner, p, test = job
    tmp = Path(tempfile.mkdtemp(dir=OUT / "_tmp"))
    try:
        subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", "300", "-gray", "-png", str(pdf), "pg"],
                       cwd=tmp, env=ENV, check=True, capture_output=True)
        png = next(tmp.glob("pg*.png"))
        im = Image.open(png)
        w, h = im.size
        l, t, r, b = CROP[ordner]
        im.crop((int(w * l), int(h * t), int(w * (1 - r)), int(h * (1 - b)))).save(tmp / "c.png")
        subprocess.run(["tesseract", "c.png", "neu", "-l", "tgk", "--psm", "4", "txt", "tsv"],
                       cwd=tmp, env=ENV, capture_output=True)
        nc, nw = conf(tmp / "neu.tsv")
        base = OUT / ordner / f"p{p:04d}"
        oc, ow = conf(base.with_suffix(".tsv")) if base.with_suffix(".tsv").exists() else (0.0, 0)
        if test:
            print(f"{ordner} S.{p}: alt {oc:.1f} ({ow} W.) -> neu {nc:.1f} ({nw} W.)")
            print((tmp / "neu.txt").read_text(encoding="utf-8")[:400])
            return ordner, p, oc, nc, False
        better = nc > oc
        if better:
            shutil.copy(tmp / "neu.txt", base.with_suffix(".txt"))
            shutil.copy(tmp / "neu.tsv", base.with_suffix(".tsv"))
        return ordner, p, oc, nc, better
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    test = int(sys.argv[sys.argv.index("--test") + 1]) if "--test" in sys.argv else None
    with open(OUT / "baende.csv", encoding="utf-8") as f:
        baende = {r["ordner"]: (SRC / r["datei"], int(r["seiten"])) for r in csv.DictReader(f)}
    jobs = []
    nur = [a for a in sys.argv[1:] if a in CROP]
    for ordner in (nur or CROP):
        pdf, n = baende[ordner]
        pages = [test] if test else range(1, n + 1)
        jobs += [(pdf, ordner, p, bool(test)) for p in pages]
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(run, jobs))
    if test:
        return
    for ordner in (nur or CROP):
        r = [x for x in res if x[0] == ordner]
        alt = sum(x[2] for x in r) / len(r); neu = sum(max(x[2], x[3]) for x in r) / len(r)
        print(f"{ordner}: {len(r)} S., ersetzt {sum(x[4] for x in r)}, Mittel {alt:.1f} -> {neu:.1f}")
    print("FERTIG")

if __name__ == "__main__":
    main()
