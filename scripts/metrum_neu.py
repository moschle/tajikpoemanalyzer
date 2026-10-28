"""metrum_neu.py [AUTOR ...] -- Metrum-Felder (meter*, free_verse*) im Korpus mit dem aktuellen
analyzer.py neu berechnen; alle anderen Merkmale bleiben unveraendert. Ohne Argument: alle Autoren
ausser Farzona (deren Import rechnet ohnehin neu)."""
import json, sys, logging
from dataclasses import asdict
sys.path.insert(0, "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer")
logging.disable(logging.WARNING)
from analyzer import EnhancedTajikPoemAnalyzer
from corpus_core import extract_features
F = "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer/tajik_corpus/corpus/corpus.json"
d = json.load(open(F, encoding="utf-8"))
namen = sys.argv[1:]
ids = {a for a, v in d["authors"].items() if (v["name"] in namen if namen else v["name"] != "Farzona")}
an = EnhancedTajikPoemAnalyzer(enable_corpus=False)
n = 0
for p in d["poems"]:
    if p["author_id"] not in ids:
        continue
    f = extract_features(json.loads(json.dumps(asdict(an.analyze_poem(p["text"])), default=str)))
    for k, v in f.items():
        if k.startswith("meter") or k.startswith("free_verse"):
            p["features"][k] = v
    n += 1
json.dump(d, open(F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("neu berechnet:", n)
