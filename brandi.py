"""
UAP-brändi Streamlit-sovelluksiin: favicon, sivupalkin logo ja yläotsikko.

Logo ja säännöt: brand/LOGO-OHJE.md · värit ja typografia: brand/BRANDIKIRJA.md.
Teema (värit, fontit) tulee .streamlit/config.toml:sta — tämä moduuli hoitaa vain logon.
"""

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

BRAND = Path(__file__).parent / "brand"
MERKKI_SVG = BRAND / "svg" / "uap-merkki-vari.svg"
KUVAKE_PNG = BRAND / "png" / "uap-merkki-sovelluskuvake-512.png"

PETROLI = "#14232A"
KLINIKKA = "#1F7A73"
OY_HARMAA = "#7A888B"


def sivun_asetukset(otsikko: str, varakuvake: str = "🏗️", layout: str = "wide", **lisa):
    """st.set_page_config UAP-sovelluskuvakkeella. Logo näytetään sivulla ylatunniste()-
    funktiolla — ei st.logo:a, ettei merkki näy kahteen kertaan."""
    try:
        from PIL import Image
        kuvake = Image.open(KUVAKE_PNG)
    except Exception:
        kuvake = varakuvake
    st.set_page_config(page_title=f"{otsikko} · UAP", page_icon=kuvake, layout=layout, **lisa)


@lru_cache(maxsize=1)
def _merkki_data_uri() -> str:
    try:
        return "data:image/svg+xml;base64," + base64.b64encode(MERKKI_SVG.read_bytes()).decode()
    except Exception:
        return ""


def ylatunniste(merkin_koko: int = 56):
    """Merkki + "Uudenmaan Asbestipurku Oy" logo-ohjeen mukaan (väli ¼ merkin leveydestä,
    nimi n. 60 % merkin korkeudesta, "Oy" kevyempänä harmaana)."""
    uri = _merkki_data_uri()
    if not uri:
        return
    vali = merkin_koko // 4
    nimen_koko = round(merkin_koko * 0.6 / 2.1)   # kaksi riviä, rivinkorkeus 1,05
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:{vali}px;margin:0 0 0.75rem 0">
<img src="{uri}" width="{merkin_koko}" height="{merkin_koko}" alt="Uudenmaan Asbestipurku Oy">
<div style="font-family:'Hanken Grotesk',sans-serif;font-weight:700;font-size:{nimen_koko}px;
line-height:1.05;letter-spacing:-0.015em;color:{PETROLI}">Uudenmaan<br>Asbestipurku
<span style="font-weight:500;color:{OY_HARMAA}">Oy</span></div>
</div>""",
        unsafe_allow_html=True,
    )
