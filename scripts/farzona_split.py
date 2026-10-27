#!/usr/bin/python3
"""Zerlegt die OCR-Seiten (TSV) der Farzona-Baende in Gedichte.

Phase 1 – Zeilenstrom: jede Seite wird zu Ereignissen (Zeile, Titel, Trenner, Strophe, Nummer).
Phase 2 – Anker aus dem Inhaltsverzeichnis (scripts/farzona_toc.py): feste Gedichtanfaenge.
Phase 3 – Segmentierung mit verzoegertem Trennen: ein Trenner wirkt erst an der naechsten Verszeile
  und entfaellt, wenn diese Zeile eine Fortsetzung ist (Kleinbuchstabe oder Korrektur "weiter").
Korrekturen aus der Seitenpruefung: data/ocr_farzona/korrekturen.json
  {ordner: [{"s": seite, "z": "Zeilenanfang", "a": "neu"|"weiter"|"titel"|"weg"}]}
  "z" wird normalisiert verglichen (nur Buchstaben, Praefix).
Ausgabe: data/ocr_farzona/gedichte/<ordner>.jsonl (lokal, gitignored)."""
import csv, json, re, statistics, sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

OUT = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona"
DEST = OUT / "gedichte"
KORR = OUT / "korrekturen.json"
CYRL = r"А-Яа-яЁёҒғӢӣҚқӮӯҲҳҶҷ"
WORD = re.compile(rf"[{CYRL}]{{2,}}")
W3 = re.compile(rf"[{CYRL}]{{3,}}")
TOCL = re.compile(r"(\.\s?){4,}|…{2,}")
IMPR = re.compile(r"ББК|УДК|ISBN|ІЅВК|Адади нашр|Теъдод|Супориши|Ба чоп|Ба матбаа|Ҷузъи|нусха")
# Uebersetzungsteile (Stichprobe 27.10.2026): Найсон ab S. 213 (Ли Бо, Haiku, Goethe), Себарга ab S. 236
# (Trennblatt ТАРҶУМАҲО; datierte Gedichte 1911–1941, Abai ab S. 376; Ende ab S. 385 unsicher).
UEBERSETZUNG_AB = {"ФАРЗОНА_НАЙСОН": 213, "ФАРЗОНА_СЕБАРГА": 236}
# Reimwechsel als Gedichtgrenze nur in Ghaselbaenden ohne Titel (in Strophengedichten wechselt der Reim).
GHASEL_BAENDE = {"ФАРЗОНАИ_ХУҶАНДӢ_ДЕВОН_Панҷсад_ғазали_дилангез", "ФАРЗОНА_САД_БАРГИ_ҒАЗАЛ", "ФАРЗОНА_САДУ_ЯК_ҒАЗАЛ"}

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
        out.append({"top": min(w[1] for w in ws), "text": " ".join(w[4] for w in ws), "n": len(ws),
                    "good": len(good), "good3": sum(1 for w in good if W3.search(w[4])),
                    "conf": sum(w[3] for w in ws) / len(ws)})
    out.sort(key=lambda l: l["top"])
    return out

def is_title(l):
    letters = [c for c in l["text"] if c.isalpha()]
    return len(letters) >= 3 and sum(c.isupper() for c in letters) / len(letters) > 0.8 and l["n"] <= 8

def norm(s):
    return re.sub(r"[^а-яёғӣқӯҳҷ]", "", s.lower())

def reim(t):
    k = norm(t)
    return k[-3:] if len(k) >= 3 else None

def neues_ghasel(prev_lines, cur_lines):
    """Neue Seite beginnt mit einem Matlaʿ auf anderen Reim als die Vorseite."""
    pv = [reim(l["text"]) for l in prev_lines if l["good3"] >= 2][-8:]
    cv = [reim(l["text"]) for l in cur_lines if l["good3"] >= 2][:2]
    if len(pv) < 4 or len(cv) < 2 or not cv[0] or cv[0] != cv[1]:
        return False
    c = Counter(x for x in pv if x)
    if not c:
        return False
    dom, n = c.most_common(1)[0]
    return n >= 3 and dom != cv[0]

