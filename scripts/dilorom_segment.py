"""dilorom_segment.py [-v] -- Dilorom-Quelldateien (T, E, B) in Einzelgedichte zerlegen.
Neues Gedicht: Zeile ganz in Grossbuchstaben (Titel) oder Trenner ***. Folgen zwei Titel direkt
aufeinander, ist der erste ein eigenes Gedicht nur, wenn dazwischen Text steht; Widmungen in Klammern
oder mit Ба/Барои + Name bleiben beim Gedicht."""
import re, sys, json
D = "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer/data/"
DATEIEN = {"T": "dilorom_soliboeva_tufonhoi_sokit.txt", "E": "dilorom_entwurf_bo_anore_khamhun.txt",
           "B": "dilorom_bo_anore_khamhun.txt"}


def ist_titel(l):
    s = l.strip().strip("()«»\"“”.!?…")
    buch = [c for c in s if c.isalpha()]
    return len(buch) >= 3 and all(c.isupper() for c in buch)


def ist_trenner(l):
    return bool(re.fullmatch(r"\s*[*✱•]{3,}\s*", l))


def zerlege(text):
    gedichte, cur = [], []
    for l in text.split("\n"):
        if ist_trenner(l):
            if any(x.strip() for x in cur):
                gedichte.append(cur)
            cur = []
            continue
        if ist_titel(l):
            koerper = [x for x in cur if x.strip() and not ist_titel(x)]
            if koerper:
                gedichte.append(cur)
                cur = []
        cur.append(l)
    if any(x.strip() for x in cur):
        gedichte.append(cur)
    out = []
    for g in gedichte:
        ls = [x.rstrip() for x in g]
        while ls and not ls[0].strip():
            ls.pop(0)
        while ls and not ls[-1].strip():
            ls.pop()
        if ls:
            out.append("\n".join(ls))
    return out


if __name__ == "__main__":
    res = {}
    for k, f in DATEIEN.items():
        g = zerlege(open(D + f, encoding="utf-8").read())
        res[k] = g
        print(k, len(g))
        if "-v" in sys.argv:
            for i, x in enumerate(g):
                ls = [l for l in x.split("\n") if l.strip()]
                print(f"  {i:2} n={len(ls):3} | {' / '.join(l.strip()[:28] for l in ls[:2])}")
    if "-o" in sys.argv:
        json.dump(res, open("/tmp/dilorom_seg.json", "w"), ensure_ascii=False)
