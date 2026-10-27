#!/usr/bin/python3
"""Stichproben: rendert je Band Seiten (Standard 40 % und 70 %) als kleine PNGs und schreibt,
was der Splitter auf diesen Seiten sieht (Gedichtanfaenge mit Zeilenzahl).
Aufruf: farzona_stichprobe.py [anteil ...]   Ausgabe: data/ocr_farzona/_tmp/stich/"""
import csv, json, os, subprocess, sys
from pathlib import Path
SRC = Path.home() / "Documents/Akademisch/MA/vergleichsgruppe/Farzona Tadschikistan"
OUT = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona"
ST = OUT / "_tmp/stich"; ST.mkdir(parents=True, exist_ok=True)
ENV = dict(os.environ, PATH="/opt/homebrew/bin:" + os.environ.get("PATH", ""))
anteile = [float(a) for a in sys.argv[1:]] or [0.4, 0.7]
bericht = []
with open(OUT / "baende.csv", encoding="utf-8") as f:
    for i, r in enumerate(csv.DictReader(f)):
        n = int(r["seiten"])
        poems = [json.loads(l) for l in open(OUT / "gedichte" / f"{r['ordner']}.jsonl", encoding="utf-8")]
        for a in anteile:
            p = int(n * a)
            name = f"b{i:02d}_s{p:03d}"
            subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", "55", "-gray", "-png", "-singlefile",
                            str(SRC / r["datei"]), str(ST / name)], env=ENV, check=True)
            hier = [pm for pm in poems if pm["page"] == p]
            vorher = [pm for pm in poems if pm["page"] < p]
            lauf = vorher[-1] if vorher else None
            zeilen = [f"{name}  {r['ordner'][8:30]} S.{p}"]
            if lauf:
                zeilen.append(f"   laeuft weiter: #{lauf['nr']} ab S.{lauf['page']} ({len([x for x in lauf['lines'] if x])} Z.) "
                              f"endet mit: {[x for x in lauf['lines'] if x][-1][:40]}")
            for pm in hier:
                v = [x for x in pm["lines"] if x]
                zeilen.append(f"   NEU #{pm['nr']} {'T: ' + pm['title'][:25] if pm['title'] else ''} | {v[0][:40]} | {len(v)} Z."
                              f"{' Anker' if pm.get('anker') else ''}")
            bericht.append("\n".join(zeilen))
(ST / "bericht.txt").write_text("\n".join(bericht), encoding="utf-8")
print("\n".join(bericht))
