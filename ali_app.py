"""
Aliurakoitsijoiden tuntiseuranta — erillinen sovellus
Uudenmaan Asbestipurku Oy

Käynnistys:
    python3 -m streamlit run ali_app.py --server.port 8502
→ http://localhost:8502
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import json

from storage import (
    lataa_ali_tunnit, tallenna_ali_tunnit, hae_projektit,
    lataa_projektirekisteri, tallenna_projektirekisteri,
    hae_projekti_koodilla, tallenna_projekti_yhteenveto, lataa_projekti_yhteenveto,
    lataa_ammattinimikkeet, tallenna_ammattinimikkeet,
)
from raportti_ali import luo_viikkoraportti
from translations import tr, paivat as _paivat_nimet, kategoriat, laskutustavat

# ── Apufunktiot ────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
TYONTEKIJAT_POLKU = DATA_DIR / "_aliurakoitsijat.json"
ASETUKSET_POLKU   = DATA_DIR / "_ali_asetukset.json"

PAIVAT      = ["Ma","Ti","Ke","To","Pe","La","Su"]
PAIVA_AVAIN = ["ma","ti","ke","to","pe","la","su"]
KATEGORIAT  = ["Urakka","Lisätyö","Vesivahinko"]

# ── Hyväksyntätilat ───────────────────────────────────────────────────────────
TILAT = {
    "odottaa":    {"emoji": "🔵", "tila_avain": "tila_odottaa",    "väri": "#E3F0FF", "reuna": "#1E88E5"},
    "hyvaksytty": {"emoji": "✅", "tila_avain": "tila_hyvaksytty", "väri": "#E8F5E9", "reuna": "#43A047"},
    "selvitys":   {"emoji": "⚠️", "tila_avain": "tila_selvitys",   "väri": "#FFF8E1", "reuna": "#F9A825"},
}

def _tila_css(tila: str) -> str:
    td = TILAT.get(tila, TILAT["odottaa"])
    return (
        f"background-color:{td['väri']};"
        f"border-left:5px solid {td['reuna']};"
        f"border-radius:6px;padding:10px 14px;margin:4px 0;"
    )

def _tila_badge(tila: str, kieli: str = "fi") -> str:
    td = TILAT.get(tila, TILAT["odottaa"])
    return f"{td['emoji']} {tr(td['tila_avain'], kieli)}"

def _lataa_tyontekijat() -> list:
    if TYONTEKIJAT_POLKU.exists():
        return json.loads(TYONTEKIJAT_POLKU.read_text(encoding="utf-8"))
    return []

def _tallenna_tyontekijat(lista: list):
    TYONTEKIJAT_POLKU.write_text(json.dumps(lista, ensure_ascii=False, indent=2), encoding="utf-8")

def _lataa_asetukset() -> dict:
    if ASETUKSET_POLKU.exists():
        return json.loads(ASETUKSET_POLKU.read_text(encoding="utf-8"))
    return {}

def _tallenna_asetukset(d: dict):
    ASETUKSET_POLKU.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def _viikon_paivat(vuosi: int, viikko: int) -> list[date]:
    ma = date.fromisocalendar(vuosi, viikko, 1)
    return [ma + timedelta(days=i) for i in range(7)]

def _projekti_slug(projekti: str) -> str:
    import re
    s = projekti.lower().strip()
    s = re.sub(r"[^a-z0-9äöå]", "_", s)
    return re.sub(r"_+", "_", s).strip("_") or "projekti"

def _hae_projektit() -> list:
    return hae_projektit()

# ── Sivun asetukset ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ali-tuntikirja",
    page_icon="👷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Roolikirjautuminen ─────────────────────────────────────────────────────────
import random, string

def _luo_koodi(pituus=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=pituus))

def _hae_secrets():
    try:
        return st.secrets.get("auth", {})
    except Exception:
        return {}

def _kirjautuminen():
    """Palauttaa (rooli, projekti_nimi) tai pysäyttää sovelluksen."""
    auth = _hae_secrets()
    tj_salasana  = auth.get("tj_salasana", "")
    ali_salasana = auth.get("ali_salasana", "")

    # Paikallinen kehitys ilman secretsejä
    if not tj_salasana and not ali_salasana:
        return "tj", st.session_state.get("projekti_nimi", "")

    # Jo kirjautunut
    if st.session_state.get("rooli"):
        return st.session_state["rooli"], st.session_state.get("projekti_nimi", "")

    # Kirjautumissivu
    st.markdown("## 👷 Aliurakoitsijoiden tuntikirja")
    st.markdown("---")

    valinta = st.radio("Kirjaudu sisään:", ["🔑 Työnjohtaja", "📋 Aliurakoitsija (projektikoodi)"],
                       horizontal=True)

    if valinta == "🔑 Työnjohtaja":
        pw = st.text_input("Työnjohtajan salasana", type="password", key="tj_pw")
        if st.button("Kirjaudu", type="primary", use_container_width=True):
            if pw == tj_salasana:
                st.session_state["rooli"] = "tj"
                st.session_state["projekti_nimi"] = ""
                st.rerun()
            else:
                st.error("Väärä salasana.")
    else:
        koodi = st.text_input("Projektikoodi (6 merkkiä)", max_chars=6,
                              placeholder="esim. VALT26").strip().upper()
        if st.button("Avaa projekti", type="primary", use_container_width=True):
            projekti = hae_projekti_koodilla(koodi)
            if projekti:
                st.session_state["rooli"] = "ali"
                st.session_state["projekti_nimi"] = projekti["nimi"]
                st.session_state["projekti_koodi"] = koodi
                st.rerun()
            else:
                st.error("Projektikoodi ei löydy. Tarkista koodi työnjohtajalta.")

    st.stop()

rooli, _proj_init = _kirjautuminen()

# Kompakti CSS — isommat napit, siistimpi mobiililla
st.markdown("""
<style>
    .stNumberInput input { font-size: 1.2rem; font-weight: 600; text-align: center; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; }
    .block-container { padding-top: 1rem; }
    h1 { font-size: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Tallennetut asetukset ──────────────────────────────────────────────────────
asetukset           = _lataa_asetukset()
tyontekijat_lista   = _lataa_tyontekijat()
ammattinimikkeet    = lataa_ammattinimikkeet()
_nimike_hinnat      = {n["nimike"]: n["tuntihinta"] for n in ammattinimikkeet}

# ── SIVUPALKKI ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # Kielinappi
    k1, k2 = st.columns(2)
    if k1.button("🇫🇮 Suomi", use_container_width=True,
                 type="primary" if st.session_state.get("kieli","fi")=="fi" else "secondary"):
        st.session_state["kieli"] = "fi"
        st.rerun()
    if k2.button("🇷🇺 Русский", use_container_width=True,
                 type="primary" if st.session_state.get("kieli","fi")=="ru" else "secondary"):
        st.session_state["kieli"] = "ru"
        st.rerun()

    kieli = st.session_state.get("kieli", "fi")
    st.divider()

    # ── Projektivalinta roolien mukaan ────────────────────────────────────────
    rekisteri = lataa_projektirekisteri()
    aktiiviset = [p for p in rekisteri if p.get("tila") != "valmis"]

    if rooli == "tj":
        # Työnjohtaja: dropdown kaikista projekteista + uuden luonti
        st.caption(f"🔑 Työnjohtaja")
        proj_nimet = [p["nimi"] for p in aktiiviset]
        proj_oletus = st.session_state.get("projekti_nimi", proj_nimet[0] if proj_nimet else "")
        if proj_nimet:
            valittu_idx = proj_nimet.index(proj_oletus) if proj_oletus in proj_nimet else 0
            projekti = st.selectbox(tr("projekti", kieli), proj_nimet, index=valittu_idx)
        else:
            projekti = st.text_input(tr("projekti", kieli), value=proj_oletus,
                                     placeholder=tr("projekti_ph", kieli))
        st.session_state["projekti_nimi"] = projekti

        if st.button("🔓 Kirjaudu ulos", use_container_width=True):
            for k in ["rooli","projekti_nimi","projekti_koodi","kirjautunut"]:
                st.session_state.pop(k, None)
            st.rerun()
    else:
        # Aliurakoitsija: näkee vain oman projektinsa
        projekti = st.session_state.get("projekti_nimi", "")
        proj_info = next((p for p in rekisteri if p["nimi"] == projekti), {})
        st.caption(f"📋 {projekti}")
        st.caption(f"Koodi: `{proj_info.get('koodi','')}`")
        if st.button("🔓 Kirjaudu ulos", use_container_width=True):
            for k in ["rooli","projekti_nimi","projekti_koodi"]:
                st.session_state.pop(k, None)
            st.rerun()

    # Viikko ja vuosi
    tana = date.today()
    st.divider()
    vuosi  = st.number_input(tr("vuosi", kieli),  value=asetukset.get("vuosi",  tana.year),  step=1, format="%d")
    viikko = st.number_input(tr("viikko", kieli), value=asetukset.get("viikko", int(tana.strftime("%V"))),
                              min_value=1, max_value=53, step=1)

    paivat     = _viikon_paivat(int(vuosi), int(viikko))
    PAIVAT_NYK = _paivat_nimet(kieli)
    LASK_TAVAT = laskutustavat(kieli)
    # Kustannuspaikat projektin mukaan (jos projekti löytyy rekisteristä)
    _proj_info  = next((p for p in lataa_projektirekisteri() if p["nimi"] == projekti), {})
    _kp_fi      = _proj_info.get("kustannuspaikat", ["Urakka","Lisätyö","Vesivahinko"])
    _kp_kaikki  = {"Urakka": tr("urakka",kieli), "Lisätyö": tr("lisatyo",kieli), "Vesivahinko": tr("vesivahinko",kieli)}
    KATEGORIAT  = [_kp_kaikki.get(k, k) for k in _kp_fi]

    st.caption(" · ".join(f"{P} {p.strftime('%-d.%-m.')}" for P, p in zip(PAIVAT_NYK, paivat)))
    st.divider()

    kat_oletus = asetukset.get("kategoria", KATEGORIAT[0] if KATEGORIAT else "Urakka")
    if rooli == "tj":
        # Työnjohtaja: voi lisätä väliaikaisen kategorian vapaasti
        oletus_kat = st.selectbox(tr("oletus_kat", kieli), KATEGORIAT,
                                  index=KATEGORIAT.index(kat_oletus) if kat_oletus in KATEGORIAT else 0)
        uusi_kat = st.text_input("Tai kirjoita oma kategoria",
                                 placeholder="esim. Huoltotyö",
                                 key="sb_uusi_kat")
        if uusi_kat.strip():
            oletus_kat = uusi_kat.strip()
            if oletus_kat not in KATEGORIAT:
                KATEGORIAT = KATEGORIAT + [oletus_kat]
    else:
        kat_idx    = KATEGORIAT.index(kat_oletus) if kat_oletus in KATEGORIAT else 0
        oletus_kat = st.selectbox(tr("oletus_kat", kieli), KATEGORIAT, index=kat_idx)

kieli = st.session_state.get("kieli", "fi")
rooli_badge = "🔑 TJ" if rooli == "tj" else "📋"
st.title(f"👷 {tr('app_title', kieli)}")
st.caption(f"{tr('app_caption', kieli)}  ·  {rooli_badge}  ·  {projekti or '—'}")

_tallenna_asetukset({"projekti": projekti, "vuosi": int(vuosi),
                     "viikko": int(viikko), "kategoria": oletus_kat})

if not projekti:
    st.warning(tr("aseta_projekti", kieli))
    st.stop()

# Lataa projektin ali-tuntikirja
ali_rivit: list = lataa_ali_tunnit(projekti)

# ── VÄLILEHDET — roolien mukaan ────────────────────────────────────────────────
if rooli == "tj":
    tab_pikasyotto, tab_yksittainen, tab_vkoyht, tab_tekijat, tab_projektit, tab_historia = st.tabs([
        tr("tab_pikasyotto", kieli),
        tr("tab_yksittainen", kieli),
        tr("tab_vkoyht", kieli),
        tr("tab_tekijat", kieli),
        "📁 Projektit",
        "📈 Historia",
    ])
else:
    tab_pikasyotto, tab_yksittainen, tab_vkoyht = st.tabs([
        tr("tab_pikasyotto", kieli),
        tr("tab_yksittainen", kieli),
        tr("tab_vkoyht", kieli),
    ])
    tab_tekijat = tab_projektit = tab_historia = None

# ══════════════════════════════════════════════════════════════════════════════
# PIKASYÖTTÖ — kaikki tekijät kerralla taulukossa
# ══════════════════════════════════════════════════════════════════════════════
with tab_pikasyotto:
    st.subheader(f"{tr('viikko', kieli)} {viikko} / {vuosi}")

    if not tyontekijat_lista:
        st.info(tr("ei_tekijoita", kieli))
    else:
        vko_nyky = {r["nimi"]: r for r in ali_rivit
                    if r.get("viikko") == int(viikko)
                    and r.get("vuosi", int(vuosi)) == int(vuosi)}

        pika_tunnit    = {}  # {nimi: {pk: float}}
        pika_kategoriat = {}  # {nimi: str}
        pika_huomiot   = {}  # {nimi: {pk: str}}

        for tk in tyontekijat_lista:
            nimi  = tk["nimi"]
            nyky  = vko_nyky.get(nimi, {})
            nyky_hm = nyky.get("huomiot", {})

            # ── Tekijän otsikko ──────────────────────────────────────────
            tila_nyky = nyky.get("hyvaksynta_tila", "")
            badge = f" {_tila_badge(tila_nyky, kieli)}" if tila_nyky else ""
            st.markdown(f"**{nimi}**{badge}")
            if tk.get("yritys"):
                st.caption(tk["yritys"])

            # Työnjohtajan kommentti (vain luku)
            km = nyky.get("tj_kommentti", "")
            if km:
                st.markdown(
                    f"<div style='background:#FFF3CD;border-left:4px solid #FFC107;"
                    f"border-radius:4px;padding:6px 10px;margin:2px 0;font-size:0.88em'>"
                    f"💬 {km}</div>",
                    unsafe_allow_html=True,
                )

            # ── Kategoria ────────────────────────────────────────────────
            kat_nyky = nyky.get("kategoria", oletus_kat)
            pika_kategoriat[nimi] = st.selectbox(
                tr("kategoria", kieli), KATEGORIAT,
                index=KATEGORIAT.index(kat_nyky) if kat_nyky in KATEGORIAT else 0,
                key=f"pika_kat_{nimi}_{viikko}_{vuosi}",
                label_visibility="collapsed",
            )

            # ── Tunnit (number_input per päivä — toimii puhelimella) ──────
            h_cols = st.columns(7)
            pika_tunnit[nimi] = {}
            for i, (P, pk, p) in enumerate(zip(PAIVAT_NYK, PAIVA_AVAIN, paivat)):
                oletus_h = float(nyky.get(pk, 0) or 0)
                pika_tunnit[nimi][pk] = h_cols[i].number_input(
                    f"{P} {p.strftime('%-d.%-m.')}",
                    min_value=0.0, max_value=24.0,
                    value=oletus_h, step=0.5,
                    key=f"pika_{nimi}_{pk}_{viikko}_{vuosi}",
                )

            yht = sum(pika_tunnit[nimi].values())
            st.caption(f"{tr('yht_tunnit', kieli)}: **{yht:.1f} h**")

            # ── Päiväkohtaiset huomiot ────────────────────────────────────
            with st.expander(tr("pv_huomiot", kieli), expanded=False):
                hm_cols = st.columns(7)
                pika_huomiot[nimi] = {}
                for i, (P, pk, p) in enumerate(zip(PAIVAT_NYK, PAIVA_AVAIN, paivat)):
                    pika_huomiot[nimi][pk] = hm_cols[i].text_input(
                        f"{P} {p.strftime('%-d.%-m.')}",
                        value=nyky_hm.get(pk, ""),
                        key=f"pika_hm_{nimi}_{pk}_{viikko}_{vuosi}",
                        placeholder="–",
                        label_visibility="visible",
                    )

            st.divider()

        # ── Kokonaissumma + Tallenna ──────────────────────────────────────
        yht_kaikki = sum(sum(v.values()) for v in pika_tunnit.values())
        st.metric(tr("yht_tunnit", kieli), f"{yht_kaikki:.1f} h")

        if st.button(tr("tallenna_kaikki", kieli), type="primary", use_container_width=True):
            for tk in tyontekijat_lista:
                nimi   = tk["nimi"]
                tunnit = pika_tunnit[nimi]
                yht_h  = sum(tunnit.values())
                uusi = {
                    "id":           f"{viikko}_{vuosi}_{nimi}".replace(" ","_"),
                    "viikko":       int(viikko),
                    "vuosi":        int(vuosi),
                    "nimi":         nimi,
                    "yritys":       tk.get("yritys", ""),
                    "kategoria":    pika_kategoriat[nimi],
                    **tunnit,
                    "yht_h":        yht_h,
                    "laskutustapa": tk.get("laskutustapa", "tunnit"),
                    "tuntihinta":   tk.get("tuntihinta"),
                    "kiintea_hinta":tk.get("kiintea_hinta"),
                    "huomio":       "",
                    "huomiot":      pika_huomiot.get(nimi, {}),
                    # Säilytä olemassa oleva hyväksyntä- ja kommenttidata
                    "hyvaksynta_tila":   vko_nyky.get(nimi, {}).get("hyvaksynta_tila", "odottaa"),
                    "hyvaksynta_pvm":    vko_nyky.get(nimi, {}).get("hyvaksynta_pvm", ""),
                    "hyvaksynta_klo":    vko_nyky.get(nimi, {}).get("hyvaksynta_klo", ""),
                    "hyvaksynta_kuka":   vko_nyky.get(nimi, {}).get("hyvaksynta_kuka", ""),
                    "hyvaksynta_huomio": vko_nyky.get(nimi, {}).get("hyvaksynta_huomio", ""),
                    "tj_kommentti":      vko_nyky.get(nimi, {}).get("tj_kommentti", ""),
                }
                ali_rivit = [r for r in ali_rivit
                             if not (r.get("viikko") == int(viikko)
                                     and r.get("vuosi", int(vuosi)) == int(vuosi)
                                     and r.get("nimi") == nimi)]
                ali_rivit.append(uusi)

            tallenna_ali_tunnit(projekti, ali_rivit)
            st.success(f"{tr('tallennettu', kieli)}: {len(tyontekijat_lista)} — {tr('viikko', kieli)} {viikko}/{vuosi}")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# YKSITTÄINEN SYÖTTÖ
# ══════════════════════════════════════════════════════════════════════════════
with tab_yksittainen:
    st.subheader(tr("tab_yksittainen", kieli))

    nimet = [tk["nimi"] for tk in tyontekijat_lista]
    if not nimet:
        st.info(tr("ei_tekijoita", kieli))
    else:
        col_vas, col_oik = st.columns([1, 2])
        with col_vas:
            valittu_nimi = st.selectbox(tr("tekija", kieli), nimet)
            t_info = next((tk for tk in tyontekijat_lista if tk["nimi"] == valittu_nimi), {})
            st.caption(f"{tr('yritys', kieli)}: {t_info.get('yritys','–')}")

            # Työnjohtajan kommentti tällä tekijällä tälle viikolle
            nyky_rv = next((r for r in ali_rivit
                            if r.get("viikko")==int(viikko)
                            and r.get("vuosi",int(vuosi))==int(vuosi)
                            and r.get("nimi")==valittu_nimi), {})
            yk_kommentti = nyky_rv.get("tj_kommentti","")
            if yk_kommentti:
                st.markdown(
                    f"<div style='background:#FFF3CD;border-left:4px solid #FFC107;"
                    f"border-radius:4px;padding:8px 10px;font-size:0.88em;margin:6px 0'>"
                    f"💬 <b>Työnjohtajan huomio:</b><br>{yk_kommentti}</div>",
                    unsafe_allow_html=True,
                )

            yk_kat = st.selectbox(tr("kategoria", kieli), KATEGORIAT,
                                  index=KATEGORIAT.index(oletus_kat) if oletus_kat in KATEGORIAT else 0,
                                  key="yk_kat")

            lp = t_info.get("laskutustapa","tunnit")
            if lp == "tuntihinta":
                th = t_info.get("tuntihinta") or 0
                st.caption(f"Laskutus: {th:.0f} €/h")
            elif lp == "kiintea":
                kh = t_info.get("kiintea_hinta") or 0
                st.caption(f"Laskutus: Kiinteä {kh:.0f} €")
            else:
                st.caption("Laskutus: Vain tunnit")

        with col_oik:
            st.markdown(f"**{tr('tunnit_pv', kieli)}**")
            # Hae esitäyttö
            nyky = next((r for r in ali_rivit
                         if r.get("viikko") == int(viikko)
                         and r.get("vuosi", int(vuosi)) == int(vuosi)
                         and r.get("nimi") == valittu_nimi), {})
            nyky_huomiot = nyky.get("huomiot", {})

            cols_h = st.columns(7)
            h_arvot   = {}
            h_huomiot = {}
            for i, (P, pk, p) in enumerate(zip(PAIVAT_NYK, PAIVA_AVAIN, paivat)):
                oletus_h  = float(nyky.get(pk, 0) or 0)
                oletus_hm = nyky_huomiot.get(pk, "")
                h_arvot[pk] = cols_h[i].number_input(
                    f"{P} {p.strftime('%-d.%-m.')}",
                    min_value=0.0, max_value=24.0,
                    value=oletus_h, step=0.5,
                    key=f"yk_{pk}",
                )
                h_huomiot[pk] = cols_h[i].text_input(
                    tr("huomio", kieli),
                    value=oletus_hm,
                    key=f"yk_hm_{pk}",
                    placeholder=tr("huomio_ph", kieli),
                    label_visibility="collapsed",
                )

            yht_h = sum(h_arvot.values())

            # Pikasyöttönapit
            st.markdown(f"**{tr('lisaa_tunnit', kieli)}**")
            btn_cols = st.columns(5)
            for lisays in [6, 7, 8, 9, 10]:
                if btn_cols[lisays-6].button(f"+{lisays}h ark", key=f"btn_{lisays}"):
                    for pk in ["ma","ti","ke","to","pe"]:
                        h_arvot[pk] = float(lisays)
                    yht_h = sum(h_arvot.values())

        huomio = st.text_input(tr("yleinen_huomio", kieli), key="yk_huomio")

        c1, c2 = st.columns(2)
        c1.metric("Tunnit yhteensä", f"{yht_h:.1f} h")
        if lp == "tuntihinta" and t_info.get("tuntihinta"):
            c2.metric("Summa", f"{yht_h * t_info['tuntihinta']:,.0f} €")

        if st.button(tr("tallenna", kieli), type="primary", use_container_width=True, key="yk_tall"):
            uusi = {
                "id":       f"{viikko}_{vuosi}_{valittu_nimi}".replace(" ","_"),
                "viikko":   int(viikko),
                "vuosi":    int(vuosi),
                "nimi":     valittu_nimi,
                "yritys":   t_info.get("yritys",""),
                "kategoria":yk_kat,
                **h_arvot,
                "yht_h":         yht_h,
                "laskutustapa":  lp,
                "tuntihinta":    t_info.get("tuntihinta"),
                "kiintea_hinta": t_info.get("kiintea_hinta"),
                "huomio":        huomio,
                "huomiot":       h_huomiot,
            }
            ali_rivit = [r for r in ali_rivit
                         if not (r.get("viikko") == int(viikko)
                                 and r.get("vuosi", int(vuosi)) == int(vuosi)
                                 and r.get("nimi") == valittu_nimi)]
            ali_rivit.append(uusi)
            tallenna_ali_tunnit(projekti, ali_rivit)
            st.success(f"✅ {valittu_nimi} — {yht_h:.1f} h {tr('tallennettu', kieli).replace('✅ ','').lower()}!")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# VIIKKOYHTEENVETO
# ══════════════════════════════════════════════════════════════════════════════
with tab_vkoyht:
    st.subheader(f"Viikko {viikko}/{vuosi} — yhteenveto")
    paiva_otsikot_yht = [f"{P} {p.strftime('%-d.%-m.')}"
                         for P, p in zip(PAIVAT, paivat)]

    vko_rivit = [r for r in ali_rivit
                 if r.get("viikko") == int(viikko)
                 and r.get("vuosi", int(vuosi)) == int(vuosi)]

    if not vko_rivit:
        st.info(tr("ei_kirjauksia", kieli))
    else:
        # Taulukko
        tbl = []
        for rv in sorted(vko_rivit, key=lambda r: r.get("yritys","")):
            h_per_paiva = [rv.get(pk, 0) or 0 for pk in PAIVA_AVAIN]
            yht = sum(h_per_paiva)
            lp  = rv.get("laskutustapa","tunnit")
            if lp == "tuntihinta": summa = yht * (rv.get("tuntihinta") or 0)
            elif lp == "kiintea":  summa = rv.get("kiintea_hinta") or 0
            else:                  summa = None
            rivi = {
                "Nimi": rv["nimi"], "Yritys": rv.get("yritys",""),
                "Kategoria": rv.get("kategoria",""),
            }
            for po, h in zip(paiva_otsikot_yht, h_per_paiva):
                rivi[po] = h if h else ""
            rivi[tr("taulukko_yht",kieli)]   = yht
            rivi[tr("taulukko_summa",kieli)] = f"{summa:,.0f}" if summa else "–"
            rivi[tr("taulukko_tila",kieli)]  = _tila_badge(rv.get("hyvaksynta_tila","odottaa"), kieli)
            tbl.append(rivi)

        df_yht = pd.DataFrame(tbl)
        st.dataframe(df_yht, use_container_width=True, hide_index=True)

        # Päiväkohtaiset huomiot yhteenvedossa
        huomiot_olemassa = any(
            any(v for v in r.get("huomiot", {}).values())
            for r in vko_rivit
        )
        if huomiot_olemassa:
            with st.expander(tr("pv_huomiot", kieli), expanded=False):
                for rv in sorted(vko_rivit, key=lambda r: r.get("yritys","")):
                    huomiot = rv.get("huomiot", {})
                    merkinnat = [(P, p, huomiot.get(pk,""))
                                 for P, pk, p in zip(PAIVAT, PAIVA_AVAIN, paivat)
                                 if huomiot.get(pk,"").strip()]
                    if merkinnat:
                        st.markdown(f"**{rv['nimi']}** ({rv.get('yritys','')})")
                        for P, p, teksti in merkinnat:
                            st.caption(f"{P} {p.strftime('%-d.%-m.')}: {teksti}")

        # ── Hyväksyntä ────────────────────────────────────────────────────────
        st.divider()
        st.markdown(f"### {tr('hyvaksynta', kieli)}")

        hyv_muutettu = False
        for rv in sorted(vko_rivit, key=lambda r: r.get("yritys","")):
            tila     = rv.get("hyvaksynta_tila", "odottaa")
            t        = TILAT.get(tila, TILAT["odottaa"])
            hyv_pvm  = rv.get("hyvaksynta_pvm", "")
            hyv_klo  = rv.get("hyvaksynta_klo", "")
            hyv_kuka = rv.get("hyvaksynta_kuka", "")
            hyv_hm   = rv.get("hyvaksynta_huomio", "")
            yht_h    = rv.get("yht_h", 0)

            # Värillinen kortti
            aikaleima = f" · {hyv_kuka} {hyv_pvm} {hyv_klo}" if hyv_pvm else ""
            st.markdown(
                f"<div style='{_tila_css(tila)}'>"
                f"<b>{t['emoji']} {rv['nimi']}</b> &nbsp;·&nbsp; {rv.get('yritys','')} "
                f"&nbsp;·&nbsp; {yht_h:.1f} h"
                f"<span style='color:#888;font-size:0.85em'>{aikaleima}</span>"
                + (f"<br><span style='color:#B7860B;font-size:0.9em'>💬 {hyv_hm}</span>" if hyv_hm else "")
                + "</div>",
                unsafe_allow_html=True,
            )

            # Hyväksyntänapit
            btn_id = rv["id"].replace("-","_")
            b1, b2, b3, b4 = st.columns([2, 2, 2, 4])

            if b1.button(tr("hyvaksy", kieli), key=f"hyv_{btn_id}", use_container_width=True):
                rv["hyvaksynta_tila"]   = "hyvaksytty"
                rv["hyvaksynta_pvm"]    = date.today().strftime("%d.%m.%Y")
                rv["hyvaksynta_klo"]    = __import__("datetime").datetime.now().strftime("%H:%M")
                rv["hyvaksynta_kuka"]   = "Työnjohtaja"
                rv["hyvaksynta_huomio"] = ""
                hyv_muutettu = True

            if b2.button(tr("selvitys_nappi", kieli), key=f"sel_{btn_id}", use_container_width=True):
                rv["hyvaksynta_tila"] = "selvitys"
                rv["hyvaksynta_pvm"]  = date.today().strftime("%d.%m.%Y")
                rv["hyvaksynta_klo"]  = __import__("datetime").datetime.now().strftime("%H:%M")
                rv["hyvaksynta_kuka"] = "Työnjohtaja"
                hyv_muutettu = True

            if b3.button(tr("palauta", kieli), key=f"pal_{btn_id}", use_container_width=True):
                rv["hyvaksynta_tila"]   = "odottaa"
                rv["hyvaksynta_pvm"]    = ""
                rv["hyvaksynta_klo"]    = ""
                rv["hyvaksynta_kuka"]   = ""
                rv["hyvaksynta_huomio"] = ""
                hyv_muutettu = True

            # Huomio-kenttä selvitys-tilassa
            if tila == "selvitys":
                uusi_hm = b4.text_input(
                    tr("selvityksen_syy", kieli),
                    value=hyv_hm,
                    key=f"hm_{btn_id}",
                    placeholder=tr("selvityksen_ph", kieli),
                )
                if uusi_hm != hyv_hm:
                    rv["hyvaksynta_huomio"] = uusi_hm
                    hyv_muutettu = True

            # ── Työnjohtajan kommentti ────────────────────────────────────────
            nyky_kommentti = rv.get("tj_kommentti", "")
            with st.expander(
                tr("tj_kommentti", kieli) + (f": {nyky_kommentti[:40]}…" if len(nyky_kommentti) > 40 else (f": {nyky_kommentti}" if nyky_kommentti else "")),
                expanded=bool(nyky_kommentti),
            ):
                uusi_kommentti = st.text_area(
                    tr("tj_kommentti", kieli),
                    value=nyky_kommentti,
                    key=f"tj_km_{btn_id}",
                    placeholder=tr("tj_kommentti_ph", kieli),
                    height=80,
                    label_visibility="collapsed",
                )
                k1, k2 = st.columns([1, 4])
                if k1.button(tr("tj_kommentti_tall", kieli), key=f"tj_tall_{btn_id}"):
                    rv["tj_kommentti"] = uusi_kommentti
                    tallenna_ali_tunnit(projekti, ali_rivit)
                    st.success(tr("kommentti_tall", kieli))
                    st.rerun()
                if nyky_kommentti and k2.button(tr("tj_kommentti_del", kieli), key=f"tj_del_{btn_id}"):
                    rv["tj_kommentti"] = ""
                    tallenna_ali_tunnit(projekti, ali_rivit)
                    st.rerun()

        if hyv_muutettu:
            tallenna_ali_tunnit(projekti, ali_rivit)
            st.rerun()

        # Yhteenveto hyväksyntätilanteesta
        n_hyv = sum(1 for r in vko_rivit if r.get("hyvaksynta_tila") == "hyvaksytty")
        n_sel = sum(1 for r in vko_rivit if r.get("hyvaksynta_tila") == "selvitys")
        n_odo = len(vko_rivit) - n_hyv - n_sel
        st.caption(f"✅ {n_hyv} {tr('hyv_yht',kieli)} &nbsp;·&nbsp; ⚠️ {n_sel} {tr('sel_yht',kieli)} &nbsp;·&nbsp; 🔵 {n_odo} {tr('odo_yht',kieli)}")

        # Metriikat
        st.divider()
        tot_h   = sum(r.get("yht_h",0) for r in vko_rivit)
        tot_eur = sum(
            (r.get("yht_h",0)*(r.get("tuntihinta") or 0) if r.get("laskutustapa")=="tuntihinta"
             else (r.get("kiintea_hinta") or 0) if r.get("laskutustapa")=="kiintea"
             else 0) for r in vko_rivit)
        c1,c2,c3 = st.columns(3)
        c1.metric(tr("tekijoita", kieli), len(vko_rivit))
        c2.metric(tr("tunteja_yht", kieli), f"{tot_h:.1f} h")
        c3.metric(tr("summa_yht", kieli), f"{tot_eur:,.0f} €" if tot_eur else "–")

        # Raportti
        st.divider()
        c1, c2 = st.columns([3,1])
        c1.markdown(f"**{tr('raportti_ohje', kieli)}**")
        if c2.button(tr("luo_raportti", kieli), type="primary"):
            xlsx = luo_viikkoraportti(
                rivit=ali_rivit, viikko=int(viikko), vuosi=int(vuosi),
                projekti=projekti, yritys="Uudenmaan Asbestipurku Oy")
            nm = f"Ali-tuntikirja_vko{viikko}_{_projekti_slug(projekti)}.xlsx"
            st.download_button(tr("lataa_excel", kieli), data=xlsx, file_name=nm,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Poisto
        with st.expander(tr("poista_kirjaus", kieli)):
            va = {f"{r['nimi']} – {r.get('yht_h',0):.1f}h": r["id"] for r in vko_rivit}
            pl = st.selectbox(tr("kirjaus", kieli), list(va.keys()))
            if st.button("Poista", type="secondary"):
                ali_rivit = [r for r in ali_rivit if r["id"] != va[pl]]
                tallenna_ali_tunnit(projekti, ali_rivit)
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TEKIJÄLISTA — aliurakoitsijoiden hallinta
# ══════════════════════════════════════════════════════════════════════════════
with tab_tekijat:
    st.subheader(tr("tab_tekijat", kieli))
    st.caption(tr("tekijat_ohje", kieli))

    # Näytä nykyinen lista
    if tyontekijat_lista:
        df_tek = pd.DataFrame(tyontekijat_lista)
        naytto_cols = ["nimi","yritys","ammattinimike","laskutustapa","tuntihinta","kiintea_hinta"]
        naytto_cols = [c for c in naytto_cols if c in df_tek.columns]
        naytto = df_tek[naytto_cols].copy()
        naytto.columns = [c.replace("_"," ").title() for c in naytto_cols]
        st.dataframe(naytto, use_container_width=True, hide_index=True)
        st.divider()

    # Lisää uusi
    with st.expander(tr("lisaa_tekija", kieli), expanded=len(tyontekijat_lista)==0):
        t1, t2 = st.columns(2)
        t_nimi  = t1.text_input(tr("nimi", kieli), key="t_nimi")
        t_yrit  = t1.text_input(tr("yritys", kieli), key="t_yrit")

        # Ammattinimike — täyttää tuntihinnan automaattisesti
        nimike_lista = [n["nimike"] for n in ammattinimikkeet] + ["— Muu —"]
        t_nimike = t1.selectbox("Ammattinimike", nimike_lista, key="t_nimike")
        if t_nimike != "— Muu —":
            nimike_info = next((n for n in ammattinimikkeet if n["nimike"] == t_nimike), {})
            t1.caption(f"{nimike_info.get('kuvaus','')}  |  {nimike_info.get('tuntihinta',0):.0f} €/h")

        t_lp = t2.selectbox(tr("laskutustapa", kieli), LASK_TAVAT, key="t_lp")
        t_th, t_kh = None, None
        if t_lp == LASK_TAVAT[1]:
            oletus_th = _nimike_hinnat.get(t_nimike, 38.0) if t_nimike != "— Muu —" else 38.0
            t_th = t2.number_input("€/h", 0.0, step=0.5, value=oletus_th, key="t_th")
        elif t_lp == LASK_TAVAT[2]:
            t_kh = t2.number_input(tr("kiintea_hinta", kieli), 0.0, step=10.0, key="t_kh")

        if st.button(tr("lisaa", kieli), type="primary", key="t_lisaa"):
            if not t_nimi:
                st.error(tr("syota_nimi", kieli))
            elif any(tk["nimi"] == t_nimi for tk in tyontekijat_lista):
                st.warning(f"{t_nimi} {tr('jo_listalla', kieli)}")
            else:
                lm = {LASK_TAVAT[0]:"tunnit", LASK_TAVAT[1]:"tuntihinta", LASK_TAVAT[2]:"kiintea"}
                tyontekijat_lista.append({
                    "nimi":          t_nimi,
                    "yritys":        t_yrit,
                    "ammattinimike": t_nimike if t_nimike != "— Muu —" else "",
                    "laskutustapa":  lm.get(t_lp, "tunnit"),
                    "tuntihinta":    t_th,
                    "kiintea_hinta": t_kh,
                })
                _tallenna_tyontekijat(tyontekijat_lista)
                st.success(f"✅ {t_nimi} ({t_nimike})")
                st.rerun()

    # Poista listalta
    if tyontekijat_lista:
        with st.expander(tr("poista_tekija", kieli)):
            nimet_p = [tk["nimi"] for tk in tyontekijat_lista]
            poistettava = st.selectbox(tr("tekija", kieli), nimet_p, key="t_poisto")
            if st.button(tr("poista_listalta", kieli), type="secondary", key="t_poista"):
                tyontekijat_lista = [tk for tk in tyontekijat_lista if tk["nimi"] != poistettava]
                _tallenna_tyontekijat(tyontekijat_lista)
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PROJEKTIT (vain työnjohtaja)
# ══════════════════════════════════════════════════════════════════════════════
if tab_projektit is not None:
    with tab_projektit:
        ptab1, ptab2 = st.tabs(["📁 Projektit", "🔨 Ammattinimikkeet"])

        # ══════════════════════════════════════════════════════════════════
        # PROJEKTIT
        # ══════════════════════════════════════════════════════════════════
        with ptab1:
            st.subheader("📁 Projektienhallinta")
            rekisteri = lataa_projektirekisteri()

            # ── Uusi projekti ──────────────────────────────────────────────
            KAIKKI_KUSTPAIKAT = ["Urakka", "Lisätyö", "Vesivahinko"]

            with st.expander("➕ Luo uusi projekti", expanded=len(rekisteri)==0):
                np1, np2 = st.columns(2)
                uusi_nimi   = np1.text_input("Projektin nimi",
                              placeholder="esim. Valteri-koulu, Tenholantie 15", key="np_nimi")
                uusi_kuvaus = np1.text_input("Lyhyt kuvaus",
                              placeholder="esim. Asbestipurku 5 krs", key="np_kuv")
                uusi_tilaaja = np1.text_input("Tilaaja",
                               placeholder="esim. Mirlux Oy / Lalli Kuoppala", key="np_tilaaja")

                uusi_koodi  = np2.text_input(
                    "Projektikoodi (6 merkkiä)", value=_luo_koodi(), max_chars=6,
                    key="np_koodi",
                    help="Tämä koodi annetaan aliurakoitsijoille kirjautumiseen").upper()
                np2.caption("Muuta koodi haluamaksesi tai käytä automaattista.")

                uusi_kustpaikat = np2.multiselect(
                    "Kustannuspaikat (kategoriat)",
                    KAIKKI_KUSTPAIKAT,
                    default=KAIKKI_KUSTPAIKAT,
                    key="np_kp",
                    help="Valitse vakiokategoriat",
                )
                uusi_omat_kp = np2.text_input(
                    "Omat kategoriat (pilkulla eroteltuna)",
                    placeholder="esim. Huoltotyö, Siivous, Övertid",
                    key="np_omat_kp",
                    help="Lisää omia projektikohtaisia kategorioita vakioiden lisäksi",
                )
                uusi_th_oletus = np2.number_input(
                    "Oletustuntihinta (€/h)", value=38.0, step=0.5, key="np_th",
                    help="Käytetään jos tekijälle ei ole asetettu ammattinimikettä")

                if st.button("Luo projekti", type="primary", key="np_luo"):
                    if not uusi_nimi:
                        st.error("Syötä projektin nimi.")
                    elif any(p["koodi"] == uusi_koodi for p in rekisteri):
                        st.error(f"Koodi {uusi_koodi} on jo käytössä. Valitse toinen.")
                    else:
                        omat = [k.strip() for k in uusi_omat_kp.split(",") if k.strip()]
                        kaikki_kp = uusi_kustpaikat + [k for k in omat if k not in uusi_kustpaikat]
                        rekisteri.append({
                            "nimi":              uusi_nimi,
                            "koodi":             uusi_koodi,
                            "kuvaus":            uusi_kuvaus,
                            "tilaaja":           uusi_tilaaja,
                            "kustannuspaikat":   kaikki_kp or KAIKKI_KUSTPAIKAT,
                            "tuntihinta_oletus": uusi_th_oletus,
                            "luotu":             date.today().isoformat(),
                            "tila":              "aktiivinen",
                        })
                        tallenna_projektirekisteri(rekisteri)
                        st.success(f"✅ Projekti **{uusi_nimi}** luotu!  \n"
                                   f"Aliurakoitsijat kirjautuvat koodilla: **`{uusi_koodi}`**")
                        st.rerun()

            # ── Projektilista ──────────────────────────────────────────────
            st.divider()
            for p in rekisteri:
                tila_emoji = "🟢" if p.get("tila") == "aktiivinen" else "⚫"
                c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
                kp = ", ".join(p.get("kustannuspaikat", ["Urakka","Lisätyö","Vesivahinko"]))
                c1.markdown(f"{tila_emoji} **{p['nimi']}**  \n"
                            f"{p.get('kuvaus','')}  \n"
                            f"Tilaaja: {p.get('tilaaja','–')}  ·  Kp: {kp}  ·  {p.get('tuntihinta_oletus',38):.0f} €/h")
                c2.code(p["koodi"])
                c2.caption(p.get("luotu",""))

                if p.get("tila") == "aktiivinen":
                    if c3.button("✅ Valmis", key=f"valmis_{p['koodi']}", use_container_width=True):
                        rivit = lataa_ali_tunnit(p["nimi"])
                        tunnit_yht = sum(r.get("yht_h",0) for r in rivit)
                        viikot_set = set(r.get("viikko",0) for r in rivit)
                        tallenna_projekti_yhteenveto(p["nimi"], {
                            "valmistunut":   date.today().isoformat(),
                            "nimi":          p["nimi"],
                            "kuvaus":        p.get("kuvaus",""),
                            "kesto_viikkoja":len(viikot_set),
                            "tunnit_yht":    tunnit_yht,
                            "urakka_h":      sum(r.get("yht_h",0) for r in rivit if r.get("kategoria")=="Urakka"),
                            "lisatyo_h":     sum(r.get("yht_h",0) for r in rivit if r.get("kategoria")=="Lisätyö"),
                            "tekijoita":     len(set(r.get("nimi","") for r in rivit)),
                        })
                        p["tila"] = "valmis"
                        tallenna_projektirekisteri(rekisteri)
                        st.success("Projekti valmis, tallennettu historiaan.")
                        st.rerun()
                else:
                    c3.caption("⚫ Valmis")

                if c4.button("🗑️", key=f"poista_p_{p['koodi']}", use_container_width=True):
                    rekisteri = [r for r in rekisteri if r["koodi"] != p["koodi"]]
                    tallenna_projektirekisteri(rekisteri)
                    st.rerun()
                st.divider()

        # ══════════════════════════════════════════════════════════════════
        # AMMATTINIMIKKEET
        # ══════════════════════════════════════════════════════════════════
        with ptab2:
            st.subheader("🔨 Ammattinimikkeet ja tuntihinnat")
            st.caption("Ammattinimike valitaan tekijälistalla — tuntihinta täyttyy automaattisesti.")

            # Näytä nykyinen lista
            if ammattinimikkeet:
                df_nim = pd.DataFrame(ammattinimikkeet)
                df_nim.columns = ["Nimike", "Kuvaus", "€/h"]
                st.dataframe(df_nim, use_container_width=True, hide_index=True)
                st.divider()

            # Lisää uusi
            with st.expander("➕ Lisää ammattinimike", expanded=False):
                an1, an2 = st.columns(2)
                an_nimike = an1.text_input("Nimike (lyhenne)", placeholder="esim. RAM", key="an_nimike")
                an_kuvaus = an1.text_input("Kuvaus (vapaaehtoinen)",
                                           placeholder="esim. Rakennusammattimiehen", key="an_kuv")
                an_th     = an2.number_input("Tuntihinta (€/h)", min_value=0.0,
                                             value=38.0, step=0.5, key="an_th")
                if st.button("Lisää nimike", type="primary", key="an_lisaa"):
                    if not an_nimike:
                        st.error("Syötä nimike.")
                    elif any(n["nimike"] == an_nimike for n in ammattinimikkeet):
                        st.warning(f"{an_nimike} on jo listalla.")
                    else:
                        ammattinimikkeet.append({
                            "nimike": an_nimike,
                            "kuvaus": an_kuvaus,
                            "tuntihinta": an_th,
                        })
                        tallenna_ammattinimikkeet(ammattinimikkeet)
                        st.success(f"✅ {an_nimike} — {an_th:.0f} €/h lisätty!")
                        st.rerun()

            # Muokkaa hintaa
            if ammattinimikkeet:
                with st.expander("✏️ Muokkaa tuntihintaa"):
                    muok_nim = st.selectbox("Nimike", [n["nimike"] for n in ammattinimikkeet], key="muok_nim")
                    muok_obj = next(n for n in ammattinimikkeet if n["nimike"] == muok_nim)
                    muok_th  = st.number_input("Uusi tuntihinta (€/h)", value=muok_obj["tuntihinta"],
                                               step=0.5, key="muok_th")
                    if st.button("Tallenna muutos", type="primary", key="muok_tall"):
                        muok_obj["tuntihinta"] = muok_th
                        tallenna_ammattinimikkeet(ammattinimikkeet)
                        st.success(f"✅ {muok_nim}: {muok_th:.0f} €/h päivitetty.")
                        st.rerun()

                with st.expander("🗑️ Poista nimike"):
                    poista_nim = st.selectbox("Nimike", [n["nimike"] for n in ammattinimikkeet], key="poista_nim")
                    if st.button("Poista", type="secondary", key="poista_nim_btn"):
                        ammattinimikkeet = [n for n in ammattinimikkeet if n["nimike"] != poista_nim]
                        tallenna_ammattinimikkeet(ammattinimikkeet)
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# HISTORIA (vain työnjohtaja)
# ══════════════════════════════════════════════════════════════════════════════
if tab_historia is not None:
    with tab_historia:
        st.subheader("📈 Projektihistoria — pohjatietoa tarjouslaskentaan")

        rekisteri = lataa_projektirekisteri()
        valmiit = [p for p in rekisteri if p.get("tila") == "valmis"]

        if not valmiit:
            st.info("Ei vielä valmiita projekteja. Merkitse projekti valmiiksi Projektit-välilehdellä "
                    "kun se päättyy — tiedot tallentuvat automaattisesti historiatietokantaan.")
        else:
            yhteenvedot = []
            for p in valmiit:
                yht = lataa_projekti_yhteenveto(p["nimi"])
                if yht:
                    yhteenvedot.append(yht)

            if yhteenvedot:
                import pandas as pd
                df_h = pd.DataFrame(yhteenvedot)

                # Metriikat
                st.markdown("### Keskiarvot valmiista projekteista")
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Projekteja", len(yhteenvedot))
                c2.metric("Tunnit / projekti (ka.)", f"{df_h['tunnit_yht'].mean():.0f} h")
                c3.metric("Kesto / projekti (ka.)", f"{df_h['kesto_viikkoja'].mean():.1f} vko")
                c4.metric("Tekijöitä / projekti (ka.)", f"{df_h['tekijoita'].mean():.1f}")

                st.divider()
                st.markdown("### Projektit")
                naytto = df_h[["nimi","valmistunut","kesto_viikkoja","tunnit_yht",
                                "urakka_h","lisatyo_h","tekijoita"]].copy()
                naytto.columns = ["Projekti","Valmistui","Kesto (vko)","Tunnit yht.",
                                   "Urakka (h)","Lisätyö (h)","Tekijöitä"]
                st.dataframe(naytto, use_container_width=True, hide_index=True)

                st.divider()
                st.markdown("### 💡 Tarjouslaskennan apuväline")
                st.markdown("Anna projektin koko (tunnit) niin lasketaan arvio kustannuksista "
                            "historiatietojen perusteella.")
                arvio_h = st.number_input("Arvioitu tuntimäärä uudelle projektille",
                                          min_value=0, step=10, value=500)
                if arvio_h > 0 and len(yhteenvedot) > 1:
                    urakka_osuus = df_h["urakka_h"].sum() / df_h["tunnit_yht"].sum()
                    lisatyo_osuus = 1 - urakka_osuus
                    st.markdown(f"""
                    **Arvio {arvio_h} tunnin projektille** (perustuu {len(yhteenvedot)} vanhaan projektiin):

                    | | Arvio |
                    |---|---|
                    | Urakkatunnit | {arvio_h * urakka_osuus:.0f} h ({urakka_osuus*100:.0f} %) |
                    | Lisätyötunnit | {arvio_h * lisatyo_osuus:.0f} h ({lisatyo_osuus*100:.0f} %) |
                    | Kesto | ~{arvio_h / df_h['tunnit_yht'].mean() * df_h['kesto_viikkoja'].mean():.1f} viikkoa |
                    | Tekijöitä | ~{arvio_h / df_h['tunnit_yht'].mean() * df_h['tekijoita'].mean():.1f} henkilöä |
                    """)
