#!/usr/bin/python3
"""Findet Nachdrucke ueber Baende hinweg (unscharf, OCR-tolerant).
Schluessel: ersten zwei Verse normalisiert; Kandidaten ueber Bloecke (Anfang/Ende der Verse),
Vergleich mit SequenceMatcher >= 0.85. Jedes Gedicht wird dem fruehesten Band zugeordnet.
Ausgabe: data/ocr_farzona/dubletten.json {ordner#nr: erstbeleg ordner#nr} + Tabelle."""
import json, sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from farzona_split import norm, OUT
from farzona_import import ALLE, SAMMELBAENDE, rang

def keys(pm):
    """Schluessel ueber Vers 1–2 und 2–3; eine kurze Kopfzeile (Titel in Normalschrift) wird uebersprungen."""
    v = [x for x in pm["lines"] if x]
    out = [norm(" ".join(v[:2]))[:120], norm(" ".join(v[1:3]))[:120]]
    if v and len(v[0].split()) <= 3:
        out.append(norm(" ".join(v[1:3]))[:120])
    return [k for k in dict.fromkeys(out) if len(k) >= 25]

def sim(a, b):
    return max(SequenceMatcher(None, x, y).ratio() for x in a for y in b)

def main():
    poems = []
    for ordner, (titel, jahr, *_ ) in ALLE.items():
        for l in open(OUT / "gedichte" / f"{ordner}.jsonl", encoding="utf-8"):
            pm = json.loads(l)
            ks = keys(pm)
            if ks and not pm.get("uebersetzung"):
                poems.append((jahr, ordner in SAMMELBAENDE, ordner, pm["nr"], ks))
    poems.sort()                                    # frueheste zuerst
    blocks = defaultdict(list)
    for i, (_, _, _, _, ks) in enumerate(poems):
        for k in ks:
            for b in (k[2:12], k[-12:-2], k[len(k)//2:len(k)//2+10]):
                blocks[b].append(i)
    parent = list(range(len(poems)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    seen = set()
    for ids in blocks.values():
        if len(ids) > 60:                           # Allerweltsanfang, zu unspezifisch
            continue
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                i, j = ids[a], ids[b]
                if (i, j) in seen or poems[i][2] == poems[j][2]:
                    continue
                seen.add((i, j))
                if sim(poems[i][4], poems[j][4]) >= 0.85:
                    ri, rj = find(i), find(j)
                    if ri != rj:
                        parent[max(ri, rj)] = min(ri, rj)   # frueherer Index = frueheres Jahr
    erst = {}
    for i, (j, _, o, n, _) in enumerate(poems):
        r = find(i)
        erst[f"{o}#{n}"] = f"{poems[r][2]}#{poems[r][3]}"
    json.dump(erst, open(OUT / "dubletten.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("| Jahr | Band | Gedichte | davon Erstdruck | Nachdruck |")
    print("|---|---|---|---|---|")
    tot = [0, 0]
    for ordner, (titel, jahr, *_ ) in sorted(ALLE.items(), key=lambda x: rang(x[0])):
        if ordner in SAMMELBAENDE:
            titel += " (Sammelausgabe)"
        ks = [k for k in erst if k.startswith(ordner + "#")]
        eb = sum(1 for k in ks if erst[k] == k)
        tot[0] += eb; tot[1] += len(ks) - eb
        print(f"| {jahr} | {titel} | {len(ks)} | {eb} | {len(ks) - eb} |")
    print(f"| | **Summe** | **{sum(tot)}** | **{tot[0]}** | **{tot[1]}** |")

if __name__ == "__main__":
    main()
