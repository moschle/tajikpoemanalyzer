#!/usr/bin/python3
"""Traegt Korrekturen aus der Seitenpruefung ein und protokolliert geprueften Seitenbereich.
Aufruf: korr.py ORDNER GEPRUEFT_BIS 'JSON-Liste'   z.B.  korr.py ФАРЗОНА_ОЯТИ_ИШҚ 24 '[{"s":1,"a":"seite_weg"}]'"""
import json, sys
from pathlib import Path
OUT = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona"
f, log = OUT / "korrekturen.json", OUT / "pruefung.json"
k = json.load(open(f, encoding="utf-8")) if f.exists() else {}
g = json.load(open(log, encoding="utf-8")) if log.exists() else {}
ordner, bis, neu = sys.argv[1], int(sys.argv[2]), json.loads(sys.argv[3]) if len(sys.argv) > 3 else []
lst = k.setdefault(ordner, [])
for c in neu:
    if c not in lst:
        lst.append(c)
g[ordner] = max(g.get(ordner, 0), bis)
json.dump(k, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(g, open(log, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(ordner, "Korrekturen:", len(lst), "geprueft bis S.", g[ordner])
