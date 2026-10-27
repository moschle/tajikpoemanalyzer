#!/usr/bin/python3
"""Zerlegt die OCR-Seiten (TSV) der Farzona-Baende in Gedichte.
Grenzen: Zier-Trenner (* * *, Ornamente = Zeilen ohne verlaessliche Woerter) und Titelzeilen
(Grossbuchstaben). Seitenumbrueche trennen nicht. Seitenzahlen, Inhaltsverzeichnis,
Impressum und Prosa (Vorworte) werden verworfen.
Ausgabe: data/ocr_farzona/gedichte/<ordner>.jsonl  (lokal, gitignored)"""
import csv, json, re, statistics, sys
from pathlib import Path

OUT = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona"
DEST = OUT / "gedichte"
WORD = re.compile(r"[А-Яа-яЁёҒғӢӣҚқӮӯҲҳҶҷ]{2,}")
TOC = re.compile(r"\.{4,}\s*\d+|\s\d{1,3}\s*$")
STOP = re.compile(r"МУНДАРИҶА|Мундариҷа|ФЕҲРИСТ|Фењрист|Феҳрист")
IMPR = re.compile(r"ББК|УДК|ISBN|ІЅВК|Адади нашр|Теъдод|Супориши|Ба чоп|Ба матбаа|Ҷузъи|нусха")

def lines_of(tsv):
    rows = {}
    with open(tsv, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r.get("level") != "5" or not (r.get("text") or "").strip():
                continue
            k = (int(r["block_num"]), int(r["par_num"]), int(r["line_num"]))
            rows.setdefault(k, []).append((int(r["left"]), int(r["top"]), int(r["height"]), float(r["conf"]), r["text"]))
    out = []
    for k, ws in rows.items():
        ws.sort()
        good = [w for w in ws if w[3] >= 60 and WORD.search(w[4])]
        out.append({"top": min(w[1] for w in ws), "h": statistics.median(w[2] for w in ws),
                    "text": " ".join(w[4] for w in ws), "n": len(ws), "good": len(good),
                    "conf": sum(w[3] for w in ws) / len(ws)})
    out.sort(key=lambda l: l["top"])
    return out

def is_title(l):
    letters = [c for c in l["text"] if c.isalpha()]
    return len(letters) >= 3 and sum(c.isupper() for c in letters) / len(letters) > 0.8 and l["n"] <= 6

def split(ordner, pages):
    poems, cur, title, stopped = [], [], None, False
    def flush():
        nonlocal cur, title
        body = [x for x in cur]
        while body and body[-1] == "":
            body.pop()
        verse = [x for x in body if x]
        if len(verse) >= 2:
            avg = sum(len(x.split()) for x in verse) / len(verse)
            if avg <= 11:  # laengere Zeilen = Prosa (Vorwort, Nachwort)
                poems.append({"title": title, "lines": body, "page": page_start})
        cur, title = [], None
    page_start = None
    cache = {}
    for p in range(1, pages + 1):
        tsv = OUT / ordner / f"p{p:04d}.tsv"
        if tsv.exists():
            cache[p] = lines_of(tsv)
    ends = sorted(max(l["top"] for l in ls if l["good"] >= 2) for ls in cache.values()
                  if any(l["good"] >= 2 for l in ls))
    full = ends[int(len(ends) * 0.9)] if ends else 0   # Unterkante Satzspiegel
    for p in range(1, pages + 1):
        if p not in cache:
            continue
        ls = cache[p]
        prev = cache.get(p - 1)
        if prev and cur:
            pe = [l["top"] for l in prev if l["good"] >= 2]
            if pe and max(pe) < 0.85 * full:
                flush()                       # Vorseite nicht voll: Gedicht endete dort
        if p > pages * 0.8 and any(STOP.search(l["text"]) and l["n"] <= 2 for l in ls):
            stopped = True
        if stopped:
            continue
        gaps = [b["top"] - a["top"] for a, b in zip(ls, ls[1:])]
        step = statistics.median(gaps) if gaps else 0
        prev_top = None
        for i, l in enumerate(ls):
            t = l["text"].strip()
            if re.fullmatch(r"[\d\s\-–—•.)(]+", t):
                if i < len(ls) - 1:
                    flush(); prev_top = None          # Gedichtnummer
                continue                              # sonst Seitenzahl
            if IMPR.search(t) or TOC.search(t) and l["n"] > 3:
                continue
            if l["good"] == 0 or (l["good"] < 2 and l["conf"] < 55) or (l["n"] <= 3 and re.search(r"\d", t)):
                flush(); prev_top = None; continue          # Ornament / Trenner
            if is_title(l):
                flush(); title = t; page_start = p; prev_top = l["top"]; continue
            if prev_top is not None and step and l["top"] - prev_top > 1.7 * step and cur:
                cur.append("")                                # Strophenumbruch
            if not cur:
                page_start = p
            cur.append(t)
            prev_top = l["top"]
    flush()
    return poems

def main():
    only = sys.argv[1:] or None
    DEST.mkdir(exist_ok=True)
    with open(OUT / "baende.csv", encoding="utf-8") as f:
        baende = [r for r in csv.DictReader(f) if not only or r["ordner"] in only]
    total = 0
    for r in baende:
        poems = split(r["ordner"], int(r["seiten"]))
        with open(DEST / f"{r['ordner']}.jsonl", "w", encoding="utf-8") as f:
            for i, pm in enumerate(poems, 1):
                pm["nr"] = i
                f.write(json.dumps(pm, ensure_ascii=False) + "\n")
        n_lines = [len([x for x in pm["lines"] if x]) for pm in poems]
        total += len(poems)
        print(f"{r['ordner']}: {len(poems)} Gedichte, Zeilen median {statistics.median(n_lines) if n_lines else 0}, "
              f"mit Titel {sum(1 for pm in poems if pm['title'])}")
    print("SUMME", total)

if __name__ == "__main__":
    main()
