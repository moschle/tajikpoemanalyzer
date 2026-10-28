"""review_stichprobe.py RUNDE [N_IDENT N_FREI N_FEHL] -- geschichtete Zufallsstichprobe (Seed = Runde) noch
nicht reviewter Farzona-Gedichte ausgeben: Analyzer-Ergebnis + erste Zeilen. Texte nur lokal."""
import json, sys, os, random
sys.path.insert(0, "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer")
from analyzer import EnhancedTajikPoemAnalyzer as E
B = "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer/"
R = B + "data/validierung/review.jsonl"
runde = int(sys.argv[1])
quoten = [int(x) for x in sys.argv[2:5]] if len(sys.argv) > 4 else [25, 15, 10]
d = json.load(open(B + "tajik_corpus/corpus/corpus.json", encoding="utf-8"))
aid = next(k for k, v in d["authors"].items() if v["name"] == "Farzona")
done = {json.loads(l)["sha256"] for l in open(R, encoding="utf-8")}
g = json.load(open(B + "data/validierung/farzona_metrum_gold.json", encoding="utf-8"))
done |= {x["sha256"] for s in g["stichproben"].values() for x in s}
random.seed(1000 + runde)
for st, q in zip(("identified", "free_verse", "detection_failed"), quoten):
    ps = sorted((p for p in d["poems"] if p["author_id"] == aid and p["features"].get("meter_status") == st
                 and p["text_sha256"] not in done), key=lambda p: p["id"])
    for p in random.sample(ps, min(q, len(ps))):
        ls = [l.strip() for l in p["text"].split("\n") if l.strip()]
        print(f"{p['id']} [{st[:5]}:{str(p['features'].get('meter'))[:24]}] n={len(ls)} "
              f"abw={E._laengen_abweichung(p['text']):.2f}")
        for l in ls[:3]:
            print("   ", l[:66])
