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
    ("hazaj musaddas akhrab maqbūḍ maḥdhūf", "LLS LSLL SLL"),
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
    ("sarīʿ musaddas maṭwī makshūf", "LSSL LSSL LSL"),
    ("muqtaḍab musamman maṭwī", "LSLS LSSL LSLS LSSL"),
    ("kāmil musamman sālim", "SSLSL SSLSL SSLSL SSLSL"),
    ("rubāʿī (akhrab)", "LLS SLLS SLLS SL"),
    ("rubāʿī (akhram)", "LLL LLS SLLS SL"),
]

MUSTER = [(n, m.replace(" ", "")) for n, m in METREN]


def bestes_metrum(silben):
    """silben: Folge aus 'L', 'S', 'u' (offene Silbe mit i/u: kurz oder lang), 'X' (frei).

    Rueckgabe (name, genauigkeit) des besten Musters gleicher Laenge oder (None, 0.0).
    """
    best, acc = None, 0.0
    for name, m in MUSTER:
        if len(m) != len(silben):
            continue
        ok = 0.0
        for i, (s, p) in enumerate(zip(silben, m)):
            if i == len(m) - 1 or s == "X" or s == p:
                ok += 1
            elif s == "u":
                ok += 0.9          # i/u offen: Laenge im Tadschikischen nicht geschrieben
        a = ok / len(m)
        if a > acc:
            best, acc = name, a
    return best, acc