def headers(cache):
    """Kolumnentitel: Text der ersten/letzten Zeilen, der auf vielen Seiten wiederkehrt."""
    c = Counter()
    for ls in cache.values():
        for k in {norm(l["text"]) for l in ls[:2] + ls[-2:] if l["good"] >= 1}:
            if len(k) >= 5:
                c[k] += 1
    return {k for k, v in c.items() if v >= max(5, 0.08 * len(cache))}

# ---------------------------------------------------------------- Phase 1
def stream(ordner, pages, toc_pages, versatz=None, weg=()):
    cache = {p: lines_of(OUT / ordner / f"p{p:04d}.tsv") for p in range(1, pages + 1)
             if (OUT / ordner / f"p{p:04d}.tsv").exists()}
    head = headers(cache)
    ends = sorted(max(l["top"] for l in ls if l["good"] >= 2) for ls in cache.values() if any(l["good"] >= 2 for l in ls))
    full = ends[int(len(ends) * 0.9)] if ends else 0
    ev = []                                   # (typ, text, page)
    for p in sorted(cache):
        if p in toc_pages or p in weg:
            continue
        ls = [l for l in cache[p] if not (l["good"] >= 1 and norm(l["text"]) in head)]
        # Kolumnentitel mit OCR-Rauschen ("СЕБАРГА б", "ФАРЗОНА 25"): erste Zeile, kurz, beginnt mit einem Kopfwort
        while ls and len(ls[0]["text"].split()) <= 3 and any(
                len(k) >= 6 and norm(ls[0]["text"]).startswith(k) and len(norm(ls[0]["text"])) <= len(k) + 3 for k in head):
            ls = ls[1:]
        prev = cache.get(p - 1)
        if prev:
            pe = [l["top"] for l in prev if l["good"] >= 2]
            if pe and max(pe) < 0.85 * full:
                ev.append(("PBREAK", "", p))
            elif ordner in GHASEL_BAENDE and neues_ghasel(prev, ls):
                ev.append(("BREAK", "reim", p))
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
                    ev.append(("NUM", str(num), p))
                prev_top = None
                continue
            if (IMPR.search(t) and re.search(r"\d", t)) or (TOCL.search(t) and l["n"] > 3):
                continue
            if re.match(rf"^\s*[1-9¹²³*!|]\s*[{CYRL}]", t) and len(W3.findall(t)) >= 2 and prev_top is not None and step and \
                    l["top"] - prev_top > 2.5 * step:
                break                                  # Fussnote: Rest der Seite verwerfen
            if re.match(r"^\s*\S?\s*([хХxX*жЖ]\s*){2,3}\W*$", t) or re.match(r"^\s*[«»]\s*[хХxX][еЕe]?\s*$", t) \
                    or (re.fullmatch(r"[\s*жЖхХоОеЕйxX.«»]+", t) and 2 <= len(re.sub(r"[\s.*«»]", "", t)) <= 5):
                ev.append(("BREAK", "sterne", p)); prev_top = None; continue   # * * * als "3 хх"
            if re.match(r"^\s*[-—–]", t) and re.search(r"[-—–]{2,}\s*$|»\s*[-—–]", t) and l["good3"] <= 1:
                continue                           # Fusszierleiste mit Seitenzahl: still verwerfen
            if re.search(rf"[{CYRL}]{{18,}}", t) and l["good3"] <= 1:
                ev.append(("BREAK", "ornament", p)); prev_top = None; continue   # OCR einer Zierleiste
            w3 = W3.findall(t)
            verslike = (len(w3) >= 2 and len(WORD.findall(t)) >= 0.6 * l["n"]) or \
                bool(re.search(rf"[{CYRL}]{{3,}}[!?.,:»]", t))
            noise = (not verslike and l["good3"] == 0 and (l["good"] == 0 or (l["n"] <= 3 and l["conf"] < 55))) \
                or (l["n"] <= 3 and l["good3"] == 0 and re.search(r"\d", t))
            if ordner in GHASEL_BAENDE and i == 0 and l["n"] <= 3:
                noise = True                       # Ornament mit Ghaselnummer ueber dem Text
            if noise:
                ev.append(("BREAK", "ornament", p)); prev_top = None; continue
            if is_title(l):
                if l["good3"] >= 1 and l["conf"] >= 60:
                    ev.append(("TITLE", t, p)); prev_top = l["top"]
                else:
                    ev.append(("BREAK", "ornament", p)); prev_top = None
                continue
            if prev_top is not None and step and l["top"] - prev_top > 3.0 * step:
                ev.append(("BREAK", "abstand", p))
            elif prev_top is not None and step and l["top"] - prev_top > 1.7 * step:
                ev.append(("STANZA", "", p))
            ev.append(("LINE", t, p)); prev_top = l["top"]
    return ev

