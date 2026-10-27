#!/usr/bin/python3
"""Seitenbereiche als Korrektur eintragen.  korr_bereich.py ORDNER AKTION VON-BIS [VON-BIS ...]
AKTION: seite_weg | neu_seite"""
import json, subprocess, sys
from pathlib import Path
ordner, aktion = sys.argv[1], sys.argv[2]
k = []
for b in sys.argv[3:]:
    a, e = (int(x) for x in b.split("-"))
    k += [{"s": p, "a": aktion} for p in range(a, e + 1)]
subprocess.run([sys.executable, str(Path(__file__).parent / "korr.py"), ordner, "0", json.dumps(k, ensure_ascii=False)], check=True)
