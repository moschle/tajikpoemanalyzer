#!/usr/bin/python3
"""Kennzahlen Farzona-Korpus je Band: Gedichte, Zeilen, freier Vers, Radif, Metrum-Status, Mehrfachbelege."""
import json
from collections import Counter
from pathlib import Path
d = json.load(open(Path(__file__).resolve().parent.parent / "tajik_corpus/corpus/corpus.json", encoding="utf-8"))
aid = next(a for a, v in d["authors"].items() if v["name"] == "Farzona")
works = {w: v for w, v in d["works"].items() if v["author_id"] == aid}
ps = [p for p in d["poems"] if p["author_id"] == aid]
print("| Jahr | Band | Ort, Verlag | Auflage | Gedichte | Zeilen | freier Vers | Radif |")
print("|---|---|---|---|---|---|---|---|")
tot = Counter()
for w, v in sorted(works.items(), key=lambda x: x[1]["publication_year"] or 0):
    q = [p for p in ps if any(a["work_id"] == w for a in p["attestations"])]
    f = [p["features"] for p in q]
    n = len(q); fv = sum(x["meter_status"] == "free_verse" for x in f); rd = sum(bool(x["has_radif"]) for x in f)
    ln = sum(x["lines"] or 0 for x in f)
    tot.update(n=n, fv=fv, rd=rd, ln=ln)
    print(f"| {v['publication_year']} | {v['title']} | {v['city']}, {v['publisher']} | {v['notes'].split(';')[0].replace('Auflage ', '')} | {n} | {ln} | {fv} | {rd} |")
print(f"| | **Summe** | | | **{tot['n']}** | **{tot['ln']}** | **{tot['fv']}** | **{tot['rd']}** |")
print()
print("Datensaetze:", len(ps), "| mehrfach belegt:", sum(len(p["attestations"]) > 1 for p in ps),
      "| Analysefehler:", sum("error" in (p["analysis"] or {}) for p in ps))
print("Metrum-Status:", dict(Counter(p["features"]["meter_status"] for p in ps)))
print("Metren (Top 8):", Counter(p["features"]["meter"] for p in ps if p["features"]["meter_status"] == "identified").most_common(8))
