"""review_batch.py STATUS START ANZAHL [AUTOR] -- Gedichte eines Metrum-Status zum Review ausgeben
(Index, Zeilenzahl, Laengenabweichung, erste drei Zeilen). Bereits reviewte IDs werden uebersprungen.
Texte nur lokal ausgeben, nie committen."""
import json, sys, os
sys.path.insert(0, "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer")
from analyzer import EnhancedTajikPoemAnalyzer as E
B = "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer/"
R = B + "data/validierung/review.jsonl"
st, a, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
autor = sys.argv[4] if len(sys.argv) > 4 else "Farzona"
d = json.load(open(B + "tajik_corpus/corpus/corpus.json", encoding="utf-8"))
aid = next(k for k, v in d["authors"].items() if v["name"].startswith(autor))
done = {json.loads(l)["id"] for l in open(R, encoding="utf-8")} if os.path.exists(R) else set()
ps = sorted((p for p in d["poems"] if p["author_id"] == aid and p["features"].get("meter_status") == st
             and p["id"] not in done), key=lambda p: p["id"])
for p in ps[a:a + n]:
    ls = [l.strip() for l in p["text"].split("\n") if l.strip()]
    print(f"{p['id'][:10]} n={len(ls)} abw={E._laengen_abweichung(p['text']):.2f} m={p['features'].get('meter')}")
    for l in ls[:2]:
        print("   ", l[:70])
print("REST", len(ps))
