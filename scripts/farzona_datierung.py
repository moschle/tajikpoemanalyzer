"""Datiert Gedichte, die nur in der Sammelausgabe belegt sind, ueber ihre Stelle im Inhaltsverzeichnis.

Die Sammelausgabe ordnet die Gedichte nach den Baenden, in denen sie erschienen sind (1994/1998 -> 2000/2006
-> 2008/2011 -> 2014, am Ende Rubaiyat). Ein dort neues Gedicht liegt zwischen datierten Nachbarn; sein
Erstdruck faellt in den Zeitraum zwischen dem Jahr des vorigen und des naechsten datierten Gedichts.
Fehlt ein Nachbar (Bandanfang), bleibt die Grenze offen. Obergrenze ist immer das Jahr der Sammelausgabe.

Ausgabe: data/ocr_farzona/datierung.json {ordner#nr: {"von", "bis", "vor", "nach", "methode"}}
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from farzona_import import ALLE, SAMMELBAENDE  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "ocr_farzona"


def main():
    erst = json.load(open(OUT / "dubletten.json", encoding="utf-8"))
    res = {}
    for o in SAMMELBAENDE:
        jahr_sammel = ALLE[o][1]
        seq = []
        for l in open(OUT / "gedichte" / f"{o}.jsonl", encoding="utf-8"):
            p = json.loads(l)
            if p.get("uebersetzung"):
                continue
            k = f"{o}#{p['nr']}"
            q = erst.get(k, k).split("#")[0]
            seq.append((k, None if q == o else ALLE[q][1], p["page"]))
        for i, (k, y, page) in enumerate(seq):
            if y is not None:
                continue
            vor = next((seq[j] for j in range(i - 1, -1, -1) if seq[j][1] is not None), None)
            nach = next((seq[j] for j in range(i + 1, len(seq)) if seq[j][1] is not None), None)
            ys = [x[1] for x in (vor, nach) if x]
            res[k] = {
                "von": min(ys) if vor and nach else (vor[1] if vor else None),
                "bis": min(max(ys), jahr_sammel) if ys else jahr_sammel,
                "vor": f"S. {vor[2]}, {vor[1]}" if vor else None,
                "nach": f"S. {nach[2]}, {nach[1]}" if nach else None,
                "seite": page,
                "methode": "Stelle im Inhaltsverzeichnis der Sammelausgabe zwischen datierten Gedichten",
            }
    json.dump(res, open(OUT / "datierung.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    from collections import Counter
    print(len(res), "datiert;", Counter(f"{v['von']}-{v['bis']}" for v in res.values()).most_common(15))


if __name__ == "__main__":
    main()
