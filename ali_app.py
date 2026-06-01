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

from storage import lataa_ali_tunnit, tallenna_ali_tunnit, hae_projektit
from raportti_ali import luo_viikkoraportti
from translations import t, paivat as _paivat_nimet, kategoriat, laskutustavat

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
    return f"{td['emoji']} {t(td['tila_avain'], kieli)}"

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
asetukset = _lataa_asetukset()
tyontekijat_lista = _lataa_tyontekijat()

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

    # Projekti
    projektit = _hae_projektit()
    projekti_oletus = asetukset.get("projekti", "")
    if projekti_oletus not in projektit:
        projektit = [projekti_oletus] + projektit if projekti_oletus else projektit
    projekti = st.text_input(
        t("projekti", kieli),
        value=projekti_oletus,
        placeholder=t("projekti_ph", kieli),
    )

    # Viikko ja vuosi
    tana = date.today()
    vuosi  = st.number_input(t("vuosi", kieli),  value=asetukset.get("vuosi",  tana.year),  step=1, format="%d")
    viikko = st.number_input(t("viikko", kieli), value=asetukset.get("viikko", int(tana.strftime("%V"))),
                              min_value=1, max_value=53, step=1)

    # Näytä viikon päivät
    paivat      = _viikon_paivat(int(vuosi), int(viikko))
    PAIVAT_NYK  = _paivat_nimet(kieli)
    KATEGORIAT  = kategoriat(kieli)
    LASK_TAVAT  = laskutustavat(kieli)

    st.caption(" · ".join(f"{P} {p.strftime('%-d.%-m.')}" for P, p in zip(PAIVAT_NYK, paivat)))
    st.divider()

    # Oletuskategoria
    kat_oletus = asetukset.get("kategoria", KATEGORIAT[0])
    kat_idx    = KATEGORIAT.index(kat_oletus) if kat_oletus in KATEGORIAT else 0
    oletus_kat = st.selectbox(t("oletus_kat", kieli), KATEGORIAT, index=kat_idx)

    st.divider()
    st.caption(f"🔗 {t('paasovellus', kieli)}: http://localhost:8501")

kieli = st.session_state.get("kieli", "fi")
st.title(f"👷 {t('app_title', kieli)}")
st.caption(t("app_caption", kieli))

# Tallenna viimeksi käytetyt asetukset
_tallenna_asetukset({
    "projekti": projekti,
    "vuosi": int(vuosi),
    "viikko": int(viikko),
    "kategoria": oletus_kat,
})

if not projekti:
    st.warning("Aseta projektin nimi sivupalkissa.")
    st.stop()

# Lataa projektin ali-tuntikirja
ali_rivit: list = lataa_ali_tunnit(projekti)

# ── VÄLILEHDET ──────────────────────────────────────────────────────────────────
tab_pikasyotto, tab_yksittainen, tab_vkoyht, tab_tekijat = st.tabs([
    t("tab_pikasyotto", kieli),
    t("tab_yksittainen", kieli),
    t("tab_vkoyht", kieli),
    t("tab_tekijat", kieli),
])

