"""Zieht ein Inhaltsverzeichnis aus den OCR-Seiten eines Bandes in eine TOC-Datei (seite|titel).

Aufruf: farzona_tococr.py ORDNER VON BIS AUSGABE
Punktfuehrer und Leitergruetze werden abgeschnitten; Kopfzeilen (Mundariҷa, Қисми ...) entfallen.
Das Ergebnis ist ein Rohentwurf fuer farzona_tocvergleich.py und wird von Hand gegen das Bild geprueft.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from farzona_split import OUT  # noqa: E402

KOPF = re.compile(r"^(МУНДАРИ|ФЕҲРИСТ|ҚИСМИ|ФАРЗОНА)", re.I)


def main():
    ordner, von, bis, aus = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    zeilen = []
    for p in range(von, bis + 1):
        for t in (OUT / ordner / f"p{p:04d}.txt").read_text(encoding="utf-8").split("\n"):
            t = t.strip()
            if not t or KOPF.match(t):
                continue
            m = re.match(r"^(.*?)(\.{3,}|…).*?(\d{1,3})?\W*$", t)
            titel, seite = (m.group(1), m.group(3) or "-") if m else (t, "-")
            titel = re.sub(r"^[^\wА-Яа-яӢӣӮӯҲҳҚқҒғҶҷ«]+", "", titel).strip(" .,")
            if len(re.findall(r"[А-Яа-яӢӣӮӯҲҳҚқҒғҶҷ]", titel)) < 4:
                continue
            if not m and len(re.findall(r"[ъз]", titel)) > 6:
                continue                      # reine Leiterzeile
            if max((len(w) for w in titel.split()), default=0) > 18 or len(titel.split()) < 2 and not m:
                continue                      # Ornament- oder Leiterrauschen
            zeilen.append(f"{seite}|{titel}")
    Path(aus).write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    print(len(zeilen), "Eintraege")


if __name__ == "__main__":
    main()
