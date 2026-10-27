#!/usr/bin/python3
"""Analysiert die zerlegten Farzona-Gedichte und schreibt sie ins Korpus (corpus.json, gitignored).
Aufruf: farzona_import.py [--limit N] [ordner ...]
Volltexte bleiben lokal; oeffentlich wird nur knowledge_export.py features."""
import json, sys, time, logging
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.disable(logging.WARNING)
from analyzer import EnhancedTajikPoemAnalyzer
from corpus_core import Corpus

DIR = Path.home() / "Projects/tajikpoemanalyzer/data/ocr_farzona/gedichte"
# Impressum laut OCR der Titel- und Schlussseiten (Ort, Verlag, Jahr, Auflage)
BAENDE = {
    "ФАРЗОНА_ОЯТИ_ИШҚ": ("Ояти ишқ", 1994, "Душанбе", "Адиб", 5000),
    "ФАРЗОНА_ТО_БЕКАРОНАҲО": ("То бекаронаҳо", 1998, "Хуҷанд", "Нашриёти давлатии ба номи Раҳим Ҷалил", 400),
    "ФАРЗОНА_МЕЪРОҶИ_ШАБНАМ": ("Меъроҷи шабнам", 2000, "Душанбе", "Адиб", 1000),
    "ФАРЗОНА_МУНТАХАБИ_АШЪОР": ("Мунтахаби ашъор", 2001, "Хуҷанд", "Нашриёти давлатии ба номи Раҳим Ҷалил", 200),
    "ФАРЗОНА_ЯК_ҒУНЧА_РОЗ": ("Як ғунча роз", 2005, "Хуҷанд", "Ношир (Druckerei)", 200),
    "ФАРЗОНА_МӮҲРИ_ГУЛИ_МИНО": ("Муҳри гули мино", 2006, "Хуҷанд", "Ношир", 1000),
    "ФАРЗОНА_САД_БАРГИ_ҒАЗАЛ": ("Сад барги ғазал", 2008, "Хуҷанд", "Нури маърифат", 300),
    "ФАРЗОНА_САДУ_ЯК_ҒАЗАЛ": ("Саду як ғазал", 2011, "Душанбе", "Ирфон", 500),
    "ФАРЗОНА_СЕБАРГА": ("Себарга", 2011, "Хуҷанд", "Ношир", 200),
    "ФАРЗОНАИ_ХУҶАНДӢ_ДЕВОН_Панҷсад_ғазали_дилангез": ("Девон. Панҷсад ғазали дилангез", 2014, "Хуҷанд", "Хуросон", 1000),
    "ФАРЗОНА_НАЙСОН": ("Найсон", 2019, "Хуҷанд", "Хуросон", 1700),
    "ФАРЗОНА_НАЙШАКАР": ("Найшакар", 2019, "Душанбе", "Маориф", 10000),
}
# Zweibaendige Sammelausgabe (Мураттиб, Vorwort, ueberwiegend Nachdrucke): keine eigenstaendige Publikation,
# nach Vorgabe 27.10.2026 nicht im Korpus und nicht in den Kennzahlen. Zerlegung bleibt unter gedichte/ erhalten.
SAMMELBAENDE = {
    "ФАРЗОНА_ҲАМА_ГУЛ_ҲАМА_ТАРОНА_Ҷ_1": ("Ҳама гул, ҳама тарона. Ҷ. 1", 2014, "Хуҷанд", "Хуросон-Медиа", 1200),
    "ФАРЗОНА_ҲАМА_ГУЛ_ҲАМА_ТАРОНА_Ҷ_2": ("Ҳама гул, ҳама тарона. Ҷ. 2", 2014, "Хуҷанд", "Хуросон-Медиа", 1200),
}

def main():
    args = sys.argv[1:]
    limit = None
    if "--limit" in args:
        i = args.index("--limit"); limit = int(args[i + 1]); del args[i:i + 2]
    vols = sorted(args or list(BAENDE), key=lambda v: BAENDE[v][1])   # Erstdrucke zuerst
    an = EnhancedTajikPoemAnalyzer(enable_corpus=False)
    c = Corpus(Path(__file__).resolve().parent.parent / "tajik_corpus")
    erst = json.load(open(DIR.parent / "dubletten.json", encoding="utf-8"))
    pid_of = {}                                   # ordner#nr -> poem id
    t0 = time.time(); done = fail = belege = uebers = 0
    for v in vols:
        title, year, city, pub, run = BAENDE[v]
        poems = [json.loads(l) for l in open(DIR / f"{v}.jsonl", encoding="utf-8")]
        for pm in poems[:limit]:
            text = "\n".join(pm["lines"]).strip()
            k = f"{v}#{pm['nr']}"
            if pm.get("uebersetzung"):
                uebers += 1; continue             # Farzonas Uebersetzungen: nicht als eigene Lyrik
            e = erst.get(k)
            if e and e != k and e in pid_of:      # Nachdruck: Beleg am Erstdruck
                rec = next(p for p in c.data["poems"] if p["id"] == pid_of[e])
                wid = c.upsert_work(c.upsert_author("Farzona"), title, source_type="printed",
                                    publication_year=year, city=city, publisher=pub,
                                    notes=f"Auflage {run}; OCR tgk")
                rec["attestations"].append({"work_id": wid, "title_as_given": pm["title"] or pm["lines"][0][:50],
                                            "page": pm["page"], "match": "fuzzy_incipit"})
                pid_of[k] = rec["id"]; belege += 1; continue
            try:
                res = an.analyze_poem(text)
                analysis = json.loads(json.dumps(asdict(res), default=str))
            except Exception as e:
                analysis = {"error": str(e)[:200]}; fail += 1
            pid_of[k] = c.add_poem(
                title=pm["title"] or pm["lines"][0][:50], text=text, author="Farzona",
                author_kw={"name_variants": ["Фарзона", "Фарзонаи Хуҷандӣ"]},
                work_title=title,
                work_kw={"source_type": "printed", "publication_year": year, "city": city,
                         "publisher": pub, "notes": f"Auflage {run}; OCR tgk, Seite {pm['page']} ff."},
                analysis=analysis,
                contributor={"anonymous": True, "source_filename": v, "batch_id": f"ocr_{v}", "page": pm["page"]},
            )
            done += 1
            if done % 100 == 0:
                c.save(); print(f"{done} Gedichte, {time.time() - t0:.0f}s", flush=True)
    c.save()
    print(f"FERTIG {done} Gedichte ({fail} Analysefehler), {belege} Nachdrucke als Beleg, "
          f"{uebers} Uebersetzungen ausgelassen, {time.time() - t0:.0f}s; Korpus jetzt {len(c.data['poems'])}")

if __name__ == "__main__":
    main()
