#!/usr/bin/python3
"""Sucht Impressum-Zeilen (Jahr, Verlag, ISBN, Auflage) in den ersten/letzten Seiten jedes Bandes."""
import csv, re
from pathlib import Path
OUT = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona"
PAT = re.compile(r"(19[89]\d|20[0-2]\d)|ISBN|ББК|УДК|нашриёт|Нашриёт|адади|Адади|теъдод|Теъдод|Душанбе|Хуҷанд|Тиражи|нусха", re.I)
with open(OUT / "baende.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        n = int(r["seiten"]); d = OUT / r["ordner"]
        print("=== " + r["ordner"])
        for p in list(range(1, 7)) + list(range(max(7, n - 5), n + 1)):
            t = d / f"p{p:04d}.txt"
            if not t.exists():
                continue
            for line in t.read_text(encoding="utf-8").splitlines():
                if PAT.search(line) and len(line) < 140:
                    print(f"  S{p}: {line.strip()}")