# ══════════════════════════════════════════════════════════════════════════════
# PIKASYÖTTÖ — kaikki tekijät kerralla taulukossa
# ══════════════════════════════════════════════════════════════════════════════
with tab_pikasyotto:
    st.subheader(f"Viikko {viikko} / {vuosi} — pikasyöttö")
    st.caption("Täytä taulukko ja paina Tallenna. Tyhjät = 0 h.")

    if not tyontekijat_lista:
        st.info(t("ei_tekijoita", kieli))
    else:
        # Rakenna syöttötaulukko
        # Hae nykyiset tallennukset tälle viikolle esitäyttöä varten
        vko_nyky = {r["nimi"]: r for r in ali_rivit
                    if r.get("viikko") == int(viikko)}

        paiva_otsikot = [f"{P}\n{p.strftime('%-d.%-m.')}" for P, p in zip(PAIVAT, paivat)]

        # Luo DataFrame esitäytöllä
        rivit_data = []
        for t in tyontekijat_lista:
            nimi = t["nimi"]
            nyky = vko_nyky.get(nimi, {})
            rivi = {"Nimi": nimi, "Yritys": t.get("yritys", "")}
            for pk, po in zip(PAIVA_AVAIN, paiva_otsikot):
                rivi[po] = float(nyky.get(pk, 0) or 0)
            rivi["Kategoria"] = nyky.get("kategoria", oletus_kat)
            rivit_data.append(rivi)

        df_syotto = pd.DataFrame(rivit_data)

        # Kategoria-sarake: selectbox-valinnat
        kategoria_valinnat = {r["Nimi"]: r["Kategoria"] for r in rivit_data}

        # Päivä-sarakkeiden config
        sarake_config = {
            "Nimi":     st.column_config.TextColumn(t("taulukko_nimi",kieli), disabled=True, width="medium"),
            "Yritys":   st.column_config.TextColumn(t("taulukko_yritys",kieli), disabled=True, width="medium"),
            "Kategoria": st.column_config.SelectboxColumn(
                t("kategoria",kieli), options=KATEGORIAT, width="small"),
        }
        for po in paiva_otsikot:
            sarake_config[po] = st.column_config.NumberColumn(
                po, min_value=0.0, max_value=24.0, step=0.5, format="%.1f", width="small")

        df_muokattu = st.data_editor(
            df_syotto,
            column_config=sarake_config,
            hide_index=True,
            use_container_width=True,
            key=f"pikasyotto_{viikko}_{vuosi}",
        )

        # Työnjohtajan kommentit pikasyötössä (vain jos on)
        kommentit = [(t["nimi"], next((r.get("tj_kommentti","") for r in ali_rivit
                      if r.get("viikko")==int(viikko) and r.get("vuosi",int(vuosi))==int(vuosi)
                      and r.get("nimi")==t["nimi"]), ""))
                     for t in tyontekijat_lista]
        kommentit_olemassa = [k for k in kommentit if k[1].strip()]
        if kommentit_olemassa:
            st.markdown("---")
            for nimi, km in kommentit_olemassa:
                st.markdown(
                    f"<div style='background:#FFF3CD;border-left:4px solid #FFC107;"
                    f"border-radius:4px;padding:8px 12px;margin:3px 0;font-size:0.9em'>"
                    f"💬 <b>{nimi}:</b> {km}</div>",
                    unsafe_allow_html=True,
                )

        # Yhteensä-rivi
        yht_per_paiva = {po: df_muokattu[po].sum() for po in paiva_otsikot}
        yht_kaikki    = sum(yht_per_paiva.values())
        cols = st.columns(len(PAIVAT) + 3)
        cols[0].caption("**YHT.**")
        cols[1].caption("")
        for i, (po, yht) in enumerate(yht_per_paiva.items()):
            cols[i+2].metric("", f"{yht:.1f}h" if yht else "–")
        cols[-1].metric("Kaikki", f"{yht_kaikki:.1f} h")

        st.divider()

        # ── Päiväkohtaiset huomiot pikasyötössä ──────────────────────────────
        with st.expander(t("pv_huomiot", kieli), expanded=False):
            st.caption(t("tunnit_pv", kieli))
            pika_huomiot = {}  # {nimi: {pk: teksti}}
            for t in tyontekijat_lista:
                nimi = t["nimi"]
                nyky_hm = next(
                    (r.get("huomiot", {}) for r in ali_rivit
                     if r.get("viikko") == int(viikko)
                     and r.get("vuosi", int(vuosi)) == int(vuosi)
                     and r.get("nimi") == nimi),
                    {}
                )
                st.markdown(f"**{nimi}**")
                hm_cols = st.columns(7)
                pika_huomiot[nimi] = {}
                for i, (P, pk, p) in enumerate(zip(PAIVAT, PAIVA_AVAIN, paivat)):
                    pika_huomiot[nimi][pk] = hm_cols[i].text_input(
                        f"{P} {p.strftime('%-d.%-m.')}",
                        value=nyky_hm.get(pk, ""),
                        key=f"pika_hm_{nimi}_{pk}",
                        placeholder="–",
                    )

        if st.button(t("tallenna_kaikki", kieli), type="primary", use_container_width=True):
            tallennettu = 0
            for _, row in df_muokattu.iterrows():
                nimi = row["Nimi"]
                tunnit = {pk: float(row[po]) for pk, po in zip(PAIVA_AVAIN, paiva_otsikot)}
                yht_h  = sum(tunnit.values())
                t_info = next((t for t in tyontekijat_lista if t["nimi"] == nimi), {})

                uusi = {
                    "id":        f"{viikko}_{vuosi}_{nimi}".replace(" ","_"),
                    "viikko":    int(viikko),
                    "vuosi":     int(vuosi),
                    "nimi":      nimi,
                    "yritys":    row["Yritys"],
                    "kategoria": row["Kategoria"],
                    **tunnit,
                    "yht_h":          yht_h,
                    "laskutustapa":   t_info.get("laskutustapa", "tunnit"),
                    "tuntihinta":     t_info.get("tuntihinta"),
                    "kiintea_hinta":  t_info.get("kiintea_hinta"),
                    "huomio":         "",
                    "huomiot":        pika_huomiot.get(nimi, {}),
                }
                ali_rivit = [r for r in ali_rivit
                             if not (r.get("viikko") == int(viikko)
                                     and r.get("vuosi", int(vuosi)) == int(vuosi)
                                     and r.get("nimi") == nimi)]
                ali_rivit.append(uusi)
                tallennettu += 1

            tallenna_ali_tunnit(projekti, ali_rivit)
            st.success(f"{t('tallennettu', kieli)}: {tallennettu} — {t('viikko', kieli)} {viikko}/{vuosi}")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# YKSITTÄINEN SYÖTTÖ
