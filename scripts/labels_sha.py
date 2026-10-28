"""labels_sha.py -- Review- und Gold-Labels um text_sha256 ergaenzen (IDs koennen sich bei Neuaufbau verschieben)."""
import json
B = "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer/"
d = json.load(open(B + "tajik_corpus/corpus/corpus.json", encoding="utf-8"))
S = {p["id"]: p["text_sha256"] for p in d["poems"]}
R = B + "data/validierung/review.jsonl"
rows = [json.loads(l) for l in open(R, encoding="utf-8")]
for r in rows:
    r.setdefault("sha256", S[r["id"]])
open(R, "w", encoding="utf-8").write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
G = B + "data/validierung/farzona_metrum_gold.json"
g = json.load(open(G, encoding="utf-8"))
for st in g["stichproben"].values():
    for x in st:
        x.setdefault("sha256", S[x["id"]])
json.dump(g, open(G, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", len(rows))