# ---------------------------------------------------------------- Phase 2
def anchor(ev, toc, window=600, nur_block=False):
    # nur_block: Anker nur an Blockanfaengen (Titelzeile oder erste Zeile nach Seiten-/Strophen-/Ornamentgrenze)
    cand = [i for i, e in enumerate(ev) if e[0] == "TITLE" or (e[0] == "LINE" and (
        not nur_block or i == 0 or ev[i - 1][0] != "LINE"))]
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
def korrektur(korr, p, t, used):
    """Korrektur fuer Zeile t auf Seite p (unscharf ueber die ersten 18 Buchstaben); jede nur einmal."""
    k = norm(t)[:18]
    for j, c in enumerate(korr):
        if j in used or c["s"] != p or not c.get("z"):
            continue
        z = norm(c["z"])[:18]
        if k.startswith(z) or (len(z) >= 8 and SequenceMatcher(None, z, k[:len(z)]).ratio() >= 0.8):
            used.add(j)
            return c
    return None

def segment(ev, hits, korr, vierzeiler=False):
    poems, cur, title, tpage = [], [], None, None
    pending, anchored, num = False, False, None
    pend_num, hart = None, False
    used = set()
    neu_seite = {c["s"] for c in korr if c["a"] == "neu_seite"}
    neu_seite_done = set()
    rest_weg = set()
    def flush():
        nonlocal cur, title, tpage, anchored, num
        body = list(cur)
        while body and body[-1][0] == "":
            body.pop()
        verse = [x for x in body if x[0]]
        if len(verse) >= 2 or (verse and title):
            avg = sum(len(x[0].split()) for x in verse) / len(verse)
            poems.append({"title": title, "lines": [x[0] for x in body], "lpages": [x[1] for x in body],
                          "page": tpage or verse[0][1], "prosa": avg > 11, "anker": anchored, "nummer": num})
        cur, title, tpage, anchored, num = [], None, None, False, None
    for i, (typ, t, p) in enumerate(ev):
        if typ == "PAGE":
            n_v = len([x for x in cur if x[0]])
            if vierzeiler and n_v >= 4 and n_v % 4 == 0:
                pending = True
            continue
        if typ in ("BREAK", "PBREAK"):
            pending = pending or bool(cur)
            continue
        if typ == "NUM":
            pending = pending or bool(cur)
            hart = hart or bool(cur)
            pend_num = int(t)
            continue
        if typ == "STANZA":
            if cur and not pending:
                cur.append(("", p))
            continue
        if p in rest_weg:
            continue
        c = korrektur(korr, p, t, used)
        a = c["a"] if c else None
        if a == "ab_weg":
            rest_weg.add(p)
            continue
        if a == "weg":
            continue
        if a == "neu_seite":
            a = None
        if typ == "TITLE" and a == "vers":
            typ = "LINE"
        elif typ == "TITLE" or a == "titel":
            if cur:
                flush()
            title, tpage, pending = t, p, False
            anchored = i in hits
            continue
        # LINE
        first = next((c for c in t if c.isalpha()), "")
        seitenanfang = p in neu_seite and p not in neu_seite_done
        if seitenanfang:
            neu_seite_done.add(p)
        weiter = a in ("weiter", "vers") or (first.islower() and i not in hits and a != "neu" and not seitenanfang
                                             and not hart)
        neu = a == "neu" or (i in hits and a not in ("weiter", "vers")) or seitenanfang
        if cur and (neu or (pending and not weiter)):
            keep_title = title if not [x for x in cur if x[0]] else None
            flush()
            if keep_title:
                title = keep_title
            num = pend_num
        elif not cur and pend_num is not None:
            num = pend_num
        pend_num, hart = None, False
        if c and c.get("titel"):
            title, tpage = c["titel"], p
        if i in hits:
            anchored = True
        pending = False
        if not cur and tpage is None:
            tpage = p
        cur.append((t, p))
    flush()
    return poems

