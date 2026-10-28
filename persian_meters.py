"""Gebraeuchliche Metren der persischen (und tadschikischen) klassischen Lyrik als Halbversmuster.

Das Metrenverzeichnis in analyzer.py kennt nur die 16 Grundmetren in ihrer arabischen Vollform
(Kamil, Wafir usw.). Persische Dichtung verwendet fast nur abgeleitete Formen (makhbun, akhrab,
mahdhuf ...); ohne sie landet der Abgleich bei arabischen Metren. Die Muster folgen der
ueblichen Darstellung (Elwell-Sutton, The Persian Metres, 1976; Thiesen, A Manual of Classical
Persian Prosody, 1982): L = lang, S = kurz; die letzte Silbe ist frei (anceps).
Varianten mit SS statt L am Versanfang (Ramal/Khafif/Mujtathth makhbun) sind eigene Eintraege.
"""

# name, Muster je Halbvers (Fuesse durch Leerzeichen getrennt, nur zur Lesbarkeit)
METREN = [
    ("ramal musamman makhbūn maḥdhūf", "LSLL SSLL SSLL SSL"),
    ("ramal musamman makhbūn maḥdhūf", "SSLL SSLL SSLL SSL"),
    ("ramal musamman maḥdhūf", "LSLL LSLL LSLL LSL"),
    ("ramal musaddas maḥdhūf", "LSLL LSLL LSL"),
    ("ramal musaddas makhbūn maḥdhūf", "LSLL SSLL SSL"),
    ("ramal musaddas makhbūn maḥdhūf", "SSLL SSLL SSL"),
    ("ramal musamman mashkūl", "SSLS LSLL SSLS LSLL"),
    ("hazaj musamman sālim", "SLLL SLLL SLLL SLLL"),
    ("hazaj musaddas maḥdhūf", "SLLL SLLL SLL"),
    ("hazaj musamman akhrab makfūf maḥdhūf", "LLS SLLS SLLS SLL"),
    ("hazaj musamman akhrab", "LLS SLLL LLS SLLL"),
    ("hazaj musaddas akhrab maqbūḍ maḥdhūf", "LLS SLSL SLL"),
    ("hazaj musaddas akhrab makfūf maḥdhūf", "LLS SLLS SLL"),
    ("muḍāriʿ musamman akhrab makfūf maḥdhūf", "LLS LSLS SLLS LSL"),
    ("muḍāriʿ musamman akhrab", "LLS LSLL LLS LSLL"),
    ("mujtathth musamman makhbūn maḥdhūf", "SLSL SSLL SLSL SSL"),
    ("mujtathth musamman makhbūn", "SLSL SSLL SLSL SSLL"),
    ("mutaqārib musamman maḥdhūf", "SLL SLL SLL SL"),
    ("mutaqārib musamman sālim", "SLL SLL SLL SLL"),
    ("khafīf musaddas makhbūn maḥdhūf", "LSLL SLSL SSL"),
    ("khafīf musaddas makhbūn maḥdhūf", "SSLL SLSL SSL"),
    ("rajaz musamman sālim", "LLSL LLSL LLSL LLSL"),
    ("rajaz musamman maṭwī makhbūn", "LSSL SLSL LSSL SLSL"),
    ("munsariḥ musamman maṭwī makshūf", "LSSL LSLS LSSL LSL"),
    ("munsariḥ musamman maṭwī makshūf", "LSSL LSL LSSL LSL"),
    ("sarīʿ musaddas maṭwī makshūf", "LSSL LSSL LSL"),
    ("muqtaḍab musamman maṭwī", "LSLS LSSL LSLS LSSL"),
    ("kāmil musamman sālim", "SSLSL SSLSL SSLSL SSLSL"),
    ("rubāʿī (akhrab)", "LLS SLLS SLLS SL"),
    ("rubāʿī (akhram)", "LLL LLS SLLS SL"),
]

