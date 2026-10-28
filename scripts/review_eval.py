"""review_eval.py [-v] -- aktuellen analyzer gegen alle Review- und Gold-Labels pruefen (Familienebene)."""
import json, sys, logging, unicodedata
from collections import Counter
from dataclasses import asdict
sys.path.insert(0, "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer")
logging.disable(logging.WARNING)
from analyzer import EnhancedTajikPoemAnalyzer
from corpus_core import extract_features
B = "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer/"
lab = {}
g = json.load(open(B + "data/validierung/farzona_metrum_gold.json", encoding="utf-8"))
for st in g["stichproben"].values():
    for x in st:
        lab[x["sha256"]] = x["label"]
for l in open(B + "data/validierung/review.jsonl", encoding="utf-8"):
    x = json.loads(l)
    lab[x["sha256"]] = x["label"]
lab = {k: v for k, v in lab.items() if v not in ("?", "ocr")}
d = json.load(open(B + "tajik_corpus/corpus/corpus.json", encoding="utf-8"))
P = {p["text_sha256"]: p for p in d["poems"]}
an = EnhancedTajikPoemAnalyzer(enable_corpus=False)
def fam(m):
    m = unicodedata.normalize("NFD", str(m).lower())
    m = "".join(c for c in m if c.isalpha() or c == " ")
    return m.split()[0][:4] if m.strip() else ""
ok, fehler = 0, Counter()
for i, g in lab.items():
    f = extract_features(json.loads(json.dumps(asdict(an.analyze_poem(P[i]["text"])), default=str)))
    st = f.get("meter_status")
    res = "frei" if st == "free_verse" else (fam(f.get("meter")) if st == "identified" else "FEHL")
    hit = res == ("frei" if g == "frei" else g[:4]) or (g == "geb" and res not in ("frei", "FEHL"))
    ok += hit
    if not hit:
        fehler[(g, res)] += 1
        if "-v" in sys.argv:
            print(P[i]["id"], g, "->", res, f.get("meter"))
print(f"Treffer {ok}/{len(lab)} = {ok / len(lab):.1%}")
print("Fehler:", fehler.most_common(12))
