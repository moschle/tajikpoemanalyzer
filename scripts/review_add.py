"""review_add.py RUNDE 'ID=label ID=label ...' -- Labels an data/validierung/review.jsonl anhaengen.
Label = Versmassfamilie (hazaj, ramal, rajaz, mujt, khafif, mudari, sari, ruba, munsarih, mutaqarib, kamil ...),
'frei', 'ocr' (Text zu beschaedigt) oder '?'. Optional Unterform nach Doppelpunkt: hazaj:ashtar."""
import json, sys, datetime
R = "/Users/moritzschlenstedt/Projects/tajikpoemanalyzer/data/validierung/review.jsonl"
runde = int(sys.argv[1])
d = json.load(open("/Users/moritzschlenstedt/Projects/tajikpoemanalyzer/tajik_corpus/corpus/corpus.json", encoding="utf-8"))
S = {p["id"]: p["text_sha256"] for p in d["poems"]}
with open(R, "a", encoding="utf-8") as f:
    for tok in sys.argv[2].split():
        i, lab = tok.split("=")
        fam, _, sub = lab.partition(":")
        f.write(json.dumps({"id": i, "sha256": S[i], "label": fam, "unterform": sub or None, "runde": runde,
                            "reviewer": "claude-opus-5.5", "geprueft_von_mensch": False,
                            "datum": datetime.date.today().isoformat()}, ensure_ascii=False) + "\n")
print("ok")
