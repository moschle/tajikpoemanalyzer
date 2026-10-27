"""Gleicht die Segmentierung eines Bandes mit einem von Hand abgeschriebenen Inhaltsverzeichnis ab.

Aufruf: farzona_tocvergleich.py ORDNER TOCDATEI [BIS_SEITE]
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
    if len(sys.argv) > 3:
        poems = [pm for pm in poems if pm["page"] <= int(sys.argv[3])]
    keys = [norm(t)[:24] for _, t in toc]
    n, m = len(poems), len(toc)
    sc = [[0.0] * m for _ in range(n)]
    for a in range(n):
        for b in range(m):
            s = score(keys[b], poems[a])
            sc[a][b] = s if s >= 0.6 else 0.0
    # globale Ausrichtung (Reihenfolge bleibt erhalten), Luecken kosten nichts
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    for a in range(n - 1, -1, -1):
        for b in range(m - 1, -1, -1):
            D[a][b] = max(D[a + 1][b], D[a][b + 1], (sc[a][b] + D[a + 1][b + 1]) if sc[a][b] else 0.0)
    a = b = 0
    extra, fehlt = [], []
    while a < n or b < m:
        if a < n and b < m and sc[a][b] and D[a][b] == sc[a][b] + D[a + 1][b + 1]:
            a += 1; b += 1
        elif a < n and (b == m or D[a][b] == D[a + 1][b]):
            extra.append(a)
            a += 1
        else:
            fehlt.append(b)
            b += 1
    # Eintraege, die im Verzeichnis an anderer Stelle stehen (OCR-Reihenfolge), nachtraeglich zuordnen
    for a in list(extra):
        best = max(fehlt, key=lambda b: sc[a][b], default=None)
        if best is not None and sc[a][best] >= 0.75:
            extra.remove(a); fehlt.remove(best)
    aus = []
    for a in extra:
        pm = poems[a]
        aus.append((pm["page"], f"EXTRA S.{pm['page']} «{(pm.get('title') or '')[:25]}» «{' '.join(pm['lines'][0].split()[:4]) if pm['lines'] else ''}» {len(pm['lines'])}"))
    for b in fehlt:
        aus.append((int(toc[b][0]) if toc[b][0].isdigit() else 0, f"FEHLT {toc[b][0]} {toc[b][1]}"))
    aus = [t for _, t in sorted(aus, key=lambda x: x[0])]
    print(f"{ordner}: Gedichte {len(poems)}, Verzeichnis {len(toc)}")
    print("\n".join(aus))


if __name__ == "__main__":
    main()
