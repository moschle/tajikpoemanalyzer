#!/usr/bin/python3
"""Soll-Stand verifizierter Baende sichern und pruefen (Regressionsschutz).
  farzona_soll.py save ORDNER      Zerlegung nach Seitenpruefung als Soll speichern
  farzona_soll.py check            alle gesicherten Baende neu zerlegen und mit dem Soll vergleichen
Soll je Gedicht: Seite, Titel, Anfang der ersten Zeile, Verszahl."""
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from farzona_split import OUT, split_band, load_korr, norm
SOLL = OUT / "soll"

def sig(pm):
    v = [x for x in pm["lines"] if x]
    return [pm["page"], pm["title"] or "", norm(v[0])[:12] if v else "", len(v)]

def main():
    SOLL.mkdir(exist_ok=True)
    baende = {r["ordner"]: r for r in csv.DictReader(open(OUT / "baende.csv", encoding="utf-8"))}
    if sys.argv[1] == "save":
        r = baende[sys.argv[2]]
        poems, _, _ = split_band(r)
        json.dump([sig(p) for p in poems], open(SOLL / f"{r['ordner']}.json", "w", encoding="utf-8"), ensure_ascii=False)
        print(r["ordner"], "Soll gesichert:", len(poems), "Gedichte")
        return
    korr = load_korr(); ok = True
    for f in sorted(SOLL.glob("*.json")):
        r = baende[f.stem]
        soll = json.load(open(f, encoding="utf-8"))
        ist = [sig(p) for p in split_band(r, korr)[0]]
        if ist == soll:
            print(f"OK   {f.stem}: {len(ist)}")
            continue
        ok = False
        diff = [(a, b) for a, b in zip(soll, ist) if a != b][:3]
        print(f"FEHL {f.stem}: Soll {len(soll)}, Ist {len(ist)}; erste Abweichungen: {diff}")
    print("ALLES OK" if ok else "REGRESSION")

if __name__ == "__main__":
    main()