def epigraphe(poems):
    """Ghaselbaende: Bloecke unter 4 Versen sind Epigraph/Widmung des folgenden Ghasels."""
    out, vor = [], None
    for pm in poems:
        n = len([x for x in pm["lines"] if x])
        if vor is not None:
            pm["lines"] = vor["lines"] + pm["lines"]
            pm["lpages"] = vor["lpages"] + pm["lpages"]
            pm["page"] = min(pm["page"], vor["page"])
            pm["title"] = pm["title"] or vor["title"]
            vor = None
            n = len([x for x in pm["lines"] if x])
        if n < 4 and not pm["anker"]:
            vor = pm
            continue
        out.append(pm)
    if vor is not None and out:
        out[-1]["lines"] += vor["lines"]; out[-1]["lpages"] += vor["lpages"]
    return out

def load_korr():
    return json.load(open(KORR, encoding="utf-8")) if KORR.exists() else {}

def split_band(r, korr_all=None):
    korr_all = korr_all if korr_all is not None else load_korr()
    tf = OUT / "toc" / f"{r['ordner']}.json"
    toc = json.load(open(tf, encoding="utf-8")) if tf.exists() else {"eintraege": []}
    entries = [e for e in toc["eintraege"] if not e.get("sektion")]
    toc_pages = {e["tocseite"] for e in toc["eintraege"]}
    hand = OUT / "toc_hand" / f"{r['ordner']}.txt"     # am Bild abgeschriebenes Verzeichnis ersetzt das OCR-Verzeichnis
    if hand.exists():
        entries = [{"titel": l.split("|", 1)[1], "seite": l.split("|", 1)[0]}
                   for l in hand.read_text(encoding="utf-8").splitlines() if "|" in l]
    korr = korr_all.get(r["ordner"], [])
    weg = {c["s"] for c in korr if c["a"] == "seite_weg"}
    ev = stream(r["ordner"], int(r["seiten"]), toc_pages, toc.get("versatz"), weg)
    hits = anchor(ev, entries, nur_block=hand.exists())
    poems = [pm for pm in segment(ev, hits, korr) if not pm["prosa"]]
    med = statistics.median(len([x for x in pm["lines"] if x]) for pm in poems) if poems else 0
    if med == 4:
        poems = [pm for pm in segment(ev, hits, korr, vierzeiler=True) if not pm["prosa"]]
    if r["ordner"] in GHASEL_BAENDE:
        poems = epigraphe(poems)
    ab = UEBERSETZUNG_AB.get(r["ordner"])
    for i, pm in enumerate(poems, 1):
        pm["nr"] = i
        pm["uebersetzung"] = bool(ab and pm["page"] >= ab)
    return poems, entries, hits

def main():
    only = sys.argv[1:] or None
    DEST.mkdir(exist_ok=True)
    korr_all = load_korr()
    with open(OUT / "baende.csv", encoding="utf-8") as f:
        baende = [r for r in csv.DictReader(f) if not only or r["ordner"] in only]
    total = 0
    for r in baende:
        poems, entries, hits = split_band(r, korr_all)
        with open(DEST / f"{r['ordner']}.jsonl", "w", encoding="utf-8") as f:
            for pm in poems:
                f.write(json.dumps(pm, ensure_ascii=False) + "\n")
        total += len(poems)
        n_l = [len([x for x in pm["lines"] if x]) for pm in poems]
        tr = sum(1 for pm in poems if pm["uebersetzung"])
        nums = [pm["nummer"] for pm in poems if pm["nummer"] is not None]
        print(f"{r['ordner']}: {len(poems)} Gedichte (TOC {len(entries)}, Anker {len(hits)}), "
              f"Zeilen median {statistics.median(n_l) if n_l else 0}, nummeriert {len(nums)}"
              + (f", Übersetzungen {tr}" if tr else "") + f", Korrekturen {len(korr_all.get(r['ordner'], []))}")
    print("SUMME", total)

if __name__ == "__main__":
    main()
