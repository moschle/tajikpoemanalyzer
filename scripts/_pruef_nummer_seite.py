import re, sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from farzona_split import lines_of, OUT
V, von, bis, off = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
ok, bad = [], []
for p in range(von, bis + 1):
    ls = lines_of(OUT / V / f"p{p:04d}.tsv")
    top = " ".join(l["text"] for l in ls[:3])
    nums = [int(x) for x in re.findall(r"\d{1,3}", top)]
    (ok if p - off in nums else bad).append((p, top[:25]))
print("passend", len(ok), "| ohne passende Nummer:", bad)
for p in [int(x) for x in sys.argv[5:]]:
    print(p, [l["text"][:25] for l in lines_of(OUT / V / f"p{p:04d}.tsv")[:2]])
