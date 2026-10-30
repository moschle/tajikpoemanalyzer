#!/usr/bin/env python3
"""Method — how the analyzer reads a poem, and the metre inventory it matches against.

Every threshold stated here is the one the code uses (analyzer.py, persian_meters.py,
corpus_core.py). Change the code, change this page.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

from persian_meters import METREN, grundmass

st.set_page_config(page_title="Method", page_icon="M", layout="wide")
st.title("Method")
st.caption("What the analyzer measures and where its decisions are made. "
           "Thresholds are quoted from the code.")

st.subheader("Syllable weight")
st.markdown(
    "Lines are syllabified word by word and every syllable gets a weight: "
    "**L** (long: ӣ, ӯ, о, е, or a closed syllable), **S** (short), "
    "**u** (open syllable with и/у, short or long), **X** (anceps, the last position), "
    "**o** (possible overlength after a closed syllable with и/у: an optional extra short). "
    "Vasl and hiatus are applied before matching."
)

st.subheader("Metre")
st.markdown(
    "- Each line is held against the Persian half-verse patterns listed below "
    "(derived forms such as makhbūn, akhrab, maḥdhūf), not against the sixteen Arabic full schemes first.\n"
    "- A line counts for a metre at **≥ 85 % positional agreement** "
    "(`alle_metren(silben, 0.85)`); an ambiguous **u** scores 0.9, the final position is free.\n"
    "- Variants of the same family and foot count (`grundmass`) are pooled, so ramal musamman makhbūn "
    "and ramal musamman maḥdhūf support each other. Akhrab, ashtar and mashkūl stay separate.\n"
    "- A poem has a metre only if one basic measure carries **at least 40 % of its lines** "
    "(and at least two). Single chance hits in free verse do not count.\n"
    "- Rubāʿī versus dubaytī: if hazaj musaddas fits as many lines, or the median line has "
    "≤ 10 syllables, the poem is read as hazaj musaddas."
)

st.subheader("Free verse and failed detection")
st.markdown(
    "- **Nimāʾī**: at least 20 % of the (re-joined) lines deviate by more than 30 % from the "
    "median vowel count. Such a poem is free verse; a recognised metre stays recorded as its metrical base.\n"
    "- `meter_status` has three values: **identified**, **free_verse**, **detection_failed**. "
    "Lines of even length without a metre are a failed detection, not shiʿr-i naw."
)

st.subheader("Lexical diversity (MTLD)")
st.markdown(
    "MTLD after McCarthy & Jarvis (2010), TTR threshold **0.72**. The text is run forwards and "
    "backwards; each run gives MTLD = tokens / factors (with a partial factor for the remainder); "
    "the reported value is the **mean of the two MTLD values**. Texts under 10 tokens return 0. "
    "Tokens: `[\\wӣӯ]+` on the lower-cased text. "
    "`TPA_ALTE_MTLD=1` restores the earlier variant (mean of the factor counts), for comparison with older exports."
)

st.subheader("Metre inventory")
st.caption("From persian_meters.py, after Elwell-Sutton, *The Persian Metres* (1976), and "
           "Thiesen, *A Manual of Classical Persian Prosody* (1982). — long, ∪ short; "
           "the last syllable is anceps.")


def zeichen(muster: str) -> str:
    return " ".join("".join("—" if c == "L" else "∪" for c in fuss) for fuss in muster.split())


rubai = [m for n, m in METREN if n == "rubāʿī"]
zeilen = [{"Metre": n, "Basic measure": grundmass(n), "Pattern": zeichen(m),
           "Syllables": len(m.replace(" ", ""))}
          for n, m in METREN if n != "rubāʿī"]
df = pd.DataFrame(zeilen)
st.dataframe(df, hide_index=True, width="stretch")
st.markdown(f"Plus **rubāʿī**: {len(rubai)} variants generated from the scheme "
            "— — (∪∪|—) (— — ∪∪|— — —|— ∪ — ∪) — — (∪∪|—) —.")
st.caption(f"{df['Basic measure'].nunique() + 1} basic measures, "
           f"{len(df) + len(rubai)} patterns in total.")