# ══════════════════════════════════════════════════════════════════════════════
with tab_yksittainen:
    st.subheader(t("tab_yksittainen", kieli))

    nimet = [tk["nimi"] for tk in tyontekijat_lista]
    if not nimet:
        st.info(t("ei_tekijoita", kieli))
    else:
        col_vas, col_oik = st.columns([1, 2])
        with col_vas:
            valittu_nimi = st.selectbox(t("tekija", kieli), nimet)
            t_info = next((tk for tk in tyontekijat_lista if tk["nimi"] == valittu_nimi), {})
            st.caption(f"{t('yritys', kieli)}: {t_info.get('yritys','–')}")

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

            yk_kat = st.selectbox(t("kategoria", kieli), KATEGORIAT,
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
            st.markdown(f"**{t('tunnit_pv', kieli)}**")
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
                    t("huomio", kieli),
                    value=oletus_hm,
                    key=f"yk_hm_{pk}",
                    placeholder=t("huomio_ph", kieli),
                    label_visibility="collapsed",
                )

            yht_h = sum(h_arvot.values())

            # Pikasyöttönapit
            st.markdown(f"**{t('lisaa_tunnit', kieli)}**")
            btn_cols = st.columns(5)
            for lisays in [6, 7, 8, 9, 10]:
                if btn_cols[lisays-6].button(f"+{lisays}h ark", key=f"btn_{lisays}"):
                    for pk in ["ma","ti","ke","to","pe"]:
                        h_arvot[pk] = float(lisays)
                    yht_h = sum(h_arvot.values())

        huomio = st.text_input(t("yleinen_huomio", kieli), key="yk_huomio")

        c1, c2 = st.columns(2)
        c1.metric("Tunnit yhteensä", f"{yht_h:.1f} h")
        if lp == "tuntihinta" and t_info.get("tuntihinta"):
            c2.metric("Summa", f"{yht_h * t_info['tuntihinta']:,.0f} €")

        if st.button(t("tallenna", kieli), type="primary", use_container_width=True, key="yk_tall"):
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
            st.success(f"✅ {valittu_nimi} — {yht_h:.1f} h {t('tallennettu', kieli).replace('✅ ','').lower()}!")
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
        st.info(t("ei_kirjauksia", kieli))
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
            rivi[t("taulukko_yht",kieli)]   = yht
            rivi[t("taulukko_summa",kieli)] = f"{summa:,.0f}" if summa else "–"
            rivi[t("taulukko_tila",kieli)]  = _tila_badge(rv.get("hyvaksynta_tila","odottaa"), kieli)
            tbl.append(rivi)

        df_yht = pd.DataFrame(tbl)
        st.dataframe(df_yht, use_container_width=True, hide_index=True)

        # Päiväkohtaiset huomiot yhteenvedossa
        huomiot_olemassa = any(
            any(v for v in r.get("huomiot", {}).values())
            for r in vko_rivit
        )
        if huomiot_olemassa:
            with st.expander(t("pv_huomiot", kieli), expanded=False):
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
        st.markdown(f"### {t('hyvaksynta', kieli)}")

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

            if b1.button(t("hyvaksy", kieli), key=f"hyv_{btn_id}", use_container_width=True):
                rv["hyvaksynta_tila"]   = "hyvaksytty"
                rv["hyvaksynta_pvm"]    = date.today().strftime("%d.%m.%Y")
                rv["hyvaksynta_klo"]    = __import__("datetime").datetime.now().strftime("%H:%M")
                rv["hyvaksynta_kuka"]   = "Työnjohtaja"
                rv["hyvaksynta_huomio"] = ""
                hyv_muutettu = True

            if b2.button(t("selvitys_nappi", kieli), key=f"sel_{btn_id}", use_container_width=True):
                rv["hyvaksynta_tila"] = "selvitys"
                rv["hyvaksynta_pvm"]  = date.today().strftime("%d.%m.%Y")
                rv["hyvaksynta_klo"]  = __import__("datetime").datetime.now().strftime("%H:%M")
                rv["hyvaksynta_kuka"] = "Työnjohtaja"
                hyv_muutettu = True

            if b3.button(t("palauta", kieli), key=f"pal_{btn_id}", use_container_width=True):
                rv["hyvaksynta_tila"]   = "odottaa"
                rv["hyvaksynta_pvm"]    = ""
                rv["hyvaksynta_klo"]    = ""
                rv["hyvaksynta_kuka"]   = ""
                rv["hyvaksynta_huomio"] = ""
                hyv_muutettu = True

            # Huomio-kenttä selvitys-tilassa
            if tila == "selvitys":
                uusi_hm = b4.text_input(
                    t("selvityksen_syy", kieli),
                    value=hyv_hm,
                    key=f"hm_{btn_id}",
                    placeholder=t("selvityksen_ph", kieli),
                )
                if uusi_hm != hyv_hm:
                    rv["hyvaksynta_huomio"] = uusi_hm
                    hyv_muutettu = True

            # ── Työnjohtajan kommentti ────────────────────────────────────────
            nyky_kommentti = rv.get("tj_kommentti", "")
            with st.expander(
                t("tj_kommentti", kieli) + (f": {nyky_kommentti[:40]}…" if len(nyky_kommentti) > 40 else (f": {nyky_kommentti}" if nyky_kommentti else "")),
                expanded=bool(nyky_kommentti),
            ):
                uusi_kommentti = st.text_area(
                    t("tj_kommentti", kieli),
                    value=nyky_kommentti,
                    key=f"tj_km_{btn_id}",
                    placeholder=t("tj_kommentti_ph", kieli),
                    height=80,
                    label_visibility="collapsed",
                )
                k1, k2 = st.columns([1, 4])
                if k1.button(t("tj_kommentti_tall", kieli), key=f"tj_tall_{btn_id}"):
                    rv["tj_kommentti"] = uusi_kommentti
                    tallenna_ali_tunnit(projekti, ali_rivit)
                    st.success(t("kommentti_tall", kieli))
                    st.rerun()
                if nyky_kommentti and k2.button(t("tj_kommentti_del", kieli), key=f"tj_del_{btn_id}"):
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
        st.caption(f"✅ {n_hyv} {t('hyv_yht',kieli)} &nbsp;·&nbsp; ⚠️ {n_sel} {t('sel_yht',kieli)} &nbsp;·&nbsp; 🔵 {n_odo} {t('odo_yht',kieli)}")

        # Metriikat
        st.divider()
        tot_h   = sum(r.get("yht_h",0) for r in vko_rivit)
        tot_eur = sum(
            (r.get("yht_h",0)*(r.get("tuntihinta") or 0) if r.get("laskutustapa")=="tuntihinta"
             else (r.get("kiintea_hinta") or 0) if r.get("laskutustapa")=="kiintea"
             else 0) for r in vko_rivit)
        c1,c2,c3 = st.columns(3)
        c1.metric(t("tekijoita", kieli), len(vko_rivit))
        c2.metric(t("tunteja_yht", kieli), f"{tot_h:.1f} h")
        c3.metric(t("summa_yht", kieli), f"{tot_eur:,.0f} €" if tot_eur else "–")

        # Raportti
        st.divider()
        c1, c2 = st.columns([3,1])
        c1.markdown(f"**{t('raportti_ohje', kieli)}**")
        if c2.button(t("luo_raportti", kieli), type="primary"):
            xlsx = luo_viikkoraportti(
                rivit=ali_rivit, viikko=int(viikko), vuosi=int(vuosi),
                projekti=projekti, yritys="Uudenmaan Asbestipurku Oy")
            nm = f"Ali-tuntikirja_vko{viikko}_{_projekti_slug(projekti)}.xlsx"
            st.download_button(t("lataa_excel", kieli), data=xlsx, file_name=nm,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Poisto
        with st.expander(t("poista_kirjaus", kieli)):
            va = {f"{r['nimi']} – {r.get('yht_h',0):.1f}h": r["id"] for r in vko_rivit}
            pl = st.selectbox(t("kirjaus", kieli), list(va.keys()))
            if st.button("Poista", type="secondary"):
                ali_rivit = [r for r in ali_rivit if r["id"] != va[pl]]
                tallenna_ali_tunnit(projekti, ali_rivit)
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TEKIJÄLISTA — aliurakoitsijoiden hallinta
# ══════════════════════════════════════════════════════════════════════════════
with tab_tekijat:
    st.subheader(t("tab_tekijat", kieli))
    st.caption(t("tekijat_ohje", kieli))

    # Näytä nykyinen lista
    if tyontekijat_lista:
        df_tek = pd.DataFrame(tyontekijat_lista)
        naytto_cols = ["nimi","yritys","laskutustapa","tuntihinta","kiintea_hinta"]
        naytto_cols = [c for c in naytto_cols if c in df_tek.columns]
        naytto = df_tek[naytto_cols].copy()
        naytto.columns = [c.replace("_"," ").title() for c in naytto_cols]
        st.dataframe(naytto, use_container_width=True, hide_index=True)
        st.divider()

    # Lisää uusi
    with st.expander(t("lisaa_tekija", kieli), expanded=len(tyontekijat_lista)==0):
        t1, t2 = st.columns(2)
        t_nimi = t1.text_input(t("nimi", kieli), key="t_nimi")
        t_yrit = t1.text_input(t("yritys", kieli), key="t_yrit")
        t_lp   = t2.selectbox(t("laskutustapa", kieli), LASK_TAVAT, key="t_lp")
        t_th, t_kh = None, None
        if t_lp == LASK_TAVAT[1]:   # tuntihinta
            t_th = t2.number_input("€/h", 0.0, step=1.0, value=38.0, key="t_th")
        elif t_lp == LASK_TAVAT[2]: # kiinteä
            t_kh = t2.number_input(t("kiintea_hinta", kieli), 0.0, step=10.0, key="t_kh")

        if st.button(t("lisaa", kieli), type="primary", key="t_lisaa"):
            if not t_nimi:
                st.error(t("syota_nimi", kieli))
            elif any(tk["nimi"] == t_nimi for tk in tyontekijat_lista):
                st.warning(f"{t_nimi} {t('jo_listalla', kieli)}")
            else:
                lm = {LASK_TAVAT[0]:"tunnit", LASK_TAVAT[1]:"tuntihinta", LASK_TAVAT[2]:"kiintea"}
                tyontekijat_lista.append({
                    "nimi": t_nimi, "yritys": t_yrit,
                    "laskutustapa": lm.get(t_lp, "tunnit"),
                    "tuntihinta": t_th, "kiintea_hinta": t_kh,
                })
                _tallenna_tyontekijat(tyontekijat_lista)
                st.success(f"✅ {t_nimi}")
                st.rerun()

    # Poista listalta
    if tyontekijat_lista:
        with st.expander(t("poista_tekija", kieli)):
            nimet_p = [tk["nimi"] for tk in tyontekijat_lista]
            poistettava = st.selectbox(t("tekija", kieli), nimet_p, key="t_poisto")
            if st.button(t("poista_listalta", kieli), type="secondary", key="t_poista"):
                tyontekijat_lista = [tk for tk in tyontekijat_lista if tk["nimi"] != poistettava]
                _tallenna_tyontekijat(tyontekijat_lista)
                st.rerun()
