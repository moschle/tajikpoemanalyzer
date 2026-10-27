#!/usr/bin/python3
"""Zerlegt die OCR-Seiten (TSV) der Farzona-Baende in Gedichte.

Phase 1 – Zeilenstrom: jede Seite wird zu Ereignissen (Zeile, Titel, Trenner, Strophe).
  Trenner: Ornamente (* * *), Gedichtnummern, Seite endet vor Satzspiegel-Ende.
Phase 2 – Anker aus dem Inhaltsverzeichnis (scripts/farzona_toc.py): jeder Eintrag wird in
  Reihenfolge unscharf im Strom gesucht; ein Treffer ist eine feste Grenze (und ggf. Titel).
Phase 3 – Segmentierung; Prosa (Vorwort, Biographie) und Abschnitt ТАРҶУМАҲО werden markiert.
Ausgabe: data/ocr_farzona/gedichte/<ordner>.jsonl (lokal, gitignored) + Kennzahlen."""
import csv, json, re, statistics, sys
from difflib import SequenceMatcher
from pathlib import Path

OUT = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona"
DEST = OUT / "gedichte"
WORD = re.compile(r"[А-Яа-яЁёҒғӢӣҚқӮӯҲҳҶҷ]{2,}")
TOCL = re.compile(r"(\.\s?){4,}|…{2,}")
IMPR = re.compile(r"ББК|УДК|ISBN|ІЅВК|Адади нашр|Теъдод|Супориши|Ба чоп|Ба матбаа|Ҷузъи|нусха")
TRANSL = re.compile(r"ТАРҶУМАҲО|ТАРҶУМА|Тарҷумаҳо")
# Uebersetzungsteile (Stichprobe 27.10.2026): Найсон ab S. 213 (Ли Бо, Haiku), Себарга ab S. 236
# (Trennblatt ТАРҶУМАҲО; datierte Gedichte 1917–1941, Abai ab S. 376; Ende ab S. 385 unsicher).
UEBERSETZUNG_AB = {"ФАРЗОНА_НАЙСОН": 213, "ФАРЗОНА_СЕБАРГА": 236}

