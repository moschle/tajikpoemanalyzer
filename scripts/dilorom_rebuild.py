"""dilorom_rebuild.py -- Dilorom-Gedichte im Korpus aus den Quelldateien neu aufbauen
(Segmentierung: dilorom_segment.py; Ergebnis T 40, E 34, B 33 wie in der Handzaehlung).
Gleiche Texte in mehreren Fassungen bleiben ein Datensatz mit mehreren Belegen (attestations)."""
import json, sys, logging
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0, "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer")
sys.path.insert(0, "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer/scripts")
logging.disable(logging.WARNING)
from analyzer import EnhancedTajikPoemAnalyzer
from corpus_core import Corpus
from dilorom_segment import DATEIEN, D, zerlege, ist_titel

ZUSAMMEN = {"E": [(12, 13)]}      # E: Widmungsgedicht fuer Dilafruz durch *** geteilt (vgl. B: ЧАХОН ХОЛИСТ БЕ ТУ)
WERK = {"T": "Tūfonhoi sokit", "E": "Bā anore ḥamḫūn (Entwurf)", "B": "Бо аноре ҳамхун"}

c = Corpus(Path("/Users/moritzschlenstedt/Projects/tajikpoemanalyzer/tajik_corpus"))
aid = next(k for k, v in c.data["authors"].items() if v["name"].startswith("Dil"))
name = c.data["authors"][aid]["name"]
wid = {k: next(w for w, x in c.data["works"].items() if x["author_id"] == aid and x["title"] == t)
       for k, t in WERK.items()}
alt = sum(p["author_id"] == aid for p in c.data["poems"])
c.data["poems"] = [p for p in c.data["poems"] if p["author_id"] != aid]
an = EnhancedTajikPoemAnalyzer(enable_corpus=False)
n = 0
for k in ("T", "E", "B"):
    g = zerlege(open(D + DATEIEN[k], encoding="utf-8").read())
    for a, b in sorted(ZUSAMMEN.get(k, []), reverse=True):
        g[a:b + 1] = ["\n".join(g[a:b + 1])]
    w = c.data["works"][wid[k]]
    for nr, text in enumerate(g, 1):
        erste = next(l.strip() for l in text.split("\n") if l.strip())
        res = json.loads(json.dumps(asdict(an.analyze_poem(text)), default=str))
        c.add_poem(title=erste if ist_titel(erste) else erste[:50], text=text, author=name,
                   work_title=w["title"], work_kw={"is_draft": w.get("is_draft")}, analysis=res,
                   poem_id=f"D{k}{nr:02d}",
                   contributor={"anonymous": True, "source_filename": DATEIEN[k], "nr": nr})
        n += 1
    print(k, len(g))
c.save()
neu = sum(p["author_id"] == aid for p in c.data["poems"])
print(f"Dilorom: vorher {alt} Datensaetze, jetzt {neu} (aus {n} Gedichten, gleiche Texte als Belege)")
