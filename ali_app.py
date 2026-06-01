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

# ── Apufunktiot ────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
TYONTEKIJAT_POLKU = DATA_DIR / "_aliurakoitsijat.json"
ASETUKSET_POLKU   = DATA_DIR / "_ali_asetukset.json"

PAIVAT      = ["Ma","Ti","Ke","To","Pe","La","Su"]
PAIVA_AVAIN = ["ma","ti","ke","to","pe","la","su"]
KATEGORIAT  = ["Urakka","Lisätyö","Vesivahinko"]

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

st.title("👷 Aliurakoitsijoiden tuntikirja")
st.caption("Uudenmaan Asbestipurku Oy")

# ── Tallennetut asetukset ──────────────────────────────────────────────────────
asetukset = _lataa_asetukset()
tyontekijat_lista = _lataa_tyontekijat()  # [{nimi, yritys, laskutustapa, tuntihinta, kiintea}]

# ── SIVUPALKKI ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Projekti & viikko")

    # Projekti
    projektit = _hae_projektit()
    projekti_oletus = asetukset.get("projekti", "")
    if projekti_oletus not in projektit:
        projektit = [projekti_oletus] + projektit if projekti_oletus else projektit
    projekti = st.text_input(
        "Projektin nimi",
        value=projekti_oletus,
        placeholder="esim. Valteri-koulu, Tenholantie 15",
    )

    # Viikko ja vuosi
    tana = date.today()
    vuosi   = st.number_input("Vuosi",  value=asetukset.get("vuosi",  tana.year),  step=1, format="%d")
    viikko  = st.number_input("Viikko", value=asetukset.get("viikko", int(tana.strftime("%V"))),
                               min_value=1, max_value=53, step=1)

    # Näytä viikon päivät
    paivat = _viikon_paivat(int(vuosi), int(viikko))
    st.caption(" · ".join(f"{P} {p.strftime('%-d.%-m.')}" for P, p in zip(PAIVAT, paivat)))

    st.divider()

    # Oletuskategoria
    kat_oletus = asetukset.get("kategoria", "Urakka")
    kat_idx    = KATEGORIAT.index(kat_oletus) if kat_oletus in KATEGORIAT else 0
    oletus_kat = st.selectbox("Oletuskategoria", KATEGORIAT, index=kat_idx)

    st.divider()
    st.caption("🔗 Pääsovellus: http://localhost:8501")

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
    "⚡ Pikasyöttö",
    "👤 Yksittäinen",
    "📊 Viikkoyhteenveto",
    "👥 Tekijälista",
])