def lines_of(tsv):
    rows = {}
    with open(tsv, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r.get("level") != "5" or not (r.get("text") or "").strip():
                continue
            k = (int(r["block_num"]), int(r["par_num"]), int(r["line_num"]))
            rows.setdefault(k, []).append((int(r["left"]), int(r["top"]), int(r["height"]), float(r["conf"]), r["text"]))
    out = []
    for ws in rows.values():
        ws.sort()
        good = [w for w in ws if w[3] >= 60 and WORD.search(w[4])]
        good3 = [w for w in good if re.search(r"[А-Яа-яЁёҒғӢӣҚқӮӯҲҳҶҷ]{3,}", w[4])]
        out.append({"top": min(w[1] for w in ws), "text": " ".join(w[4] for w in ws), "n": len(ws),
                    "good": len(good), "good3": len(good3), "conf": sum(w[3] for w in ws) / len(ws)})
    out.sort(key=lambda l: l["top"])
    return out

def is_title(l):
    letters = [c for c in l["text"] if c.isalpha()]
    return len(letters) >= 3 and sum(c.isupper() for c in letters) / len(letters) > 0.8 and l["n"] <= 6

def norm(s):
    return re.sub(r"[^а-яёғӣқӯҳҷ]", "", s.lower())

def reim(t):
    """Reimklang: letzte drei Buchstaben (deckt Radif und Qāfiya ab)."""
    k = norm(t)
    return k[-3:] if len(k) >= 3 else None

def neues_ghasel(prev_lines, cur_lines):
    """Neue Seite beginnt mit einem Matlaʿ auf anderen Reim als die Vorseite."""
    from collections import Counter
    pv = [reim(l["text"]) for l in prev_lines if l["good3"] >= 2][-8:]
    cv = [reim(l["text"]) for l in cur_lines if l["good3"] >= 2][:2]
    if len(pv) < 4 or len(cv) < 2 or not cv[0] or cv[0] != cv[1]:
        return False
    dom, n = Counter(x for x in pv if x).most_common(1)[0] if any(pv) else (None, 0)
    return n >= 3 and dom != cv[0]

# ---------------------------------------------------------------- Phase 1
def headers(cache):
    """Kolumnentitel: Text der ersten/letzten Zeilen, der auf vielen Seiten wiederkehrt."""
    from collections import Counter
    c = Counter()
    for ls in cache.values():
        for k in {norm(l["text"]) for l in ls[:2] + ls[-2:] if l["good"] >= 1}:
            if len(k) >= 5:
                c[k] += 1
    return {k for k, v in c.items() if v >= max(5, 0.08 * len(cache))}

def stream(ordner, pages, toc_pages, versatz=None, vierzeiler=False):
    cache = {p: lines_of(OUT / ordner / f"p{p:04d}.tsv") for p in range(1, pages + 1)
             if (OUT / ordner / f"p{p:04d}.tsv").exists()}
    head = headers(cache)
    ends = sorted(max(l["top"] for l in ls if l["good"] >= 2) for ls in cache.values() if any(l["good"] >= 2 for l in ls))
    full = ends[int(len(ends) * 0.9)] if ends else 0
    ev = []                                   # (typ, text, page)
    for p in sorted(cache):
        if p in toc_pages:
            continue
        ls = [l for l in cache[p] if not (l["good"] >= 1 and norm(l["text"]) in head)]
        prev = cache.get(p - 1)
        if prev:
            pe = [l["top"] for l in prev if l["good"] >= 2]
            if pe and max(pe) < 0.85 * full:
                ev.append(("PBREAK", "", p))       # Vorseite nicht voll
            elif neues_ghasel(prev, ls):
                ev.append(("BREAK", "", p))        # neuer Reim mit Matlaʿ
        ev.append(("PAGE", "", p))
        gaps = [b["top"] - a["top"] for a, b in zip(ls, ls[1:])]
        step = statistics.median(gaps) if gaps else 0
        prev_top = None
        for i, l in enumerate(ls):
            t = l["text"].strip()
            if re.fullmatch(r"[\d\s\-–—•.)(]+", t):
                num = int(re.sub(r"\D", "", t) or -1)
                seitenzahl = versatz is not None and abs(num - (p - versatz)) <= 1
                if not seitenzahl and i < len(ls) - 1:
                    ev.append(("BREAK", "", p))       # Gedichtnummer
                prev_top = None
                continue
            if IMPR.search(t) or (TOCL.search(t) and l["n"] > 3):
                continue
            w3 = re.findall(r"[А-Яа-яЁёҒғӢӣҚқӮӯҲҳҶҷ]{3,}", t)
            verslike = (len(w3) >= 2 and len(WORD.findall(t)) >= 0.6 * l["n"]) or \
                bool(re.search(r"[А-Яа-яӣӯҳқҷғ]{3,}[!?.,:»]", t))
            noise = (not verslike and l["good3"] == 0 and (l["good"] == 0 or (l["n"] <= 3 and l["conf"] < 55))) \
                or (l["n"] <= 3 and l["good3"] == 0 and re.search(r"\d", t))
            if noise:
                ev.append(("BREAK", "", p)); prev_top = None; continue
            if is_title(l):
                ev.append(("TITLE", t, p)); prev_top = l["top"]; continue
            if prev_top is not None and step and l["top"] - prev_top > 3.0 * step:
                ev.append(("BREAK", "", p))          # unerkannter Trenner (* * *)
            elif prev_top is not None and step and l["top"] - prev_top > 1.7 * step:
                ev.append(("STANZA", "", p))
            ev.append(("LINE", t, p)); prev_top = l["top"]
    return ev

# ---------------------------------------------------------------- Phase 2
def anchor(ev, toc, window=600):
    """Sucht TOC-Eintraege der Reihe nach im Strom. Rueckgabe: Index -> Eintrag."""
    cand = [i for i, e in enumerate(ev) if e[0] in ("LINE", "TITLE")]
    keys = {i: norm(ev[i][1]) for i in cand}
    hits, pos = {}, 0
    for e in toc:
        k = norm(e["titel"])
        if len(k) < 5:
            continue
        best, bi = 0.0, None
        start = next((j for j, i in enumerate(cand) if i >= pos), len(cand))
        for i in cand[start:start + window]:
            s = keys[i][:len(k) + 4]
            if not s:
                continue
            r = SequenceMatcher(None, k, s).ratio()
            if r > best:
                best, bi = r, i
                if r > 0.95:
                    break
        if bi is not None and best >= 0.78:
            hits[bi] = e
            pos = bi + 1
    return hits

# ---------------------------------------------------------------- Phase 3
def segment(ev, hits, vierzeiler=False):
    poems, cur, title, page, sect = [], [], None, None, None
    def flush():
        nonlocal cur, title
        body = list(cur)
        while body and body[-1] == "":
            body.pop()
        verse = [x for x in body if x]
        if len(verse) >= 2 or (verse and title):
            avg = sum(len(x.split()) for x in verse) / len(verse)
            poems.append({"title": title, "lines": body, "page": page, "abschnitt": sect,
                          "prosa": avg > 11, "anker": anchored})
        cur, title = [], None
    anchored, pend = False, False
    for i, (typ, t, p) in enumerate(ev):
        if i in hits:
            flush(); anchored = True; page = p; pend = False
            if typ == "TITLE":
                title = t; continue
        if typ == "PBREAK":
            pend = bool(cur); continue
        if typ == "LINE" and pend:
            pend = False
            first = next((c for c in t if c.isalpha()), "")
            if not first.islower():
                flush(); anchored = False       # sonst: Fortsetzung mit Kleinbuchstaben
        if typ in ("BREAK", "TITLE"):
            pend = False
        if typ == "PAGE":
            n_v = len([x for x in cur if x])
            if vierzeiler and n_v >= 4 and n_v % 4 == 0:
                flush(); anchored = False          # Rubāʿī endet am Seitenende
            continue
        if typ == "BREAK":
            if cur:
                flush(); anchored = False
        elif typ == "TITLE":
            if TRANSL.search(t) or (t.isupper() and len(t.split()) <= 4 and not cur and title):
                sect = t if TRANSL.search(t) or len(t) > 3 else sect
            if cur:
                flush(); anchored = False
            title, page = t, p
        elif typ == "STANZA":
            if cur:
                cur.append("")
        else:
            if not cur and title is None:
                page = p
            elif not cur:
                page = page or p
            cur.append(t)
    flush()
    # Ein Gedicht beginnt nie mit Kleinbuchstaben: ohne Anker/Titel an das vorige haengen.
    out = []
    for pm in poems:
        v = [x for x in pm["lines"] if x]
        first = next((c for c in (v[0] if v else "") if c.isalpha()), "")
        if out and first.islower() and not pm["anker"] and not pm["title"]:
            out[-1]["lines"] += pm["lines"]
        else:
            out.append(pm)
    return out

def main():
    only = sys.argv[1:] or None
    DEST.mkdir(exist_ok=True)
    with open(OUT / "baende.csv", encoding="utf-8") as f:
        baende = [r for r in csv.DictReader(f) if not only or r["ordner"] in only]
    total = 0
    for r in baende:
        tf = OUT / "toc" / f"{r['ordner']}.json"
        toc = json.load(open(tf, encoding="utf-8")) if tf.exists() else {"eintraege": []}
        entries = [e for e in toc["eintraege"] if not e.get("sektion")]
        toc_pages = {e["tocseite"] for e in toc["eintraege"]}
        ev = stream(r["ordner"], int(r["seiten"]), toc_pages, toc.get("versatz"))
        hits = anchor(ev, entries)
        poems = [pm for pm in segment(ev, hits) if not pm["prosa"]]
        med = statistics.median(len([x for x in pm["lines"] if x]) for pm in poems) if poems else 0
        if med == 4:
            poems = [pm for pm in segment(ev, hits, vierzeiler=True) if not pm["prosa"]]
        ab = UEBERSETZUNG_AB.get(r["ordner"])
        for pm in poems:
            pm["uebersetzung"] = bool(ab and pm["page"] and pm["page"] >= ab)
        with open(DEST / f"{r['ordner']}.jsonl", "w", encoding="utf-8") as f:
            for i, pm in enumerate(poems, 1):
                pm["nr"] = i
                f.write(json.dumps(pm, ensure_ascii=False) + "\n")
        total += len(poems)
        n_l = [len([x for x in pm["lines"] if x]) for pm in poems]
        tr = sum(1 for pm in poems if pm["uebersetzung"])
        print(f"{r['ordner']}: {len(poems)} Gedichte (TOC {len(entries)}, Anker {len(hits)} = "
              f"{100*len(hits)/max(len(entries),1):.0f}%), Zeilen median {statistics.median(n_l) if n_l else 0}"
              + (f", im Abschnitt Übersetzungen {tr}" if tr else ""))
    print("SUMME", total)

if __name__ == "__main__":
    main()
