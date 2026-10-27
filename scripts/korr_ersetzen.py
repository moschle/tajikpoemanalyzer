"""Ersetzt oder entfernt bestehende Korrekturen.

Aufruf: korr_ersetzen.py ORDNER SEITE ZEILENANFANG [NEUE_AKTION [TITEL]]
Ohne NEUE_AKTION wird die Korrektur geloescht.
"""
import json
import sys
from pathlib import Path

KORR = Path(__file__).resolve().parent.parent / "data" / "ocr_farzona" / "korrekturen.json"


def main():
    ordner, seite, z = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    neu = sys.argv[4] if len(sys.argv) > 4 else None
    titel = sys.argv[5] if len(sys.argv) > 5 else None
    k = json.loads(KORR.read_text(encoding="utf-8"))
    liste, treffer = [], 0
    for c in k.get(ordner, []):
        if c["s"] == seite and c.get("z", "").startswith(z):
            treffer += 1
            if neu is None:
                continue
            c = {"s": seite, "z": c["z"], "a": neu}
            if titel:
                c["titel"] = titel
        liste.append(c)
    k[ordner] = liste
    KORR.write_text(json.dumps(k, ensure_ascii=False, indent=1), encoding="utf-8")
    print(ordner, "geaendert:", treffer)


if __name__ == "__main__":
    main()