# ══════════════════════════════════════════════════════════════════════════════
# PIKASYÖTTÖ — kaikki tekijät kerralla taulukossa
# ══════════════════════════════════════════════════════════════════════════════
with tab_pikasyotto:
    st.subheader(f"Viikko {viikko} / {vuosi} — pikasyöttö")
    st.caption("Täytä taulukko ja paina Tallenna. Tyhjät = 0 h.")

    if not tyontekijat_lista:
        st.info("Lisää ensin aliurakoitsijat **Tekijälista**-välilehdeltä.")
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
            "Nimi":     st.column_config.TextColumn("Nimi", disabled=True, width="medium"),
            "Yritys":   st.column_config.TextColumn("Yritys", disabled=True, width="medium"),
            "Kategoria": st.column_config.SelectboxColumn(
                "Kategoria", options=KATEGORIAT, width="small"),
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

        if st.button("💾 Tallenna kaikki", type="primary", use_container_width=True):
            tallennettu = 0
            for _, row in df_muokattu.iterrows():
                nimi = row["Nimi"]
                tunnit = {pk: float(row[po]) for pk, po in zip(PAIVA_AVAIN, paiva_otsikot)}
                yht_h  = sum(tunnit.values())

                # Hae laskutustiedot tekijälistalta
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
                }
                ali_rivit = [r for r in ali_rivit
                             if not (r.get("viikko") == int(viikko)
                                     and r.get("vuosi", int(vuosi)) == int(vuosi)
                                     and r.get("nimi") == nimi)]
                ali_rivit.append(uusi)
                tallennettu += 1

            tallenna_ali_tunnit(projekti, ali_rivit)
            st.success(f"✅ Tallennettu {tallennettu} tekijää — viikko {viikko}/{vuosi}")
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# YKSITTÄINEN SYÖTTÖ — yksi tekijä kerrallaan, isot napit
# ══════════════════════════════════════════════════════════════════════════════
with tab_yksittainen:
    st.subheader("Yksittäinen kirjaus")

    nimet = [t["nimi"] for t in tyontekijat_lista]
    if not nimet:
        st.info("Lisää aliurakoitsijat **Tekijälista**-välilehdeltä.")
    else:
        col_vas, col_oik = st.columns([1, 2])
        with col_vas:
            valittu_nimi = st.selectbox("Tekijä", nimet)
            t_info = next((t for t in tyontekijat_lista if t["nimi"] == valittu_nimi), {})
            st.caption(f"Yritys: {t_info.get('yritys','–')}")

            yk_kat = st.selectbox("Kategoria", KATEGORIAT,
                                  index=KATEGORIAT.index(oletus_kat), key="yk_kat")

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
            st.markdown("**Tunnit päivittäin**")
            # Hae esitäyttö
            nyky = next((r for r in ali_rivit
                         if r.get("viikko") == int(viikko)
                         and r.get("vuosi", int(vuosi)) == int(vuosi)
                         and r.get("nimi") == valittu_nimi), {})

            cols_h = st.columns(7)
            h_arvot = {}
            for i, (P, pk, p) in enumerate(zip(PAIVAT, PAIVA_AVAIN, paivat)):
                oletus_h = float(nyky.get(pk, 0) or 0)
                h_arvot[pk] = cols_h[i].number_input(
                    f"{P}\n{p.strftime('%-d.%-m.')}",
                    min_value=0.0, max_value=24.0,
                    value=oletus_h, step=0.5,
                    key=f"yk_{pk}",
                )

            yht_h = sum(h_arvot.values())

            # Pikasyöttönapit
            st.markdown("**Lisää tunnit kerralla:**")
            btn_cols = st.columns(5)
            for lisays in [6, 7, 8, 9, 10]:
                if btn_cols[lisays-6].button(f"+{lisays}h ark", key=f"btn_{lisays}"):
                    for pk in ["ma","ti","ke","to","pe"]:
                        h_arvot[pk] = float(lisays)
                    yht_h = sum(h_arvot.values())

        huomio = st.text_input("Huomio (vapaaehtoinen)", key="yk_huomio")

        c1, c2 = st.columns(2)
        c1.metric("Tunnit yhteensä", f"{yht_h:.1f} h")
        if lp == "tuntihinta" and t_info.get("tuntihinta"):
            c2.metric("Summa", f"{yht_h * t_info['tuntihinta']:,.0f} €")

        if st.button("💾 Tallenna", type="primary", use_container_width=True, key="yk_tall"):
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
            }
            ali_rivit = [r for r in ali_rivit
                         if not (r.get("viikko") == int(viikko)
                                 and r.get("vuosi", int(vuosi)) == int(vuosi)
                                 and r.get("nimi") == valittu_nimi)]
            ali_rivit.append(uusi)
            tallenna_ali_tunnit(projekti, ali_rivit)
            st.success(f"✅ {valittu_nimi} — {yht_h:.1f} h tallennettu!")
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
        st.info("Ei kirjauksia tälle viikolle.")
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
            rivi["Yht (h)"]   = yht
            rivi["Summa (€)"] = f"{summa:,.0f}" if summa else "–"
            tbl.append(rivi)

        df_yht = pd.DataFrame(tbl)
        st.dataframe(df_yht, use_container_width=True, hide_index=True)

        # Metriikat
        tot_h   = sum(r.get("yht_h",0) for r in vko_rivit)
        tot_eur = sum(
            (r.get("yht_h",0)*(r.get("tuntihinta") or 0) if r.get("laskutustapa")=="tuntihinta"
             else (r.get("kiintea_hinta") or 0) if r.get("laskutustapa")=="kiintea"
             else 0) for r in vko_rivit)
        c1,c2,c3 = st.columns(3)
        c1.metric("Tekijöitä", len(vko_rivit))
        c2.metric("Tunteja yht.", f"{tot_h:.1f} h")
        c3.metric("Summa yht.", f"{tot_eur:,.0f} €" if tot_eur else "–")

        # Raportti
        st.divider()
        c1, c2 = st.columns([3,1])
        c1.markdown("**📄 Lataa viikkoraportti** — tulosta PDF:nä selaimessa")
        if c2.button("Luo raportti", type="primary"):
            xlsx = luo_viikkoraportti(
                rivit=ali_rivit, viikko=int(viikko), vuosi=int(vuosi),
                projekti=projekti, yritys="Uudenmaan Asbestipurku Oy")
            nm = f"Ali-tuntikirja_vko{viikko}_{_projekti_slug(projekti)}.xlsx"
            st.download_button("⬇️ Lataa Excel", data=xlsx, file_name=nm,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Poisto
        with st.expander("🗑️ Poista kirjaus"):
            va = {f"{r['nimi']} – {r.get('yht_h',0):.1f}h": r["id"] for r in vko_rivit}
            pl = st.selectbox("Kirjaus", list(va.keys()))
            if st.button("Poista", type="secondary"):
                ali_rivit = [r for r in ali_rivit if r["id"] != va[pl]]
                tallenna_ali_tunnit(projekti, ali_rivit)
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TEKIJÄLISTA — aliurakoitsijoiden hallinta
# ══════════════════════════════════════════════════════════════════════════════
with tab_tekijat:
    st.subheader("Aliurakoitsijoiden hallinta")
    st.caption("Lisää tekijät kerran — sen jälkeen ne näkyvät pikasyötössä automaattisesti.")

    # Näytä nykyinen lista
    if tyontekijat_lista:
        df_tek = pd.DataFrame(tyontekijat_lista)
        # Näytä siisti versio
        naytto_cols = ["nimi","yritys","laskutustapa","tuntihinta","kiintea_hinta"]
        naytto_cols = [c for c in naytto_cols if c in df_tek.columns]
        naytto = df_tek[naytto_cols].copy()
        naytto.columns = [c.replace("_"," ").title() for c in naytto_cols]
        st.dataframe(naytto, use_container_width=True, hide_index=True)
        st.divider()

    # Lisää uusi
    with st.expander("➕ Lisää aliurakoitsija", expanded=len(tyontekijat_lista)==0):
        t1, t2 = st.columns(2)
        t_nimi  = t1.text_input("Nimi", key="t_nimi")
        t_yrit  = t1.text_input("Yritys", key="t_yrit")
        t_lp    = t2.selectbox("Laskutustapa",
                               ["Vain tunnit","Tuntihinta (€/h)","Kiinteä hinta (€)"],
                               key="t_lp")
        t_th, t_kh = None, None
        if t_lp == "Tuntihinta (€/h)":
            t_th = t2.number_input("€/h", 0.0, step=1.0, value=38.0, key="t_th")
        elif t_lp == "Kiinteä hinta (€)":
            t_kh = t2.number_input("Kiinteä hinta (€)", 0.0, step=10.0, key="t_kh")

        if st.button("Lisää listalle", type="primary", key="t_lisaa"):
            if not t_nimi:
                st.error("Syötä nimi.")
            elif any(t["nimi"] == t_nimi for t in tyontekijat_lista):
                st.warning(f"{t_nimi} on jo listalla.")
            else:
                lm = {"Vain tunnit":"tunnit","Tuntihinta (€/h)":"tuntihinta","Kiinteä hinta (€)":"kiintea"}
                tyontekijat_lista.append({
                    "nimi": t_nimi, "yritys": t_yrit,
                    "laskutustapa": lm[t_lp],
                    "tuntihinta": t_th, "kiintea_hinta": t_kh,
                })
                _tallenna_tyontekijat(tyontekijat_lista)
                st.success(f"✅ {t_nimi} lisätty!")
                st.rerun()

    # Poista listalta
    if tyontekijat_lista:
        with st.expander("🗑️ Poista listalta"):
            nimet_p = [t["nimi"] for t in tyontekijat_lista]
            poistettava = st.selectbox("Tekijä", nimet_p, key="t_poisto")
            if st.button("Poista listalta", type="secondary", key="t_poista"):
                tyontekijat_lista = [t for t in tyontekijat_lista if t["nimi"] != poistettava]
                _tallenna_tyontekijat(tyontekijat_lista)
                st.rerun()
