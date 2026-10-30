#!/usr/bin/env python3
"""MTLD im Korpus auf McCarthy/Jarvis umstellen (Commit 14300df), nur die Formel.

Fuer jedes Gedicht wird die Tokenbasis gesucht, auf der der gespeicherte Wert mit der alten
Formel (Mittel der Faktorzahlen) entstanden ist: Text, Titel + Text oder Text ohne erste Zeile.
Auf derselben Basis wird der neue Wert (Mittel aus Vorwaerts- und Rueckwaerts-MTLD) gerechnet;
alle anderen Analysefelder bleiben unberuehrt. Ohne Treffer gilt der Text.
Geschrieben werden features.mtld und analysis.content.lexical_diversity.

    python3 scripts/mtld_neu.py          # Probelauf
    python3 scripts/mtld_neu.py --write  # corpus.json schreiben (Sicherung daneben)
"""
import json, re, shutil, sys
from datetime import date
from pathlib import Path

CORPUS = Path(__file__).resolve().parent.parent / "tajik_corpus" / "corpus" / "corpus.json"
T = 0.72


def faktoren(w):
    f, s = 0.0, 0
    for i in range(1, len(w) + 1):
        seg = w[s:i]
        if len(set(seg)) / len(seg) <= T:
            f, s = f + 1, i
    if s < len(w):
        r = w[s:]
        f += (1 - len(set(r)) / len(r)) / (1 - T)
    return f


def alt(w):
    if len(w) < 10:
        return 0.0
    a = (faktoren(w) + faktoren(w[::-1])) / 2
    return len(w) / a if a > 0 else float(len(w))


def neu(w):
    if len(w) < 10:
        return 0.0
    n, fv, rv = len(w), faktoren(w), faktoren(w[::-1])
    return ((n / fv if fv > 0 else float(n)) + (n / rv if rv > 0 else float(n))) / 2


def tokens(t):
    return re.findall(r"[\wӣӯ]+", t.lower())


def main(write):
    d = json.loads(CORPUS.read_text(encoding="utf-8"))
    stat = {"text": 0, "titel+text": 0, "ohne 1. zeile": 0, "ohne treffer": 0}
    diffs = []
    for p in d["poems"]:
        t, alt_w = p.get("text", ""), (p.get("features") or {}).get("mtld")
        basen = [("text", t), ("titel+text", p.get("title", "") + "\n" + t),
                 ("ohne 1. zeile", "\n".join(t.split("\n")[1:]))]
        art, w = "ohne treffer", tokens(t)
        if alt_w is not None:
            for name, b in basen:
                if abs(alt(tokens(b)) - alt_w) < 0.01:
                    art, w = name, tokens(b)
                    break
        stat[art] += 1
        v = round(neu(w), 3)
        diffs.append(v - (alt_w or 0))
        p.setdefault("features", {})["mtld"] = v
        c = p.get("analysis", {}).get("content")
        if isinstance(c, dict) and "lexical_diversity" in c:
            c["lexical_diversity"] = v
    print(len(d["poems"]), "Gedichte;", stat)
    diffs.sort()
    print("Aenderung neu - alt: Median %.2f, min %.2f, max %.2f"
          % (diffs[len(diffs) // 2], diffs[0], diffs[-1]))
    if write:
        bak = CORPUS.with_name(f"corpus_vor_mtld_{date.today()}.json")
        shutil.copy2(CORPUS, bak)
        CORPUS.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print("geschrieben; Sicherung", bak.name)


if __name__ == "__main__":
    main("--write" in sys.argv)