METREN += [
    ("ramal musamman makhbūn aṣlam", "LSLL SSLL SSLL LL"),
    ("ramal musamman makhbūn aṣlam", "SSLL SSLL SSLL LL"),
    ("ramal musaddas makhbūn aṣlam", "SSLL SSLL LL"),
    ("mujtathth musamman makhbūn aṣlam", "SLSL SSLL SLSL LL"),
    ("khafīf musaddas makhbūn aṣlam", "LSLL SLSL LL"),
    ("khafīf musaddas makhbūn aṣlam", "SSLL SLSL LL"),
    ("muḍāriʿ murabbaʿ akhrab", "LLS LSLL"),
    ("hazaj murabbaʿ sālim", "SLLL SLLL"),
    ("ramal murabbaʿ sālim", "LSLL LSLL"),
    ("hazaj musamman maḥdhūf", "SLLL SLLL SLLL SLL"),
    ("hazaj musaddas sālim", "SLLL SLLL SLLL"),
    ("rajaz murabbaʿ sālim", "LLSL LLSL"),
    ("rajaz musaddas sālim", "LLSL LLSL LLSL"),
    ("hazaj musamman ashtar", "LSL SLLL LSL SLLL"),
    ("hazaj murabbaʿ ashtar", "LSL SLLL"),
    ("ramal musamman sālim", "LSLL LSLL LSLL LSLL"),
    ("ramal musaddas sālim", "LSLL LSLL LSLL"),
    ("ramal musamman makhbūn", "LSLL SSLL SSLL SSLL"),
    ("ramal musamman makhbūn", "SSLL SSLL SSLL SSLL"),
    ("rajaz musamman makhbūn", "SLSL SLSL SLSL SLSL"),
    ("rajaz musaddas makhbūn", "SLSL SLSL SLSL"),
    ("rajaz murabbaʿ makhbūn", "SLSL SLSL"),
    ("rajaz musamman maṭwī", "LSSL LSSL LSSL LSSL"),
    ("muḍāriʿ murabbaʿ akhrab maḥdhūf", "LLS LSL"),
    ("hazaj murabbaʿ akhrab", "LLS SLLL"),
    ("ramal murabbaʿ maḥdhūf", "LSLL LSL"),
]


def _rubai():
    """Die 24 Rubai-Varianten als Schema: LL SS LL SS LL SS L; jedes SS darf zu L werden,
    das mittlere LSS (mafaʿilu) darf als SLS (mafaʿilun) stehen."""
    return sorted({"LL" + a + m + "LL" + c + "L"
                   for a in ("SS", "L") for m in ("LLSS", "LLL", "LSLS") for c in ("SS", "L")})


METREN = [m for m in METREN if not m[0].startswith("rubāʿī")] + \
    [("rubāʿī", r) for r in _rubai()]
MUSTER = [(n, m.replace(" ", "")) for n, m in METREN]


def _passung(silben, m):
    """Beste Summe der Positionstreffer; 'o' = optionale Kurzsilbe (fehlt oder S)."""
    from functools import lru_cache
    n, k = len(silben), len(m)

    @lru_cache(maxsize=None)
    def f(i, j):
        if j == k:
            return 0.0 if all(x == "o" for x in silben[i:]) else None
        if i == n:
            return None
        s = silben[i]
        best = None
        if s == "o":
            r = f(i + 1, j)
            best = r
            s = "S"
        sc = 1.0 if (j == k - 1 or s == "X" or s == m[j]) else (0.9 if s == "u" else 0.0)
        r = f(i + 1, j + 1)
        if r is not None and (best is None or r + sc > best):
            best = r + sc
        return best
    return f(0, 0)


def bestes_metrum(silben):
    """silben: Folge aus 'L', 'S', 'u' (offene Silbe mit i/u: kurz oder lang), 'X' (frei),
    'o' (moegliche Ueberlaenge nach geschlossenem i/u: Kurzsilbe optional).

    Rueckgabe (name, genauigkeit) des besten Musters oder (None, 0.0).
    """
    silben = tuple(silben)
    fest = sum(1 for x in silben if x != "o")
    opt = len(silben) - fest
    best, acc = None, 0.0
    for name, m in MUSTER:
        if not fest <= len(m) <= fest + opt:
            continue
        r = _passung(silben, m)
        if r is None:
            continue
        a = r / len(m)
        if a > acc:
            best, acc = name, a
    return best, acc



def alle_metren(silben, schwelle=0.85):
    """Alle Muster mit Genauigkeit >= schwelle als [(name, genauigkeit)], absteigend."""
    silben = tuple(silben)
    fest = sum(1 for x in silben if x != "o")
    opt = len(silben) - fest
    out = {}
    for name, m in MUSTER:
        if not fest <= len(m) <= fest + opt:
            continue
        r = _passung(silben, m)
        if r is not None and r / len(m) >= schwelle:
            out[name] = max(out.get(name, 0.0), r / len(m))
    return sorted(out.items(), key=lambda x: -x[1])


def grundmass(name):
    """Grundmass = Familie + Fusszahl ('ramal musaddas'); Varianten des ersten und letzten Fusses
    (makhbun/salim, mahdhuf/aslam) sowie Rubai zaehlen zusammen. Akhrab-Formen des Hazaj bleiben
    eigenes Mass, ebenso Ashtar."""
    w = str(name).split()
    if not w:
        return ""
    if w[0].startswith("rub"):
        return "rubāʿī"
    basis = " ".join(w[:2])
    for k in ("akhrab", "ashtar", "mashkūl"):
        if k in w:
            basis += " " + k
    return basis
