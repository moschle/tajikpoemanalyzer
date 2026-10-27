#!/usr/bin/python3
"""Liest die Inhaltsverzeichnisse der Farzona-Baende.
- TOC-Bereich: ab Seite mit Ueberschrift (Мундариҷа/Феҳрист) bis Bandende, Impressum ausgenommen.
- Eintrag: Zeile mit Woertern, die auf eine Seitenzahl endet (Punktlinien optional).
- Versatz PDF-Seite -> Druckseite aus den Seitenzahlen am Seitenfuss.
Ausgabe: data/ocr_farzona/toc/<ordner>.json  [{titel, druckseite, pdfseite}]"""
import csv, json, re, statistics, sys
from collections import Counter
from pathlib import Path
OUT = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona"
HEAD = re.compile(r"МУНДАРИҶА|МУНДАРИЧА|ФЕҲРИСТ|ФЕХРИСТ", re.I)
CYR = re.compile(r"[А-Яа-яЁёҒғӢӣҚқӮӯҲҳҶҷ]{2,}")
TAIL = re.compile(r"^(?P<t>.+?)[\s.…·,:;_\-–—»«\"'|]*?(?P<p>\d{1,3})[\s\W]{0,4}$")
LEAD = re.compile(r"(\.\s?){3,}|…{2,}|·{3,}")
IMPR = re.compile(r"ББК|УДК|ISBN|Адади нашр|Теъдод|Супориши|Ба чоп|Ба матбаа|Ҷузъи|нусха|Муҳаррир|Мусаҳҳеҳ|Ороиш")

GARB = re.compile(r"[аоеихнрвзктсуАОХ.,:;]{7,}")

def tsv_lines(tsv):
    rows = {}
    with open(tsv, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r.get("level") == "5" and (r.get("text") or "").strip():
                k = (int(r["block_num"]), int(r["par_num"]), int(r["line_num"]))
                rows.setdefault(k, []).append((int(r["left"]), int(r["top"]), float(r["conf"]), r["text"]))
    out = [sorted(ws) for ws in rows.values()]
    out.sort(key=lambda ws: min(w[1] for w in ws))
    return [[(w[2], w[3]) for w in ws] for ws in out]

def offset(d, n):
    diffs = Counter()
    for p in range(1, n + 1):
        t = d / f"p{p:04d}.txt"
        if not t.exists():
            continue
        ls = [l.strip() for l in t.read_text(encoding="utf-8").splitlines() if l.strip()]
        for l in ls[-2:] + ls[:1]:
            m = re.fullmatch(r"\W*(\d{1,3})\W*", l)
            if m and 0 <= p - int(m.group(1)) < 20:
                diffs[p - int(m.group(1))] += 1
    return diffs.most_common(1)[0][0] if diffs else None, sum(diffs.values())

def main():
    show = "-v" in sys.argv
    (OUT / "toc").mkdir(exist_ok=True)
    with open(OUT / "baende.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d, n = OUT / r["ordner"], int(r["seiten"])
            off, belege = offset(d, n)
            head, region = None, []
            for p in range(int(n * 0.6), n + 1):
                t = d / f"p{p:04d}.txt"
                if not t.exists():
                    continue
                ls = [l.strip() for l in t.read_text(encoding="utf-8").splitlines() if l.strip()]
                if head is None and any(HEAD.search(l) and len(l.split()) <= 4 for l in ls):
                    head = p
                lead = sum(bool(LEAD.search(l)) for l in ls)
                numend = sum(bool(re.search(r"\d{1,3}\W{0,3}$", l)) for l in ls)
                if head is not None:
                    if p >= head and lead >= 2:
                        region.append(p)
                elif ls and lead >= 4 and lead >= 0.3 * len(ls):
                    region.append(p)
            if head is not None:
                region = [p for p in region if p >= head]
            entries = []
            for p in region:
                for words in tsv_lines(d / f"p{p:04d}.tsv"):
                    l = " ".join(w[1] for w in words)
                    if IMPR.search(l) or HEAD.search(l):
                        continue
                    titel = []
                    for c, w in words:
                        if LEAD.search(w) or GARB.fullmatch(w) or c < 50:
                            break
                        titel.append(w)
                    titel = " ".join(titel).strip(" .…·_-–—,")
                    if len(CYR.findall(titel)) < 1 or len(titel) < 4:
                        continue
                    num = re.fullmatch(r"\W*(\d{1,3})\W*", words[-1][1])
                    dp = int(num.group(1)) if num else None
                    letters = [ch for ch in titel if ch.isalpha()]
                    sektion = sum(ch.isupper() for ch in letters) / len(letters) > 0.8 and dp is None
                    entries.append({"titel": titel, "druckseite": dp, "tocseite": p, "sektion": sektion,
                                    "pdfseite": dp + off if dp is not None and off is not None else None})
            sek = [e for e in entries if e["sektion"]]
            entries_g = [e for e in entries if not e["sektion"]]
            nums = [e["druckseite"] for e in entries_g if e["druckseite"] is not None]
            mono = sum(1 for a, b in zip(nums, nums[1:]) if b >= a)
            json.dump({"versatz": off, "kopf": head, "eintraege": entries},
                      open(OUT / "toc" / f"{r['ordner']}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"{r['ordner']}: Versatz {off} ({belege} Belege), TOC ab S.{head}, TOC-Seiten {region[:1]}-{region[-1:]} ({len(region)}), Eintraege {len(entries_g)} + {len(sek)} Abschnitte, mit Seitenzahl {len(nums)}, aufsteigend {mono}/{max(len(nums)-1,0)}")
            if show:
                print("      Abschnitte:", " | ".join(e["titel"][:30] for e in sek)[:400])

if __name__ == "__main__":
    main()
