"""Gleicht die Segmentierung eines Bandes mit einem von Hand abgeschriebenen Inhaltsverzeichnis ab.

Aufruf: farzona_tocvergleich.py ORDNER TOCDATEI
TOCDATEI: eine Zeile je Gedicht, "seite|titel" (seite "-" wenn im Buch keine Zahl steht).
Ausgabe: nur Abweichungen -- EXTRA (Gedicht ohne Eintrag) und FEHLT (Eintrag ohne Gedicht).
"""
import json
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from farzona_split import OUT, norm  # noqa: E402


def score(k, pm):
    best = 0.0
    kand = [pm.get("title") or ""] + [l for l in pm["lines"][:2] if l]
    for c in kand:
        s = norm(c)[:len(k) + 2]
        if s:
            best = max(best, SequenceMatcher(None, k, s).ratio())
    return best


def main():
    ordner, tocdatei = sys.argv[1], sys.argv[2]
    toc = [l.split("|", 1) for l in open(tocdatei, encoding="utf-8").read().splitlines() if "|" in l]
    poems = [json.loads(l) for l in open(OUT / "gedichte" / f"{ordner}.jsonl", encoding="utf-8")]
    keys = [norm(t)[:24] for _, t in toc]
    j, aus = 0, []
    for pm in poems:
        treffer = None
        for d in range(0, 4):
            if j + d < len(toc) and score(keys[j + d], pm) >= 0.7:
                treffer = j + d
                break
        if treffer is None:
            aus.append(f"EXTRA S.{pm['page']} «{(pm.get('title') or '')[:25]}» «{' '.join(pm['lines'][0].split()[:4])}» {len(pm['lines'])}")
            continue
        for m in range(j, treffer):
            aus.append(f"FEHLT {toc[m][0]} {toc[m][1]}")
        j = treffer + 1
    for m in range(j, len(toc)):
        aus.append(f"FEHLT {toc[m][0]} {toc[m][1]}")
    print(f"{ordner}: Gedichte {len(poems)}, Verzeichnis {len(toc)}")
    print("\n".join(aus))


if __name__ == "__main__":
    main()
