#!/usr/bin/env python3
"""Texterkennung der tadschikisch-kyrillischen Farzona-Bände mit Tesseract (tgk).

Lokal, ohne KI-Tokens. Pro Seite: Text (.txt) und Wortkonfidenzen (.tsv).
Bereits erkannte Seiten werden übersprungen, der Lauf kann also jederzeit neu gestartet werden.
Am Ende: quality.csv mit mittlerer Konfidenz pro Seite.
"""
import csv, os, subprocess, sys, tempfile, unicodedata, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SRC = Path.home() / "Documents/Akademisch/MA/vergleichsgruppe/Farzona Tadschikistan"
OUT = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona"
EXCLUDE = ("ГЕЙЗЕР", "СОЯИ ҒАЗАЛ", "ҒАЗАЛЛАР ГУЛДАСТАСИ")  # Übersetzung, persische Schrift, usbekisch
DPI, WORKERS = 300, 6
ENV = dict(os.environ, PATH="/opt/homebrew/bin:/usr/local/bin:" + os.environ.get("PATH", ""), OMP_THREAD_LIMIT="1")


def slug(name):
    s = unicodedata.normalize("NFC", Path(name).stem)
    s = re.sub(r"[^\w]+", "_", s).strip("_")
    return s[:60]


def pages(pdf):
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, env=ENV).stdout
    return int(re.search(r"Pages:\s+(\d+)", out).group(1))


def ocr(job):
    pdf, p, d = job
    base = d / f"p{p:04d}"
    if (base.with_suffix(".txt")).exists() and base.with_suffix(".txt").stat().st_size > 0:
        return
    work = OUT / "_tmp"
    work.mkdir(exist_ok=True)
    tmp = Path(tempfile.mkdtemp(dir=work))
    try:
        subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", str(DPI), "-gray", "-png", str(pdf), "pg"],
                       check=True, env=ENV, capture_output=True, cwd=tmp)
        img = next(tmp.glob("pg*.png")).name
        r = subprocess.run(["tesseract", img, str(base), "-l", "tgk", "--psm", "4", "txt", "tsv"],
                           env=ENV, capture_output=True, text=True, cwd=tmp)
        if r.returncode != 0:
            print(f"FEHLER {pdf.name} S. {p}: {r.stderr[-200:]}", flush=True)
    finally:
        for f in tmp.glob("*"):
            f.unlink()
        tmp.rmdir()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs, vols = [], []
    for pdf in sorted(SRC.glob("*.pdf")):
        name = unicodedata.normalize("NFC", pdf.name)
        if any(x in name for x in EXCLUDE):
            continue
        d = OUT / slug(name)
        d.mkdir(exist_ok=True)
        n = pages(pdf)
        vols.append((name, d.name, n))
        jobs += [(pdf, p, d) for p in range(1, n + 1)]
    with open(OUT / "baende.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([("datei", "ordner", "seiten")] + vols)
    print(f"{len(vols)} Bände, {len(jobs)} Seiten", flush=True)
    done = 0
    with ThreadPoolExecutor(WORKERS) as ex:
        for _ in ex.map(ocr, jobs):
            done += 1
            if done % 100 == 0:
                print(f"{done}/{len(jobs)}", flush=True)
    rows = [("ordner", "seite", "woerter", "konfidenz")]
    for _, folder, n in vols:
        for p in range(1, n + 1):
            t = OUT / folder / f"p{p:04d}.tsv"
            confs = []
            if t.exists():
                for r in csv.DictReader(open(t, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
                    try:
                        c = float(r["conf"])
                    except (KeyError, ValueError):
                        continue
                    if c >= 0 and r.get("text", "").strip():
                        confs.append(c)
            rows.append((folder, p, len(confs), round(sum(confs) / len(confs), 1) if confs else ""))
    with open(OUT / "quality.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print("FERTIG", flush=True)


if __name__ == "__main__":
    main()
