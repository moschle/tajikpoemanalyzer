#!/usr/bin/python3
"""Liest Gedichtnummern neu: Zeilen, die nur aus Ziffern bestehen, werden aus der 300-dpi-Seite
ausgeschnitten und mit einem reinen Ziffernmodell erkannt. Seitenzahlen (Seite - Versatz) bleiben aus.
Ausgabe: data/ocr_farzona/nummern/<ordner>.json {seite: [nummer, top]}"""
import csv, json, os, re, subprocess, sys, tempfile, shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
SRC = Path.home() / "Documents/Akademisch/MA/vergleichsgruppe/Farzona Tadschikistan"
OUT = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona"
ENV = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ.get("PATH", ""), OMP_THREAD_LIMIT="1")

def boxes(tsv):
    rows = {}
    with open(tsv, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r.get("level") == "5" and (r.get("text") or "").strip():
                k = (r["block_num"], r["par_num"], r["line_num"])
                rows.setdefault(k, []).append((int(r["left"]), int(r["top"]), int(r["width"]), int(r["height"]), r["text"]))
    out = []
    for ws in rows.values():
        t = " ".join(w[4] for w in sorted(ws))
        if re.fullmatch(r"[\d\s\-–—•.)(]+", t.strip()) and re.search(r"\d", t):
            x0 = min(w[0] for w in ws); y0 = min(w[1] for w in ws)
            x1 = max(w[0] + w[2] for w in ws); y1 = max(w[1] + w[3] for w in ws)
            out.append((x0, y0, x1, y1))
    return out

def job(a):
    pdf, ordner, p, crop = a
    bx = boxes(OUT / ordner / f"p{p:04d}.tsv")
    if not bx:
        return p, []
    tmp = Path(tempfile.mkdtemp(dir=OUT / "_tmp"))
    try:
        subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", "300", "-gray", "-png", "-singlefile", str(pdf), "pg"],
                       cwd=tmp, env=ENV, check=True, capture_output=True)
        im = Image.open(tmp / "pg.png")
        if crop:
            w, h = im.size
            l, t, r, b = crop
            im = im.crop((int(w * l), int(h * t), int(w * (1 - r)), int(h * (1 - b))))
        res = []
        for x0, y0, x1, y1 in bx:
            pad = 25
            c = im.crop((max(0, x0 - pad), max(0, y0 - pad), x1 + pad, y1 + pad))
            c = c.resize((c.width * 2, c.height * 2))
            c.save(tmp / "n.png")
            o = subprocess.run(["tesseract", "n.png", "-", "--psm", "7", "-c", "tessedit_char_whitelist=0123456789"],
                               cwd=tmp, env=ENV, capture_output=True, text=True).stdout.strip()
            if o.isdigit():
                res.append([int(o), y0])
        return p, res
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ocr_farzona_crop import CROP
    (OUT / "nummern").mkdir(exist_ok=True)
    with open(OUT / "baende.csv", encoding="utf-8") as f:
        baende = [r for r in csv.DictReader(f) if r["ordner"] in sys.argv[1:]]
    for r in baende:
        jobs = [(SRC / r["datei"], r["ordner"], p, CROP.get(r["ordner"])) for p in range(1, int(r["seiten"]) + 1)
                if (OUT / r["ordner"] / f"p{p:04d}.tsv").exists()]
        with ThreadPoolExecutor(6) as ex:
            res = dict(ex.map(job, jobs))
        json.dump({p: v for p, v in res.items() if v}, open(OUT / "nummern" / f"{r['ordner']}.json", "w"), indent=0)
        print(r["ordner"], sum(len(v) for v in res.values()), "Nummernfelder")

if __name__ == "__main__":
    main()
