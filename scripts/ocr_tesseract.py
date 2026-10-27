#!/usr/bin/env python3
"""Local OCR for Tajik Cyrillic PDFs with Tesseract (model `tgk`). Texts never leave the machine.

    python scripts/ocr_tesseract.py VOLUME.pdf OUTDIR [--crop L,T,R,B] [--dpi 300] [--workers 6] [--pages 5-120]

Writes per page OUTDIR/pNNNN.txt and pNNNN.tsv (word boxes with confidence), OUTDIR/quality.csv
(words and mean confidence per page) and OUTDIR/volume.txt (all pages, page breaks marked as
`<<<page N>>>`). Re-running resumes: pages already recognised are skipped.

--crop  cut a margin (fractions of width/height: left, top, right, bottom) before recognition.
        Use it for books with ornamental frames, which Tesseract otherwise reads as letters
        (e.g. --crop 0.13,0.06,0.11,0.09). Check quality.csv: pages below ~70 need attention.

Requirements: tesseract with the Tajik model (`tgk.traineddata`, e.g. `brew install tesseract
tesseract-lang`), poppler (`pdftoppm`), Pillow. Splitting the page text into poems is a separate,
book-specific step: see scripts/farzona_split.py for a worked example (table of contents as anchors,
ornaments, running heads, footnotes, rubāʿī and ghazal rules, a corrections file from page review).
"""
import argparse, csv, os, shutil, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ENV = dict(os.environ, PATH="/opt/homebrew/bin:/usr/local/bin:" + os.environ.get("PATH", ""), OMP_THREAD_LIMIT="1")

def page_count(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], env=ENV, capture_output=True, text=True).stdout
    return int(next(l.split()[-1] for l in out.splitlines() if l.startswith("Pages:")))

def mean_conf(tsv):
    vals = []
    with open(tsv, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            try:
                c = float(r["conf"])
            except (KeyError, ValueError, TypeError):
                continue
            if c >= 0 and (r.get("text") or "").strip():
                vals.append(c)
    return len(vals), (sum(vals) / len(vals) if vals else 0.0)

def ocr_page(args):
    pdf, out, p, dpi, crop, lang = args
    base = out / f"p{p:04d}"
    if base.with_suffix(".txt").exists() and base.with_suffix(".txt").stat().st_size > 0:
        return p
    tmp = Path(tempfile.mkdtemp(dir=out / "_tmp"))
    try:
        subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", str(dpi), "-gray", "-png", "-singlefile",
                        str(pdf), "pg"], cwd=tmp, env=ENV, check=True, capture_output=True)
        img = "pg.png"
        if crop:
            from PIL import Image
            im = Image.open(tmp / img)
            w, h = im.size
            l, t, r, b = crop
            im.crop((int(w * l), int(h * t), int(w * (1 - r)), int(h * (1 - b)))).save(tmp / "c.png")
            img = "c.png"
        res = subprocess.run(["tesseract", img, "page", "-l", lang, "--psm", "4", "txt", "tsv"],
                             cwd=tmp, env=ENV, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"ERROR page {p}: {res.stderr.strip()[:200]}")
            return p
        shutil.copy(tmp / "page.txt", base.with_suffix(".txt"))
        shutil.copy(tmp / "page.tsv", base.with_suffix(".tsv"))
        return p
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--crop", type=lambda s: tuple(float(x) for x in s.split(",")), default=None)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--pages", default=None, help="range, e.g. 5-120")
    ap.add_argument("--lang", default="tgk")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "_tmp").mkdir(exist_ok=True)
    n = page_count(a.pdf)
    lo, hi = (map(int, a.pages.split("-")) if a.pages else (1, n))
    pages = list(range(lo, min(hi, n) + 1))
    jobs = [(a.pdf, a.out, p, a.dpi, a.crop, a.lang) for p in pages]
    with ThreadPoolExecutor(a.workers) as ex:
        for i, _ in enumerate(ex.map(ocr_page, jobs), 1):
            if i % 50 == 0:
                print(f"{i}/{len(pages)} pages")
    with open(a.out / "quality.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["page", "words", "mean_confidence"])
        for p in pages:
            tsv = a.out / f"p{p:04d}.tsv"
            if tsv.exists():
                words, conf = mean_conf(tsv)
                w.writerow([p, words, round(conf, 1)])
    with open(a.out / "volume.txt", "w", encoding="utf-8") as f:
        for p in pages:
            t = a.out / f"p{p:04d}.txt"
            if t.exists():
                f.write(f"<<<page {p}>>>\n" + t.read_text(encoding="utf-8").strip() + "\n\n")
    shutil.rmtree(a.out / "_tmp", ignore_errors=True)
    print(f"done: {len(pages)} pages -> {a.out}")

if __name__ == "__main__":
    main()
