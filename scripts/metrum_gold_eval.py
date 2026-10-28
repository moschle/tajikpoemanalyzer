"""gold_eval.py -- 40 Farzona-Gedichte, Handlabel (Claude, 28.10.) gegen analyzer."""
import json, sys, logging
from dataclasses import asdict
sys.path.insert(0, "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer")
logging.disable(logging.WARNING)
from analyzer import EnhancedTajikPoemAnalyzer
from corpus_core import extract_features
B = "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer/"
G = ("hazaj ruba ruba ruba mujtathth ruba khafif ramal ramal ramal hazaj frei ruba frei frei ? "
     "sari mudari ruba frei hazaj ruba frei mudari hazaj hazaj hazaj sari ruba hazaj hazaj rajaz "
     "mudari hazaj sari khafif ruba mudari ramal ruba").split()
an = EnhancedTajikPoemAnalyzer(enable_corpus=False)
d = json.load(open(B + "tajik_corpus/corpus/corpus.json", encoding="utf-8"))
ids = json.load(open(B + "data/ocr_farzona/_tmp/gold_ids" + ("_" + sys.argv[1] if len(sys.argv) > 1 else "") + ".json"))
if len(sys.argv) > 2: G = sys.argv[2].split()
P = {p["id"]: p for p in d["poems"]}
ok = n = 0
for i, (pid, g) in enumerate(zip(ids, G)):
    f = extract_features(json.loads(json.dumps(asdict(an.analyze_poem(P[pid]["text"])), default=str)))
    m, st, fv = f.get("meter"), f.get("meter_status"), f.get("meter_status") == "free_verse"
    res = "frei" if fv else (str(m) if st == "identified" else "FEHL")
    hit = (g == "frei" and fv) or (g != "frei" and g != "?" and g[:4] in str(m).lower().replace("ʿ", "").replace("ā", "a").replace("ḍ", "d").replace("ū", "u").replace("ī", "i"))
    if g != "?":
        n += 1; ok += bool(hit)
    print(f"#{i:2} gold={g:9} ana={res:45} {'OK' if hit else '--'}")
print("Treffer", ok, "/", n)
