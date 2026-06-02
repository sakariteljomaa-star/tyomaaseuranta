"""
Työmaaseuranta – Kustannusseurantasovellus
Uudenmaan Asbestipurku Oy
"""

import streamlit as st
import pandas as pd
from datetime import date
from parser import yhdista_tiedostot
from parser_myynti import lue_myyntireskontra
from parser_tunnit import lue_tuntikirjanpito
from excel_export import luo_excel
from raportti_ali import luo_viikkoraportti
from storage import (
    lataa_tuntiseuranta, tallenna_tuntiseuranta,
    lataa_ali_tunnit,    tallenna_ali_tunnit,
    lataa_palkat,        tallenna_palkat,
)
from kansiotuonti import lue_kansio, oletus_kansio

st.set_page_config(page_title="Työmaaseuranta", page_icon="🏗️", layout="wide")

# ── Käyttäjähallinta ja roolitukset ────────────────────────────────────────────
import auth as A

kayttaja = A.kirjaudu_gate("Työmaaseuranta — Kustannusseuranta")
rooli    = kayttaja["rooli"]
on_admin = A.voi_hallita_kayttajia(rooli)

# Kustannusseuranta on arkaluonteinen — työntekijä-rooli ei pääse
if rooli == "tyontekija":
    st.title("🔒 Ei käyttöoikeutta")
    st.warning("Kustannusseuranta on tarkoitettu vain työnjohdolle ja kirjanpidolle. "
               "Käytä tuntikirja-sovellusta.")
    if st.button("🔓 Kirjaudu ulos"):
        A.kirjaudu_ulos()
        st.rerun()
    st.stop()

with st.sidebar:
    st.caption(f"👤 {kayttaja.get('nimi', kayttaja['tunnus'])}  ·  {A.ROOLIT[rooli]['nimi']}")
    if st.button("🔓 Kirjaudu ulos", use_container_width=True, key="logout_btn"):
        A.kirjaudu_ulos()
        st.rerun()

st.title("🏗️ Työmaaseuranta – Kustannusseuranta")
st.caption("Uudenmaan Asbestipurku Oy")

EURO   = lambda x: f"{x:,.2f} €".replace(",", " ").replace(".", ",")
PAIVAT = ["ma","ti","ke","to","pe","la","su"]

# ── SIVUPALKKI: vain asetukset ─────────────────────────────────────────────────
with st.sidebar:
    st.header("Projekti")
    projekti = st.text_input("Projektin nimi", placeholder="esim. Valteri-koulu, Tenholantie 15")
    yritys   = st.text_input("Yritys", value="Uudenmaan Asbestipurku Oy")
    st.divider()
    st.header("Asetukset")
    tuntihinta      = st.number_input("Tuntiveloitus (€/h)",   value=38,  step=1)
    sivukulukerroin = st.number_input("Sivukulukerroin (palkat)", value=1.5, step=0.05)
    st.divider()

    # ── Kansiotuonti ────────────────────────────────────────────────────────
    st.header("📂 Kansiotuonti")
    st.caption("Tallenna Netvisor-viennit tähän kansioon — sovellus lukee ne automaattisesti.")

    tuontikansio = st.text_input(
        "Tuontikansio",
        value=st.session_state.get("tuontikansio", oletus_kansio()),
        placeholder="/Users/sakari/Downloads",
        key="_tuontikansio_input",
    )
    st.session_state["tuontikansio"] = tuontikansio

    if st.button("🔄 Lue kansio", use_container_width=True):
        with st.spinner("Luetaan kansiota..."):
            kansiotieto = lue_kansio(tuontikansio)

        # Ostolaskut → df_ostot (kaikki ostot yhdistettynä)
        if kansiotieto["ostot"]:
            from parser import yhdista_tiedostot as _yh
            df_o = _yh([p for p, _, _ in kansiotieto["ostot"]])
            st.session_state["df_kaikki"] = df_o

        # Myyntireskontra → df_myynti (viimeisin tiedosto)
        if kansiotieto["myynti"]:
            from parser_myynti import lue_myyntireskontra as _lm
            haku = projekti.split(",")[0].strip() if projekti else ""
            df_m = _lm(kansiotieto["myynti"][0][0], projekti_hakusana=haku)
            st.session_state["df_myynti"] = df_m

        # Tuntikirjanpito → df_tuntikirjanpito (viimeisin tiedosto)
        if kansiotieto["tunnit"]:
            from parser_tunnit import lue_tuntikirjanpito as _lt
            tulos = _lt(kansiotieto["tunnit"][0][0])
            st.session_state["df_tuntikirjanpito"] = tulos["df"]
            st.session_state["_tk_meta"] = tulos

        # Näytä yhteenveto
        ok_osat = []
        if kansiotieto["ostot"]:
            ok_osat.append(f"Ostolaskut: {len(kansiotieto['ostot'])} tiedostoa")
        if kansiotieto["myynti"]:
            ok_osat.append(f"Myynti: {len(kansiotieto['myynti'])} tiedostoa")
        if kansiotieto["tunnit"]:
            ok_osat.append(f"Tunnit: {len(kansiotieto['tunnit'])} tiedostoa")
        if kansiotieto["tuntematon"]:
            ok_osat.append(f"⚠️ Tunnistamaton: {len(kansiotieto['tuntematon'])} kpl")
        if ok_osat:
            st.success("\n".join(ok_osat))
        else:
            st.warning("Kansiosta ei löydetty Netvisor-tiedostoja.")

        if kansiotieto["virheet"]:
            for nm, err in kansiotieto["virheet"]:
                st.error(f"{nm}: {err}")

        st.rerun()

    # Näytä mitä kansiossa on
    if tuontikansio:
        from pathlib import Path as _P
        xlsx_lkm = len(list(_P(tuontikansio).glob("*.xlsx"))) if _P(tuontikansio).exists() else 0
        st.caption(f"Kansiossa: {xlsx_lkm} .xlsx-tiedostoa")

# ── APUFUNKTIOT ────────────────────────────────────────────────────────────────

def _hae(avain: str) -> pd.DataFrame:
    return st.session_state.get(avain, pd.DataFrame())

def _import_ostot(state_avain: str, widget_avain: str, ohje: str = ""):
    """Yhteinen Netvisor laskentakohderaportti -tuontiwidget."""
    df_nyky = _hae(state_avain)
    label   = "📥 Tuo Netvisorista" + (f"  ✅ {len(df_nyky)} riviä" if not df_nyky.empty else "")
    with st.expander(label, expanded=df_nyky.empty):
        st.caption(ohje or "Netvisor → Raportit → Laskentakohderaportti → vie Exceliin")
        f = st.file_uploader("Laskentakohderaportti .xlsx (voit valita useita)",
                             type=["xlsx"], accept_multiple_files=True, key=widget_avain)
        if f:
            with st.spinner("Luetaan..."):
                df = yhdista_tiedostot(f)
            st.session_state[state_avain] = df
            st.success(f"Ladattu {len(df)} riviä.")
            st.rerun()

def _nayta_kululaji(df_kaikki, kululaji, sarakkeet):
    osa = df_kaikki[df_kaikki["kululaji"] == kululaji].copy()
    if osa.empty:
        st.info(f"Ei {kululaji}-rivejä ladatussa aineistossa.")
        return
    c1, c2 = st.columns(2)
    c1.metric("Urakka",  EURO(osa[osa["kategoria"] == "Urakka"]["summa"].sum()))
    c2.metric("Lisätyö", EURO(osa[osa["kategoria"] == "Lisätyö"]["summa"].sum()))
    for kat in ["Lisätyö", "Urakka"]:
        sub = osa[osa["kategoria"] == kat]
        if sub.empty:
            continue
        st.markdown(f"**── {kat.upper()} ──**")
        naytto = sub[sarakkeet].copy()
        if "pvm" in naytto.columns:
            naytto["pvm"] = naytto["pvm"].dt.strftime("%d.%m.%Y")
        st.dataframe(naytto, use_container_width=True, hide_index=True)
    st.markdown(f"**Yhteensä: {EURO(osa['summa'].sum())}**")

# ── VÄLILEHDET ──────────────────────────────────────────────────────────────────
_tab_nimet = [
    "📊 Yhteenveto",
    "💰 Myynti",
    "⏱️ Tuntiseuranta",
    "📋 Ali-tuntikirja",
    "💼 Palkkakustannukset",
    "🛒 Ostot",
    "🗑️ Jätemaksut",
    "👷 Aliurakoitsijat",
    "🔧 Kalusto",
    "📋 Kaikki rivit",
]
if on_admin:
    _tab_nimet.append("👤 Käyttäjät")

_tabs = st.tabs(_tab_nimet)
(tab_yht, tab_myynti, tab_tunnit, tab_ali_tunnit,
 tab_palkat, tab_ostot_v, tab_jate, tab_ali,
 tab_kalusto, tab_kaikki) = _tabs[:10]
tab_kayttajat = _tabs[10] if on_admin else None

# ══════════════════════════════════════════════════════════════════════════════
# MYYNTI
# ══════════════════════════════════════════════════════════════════════════════
with tab_myynti:
    st.subheader(f"Myyntilaskut – {projekti or '(projekti ei asetettu)'}")

    df_myynti = _hae("df_myynti")
    label = "📥 Tuo Netvisorista" + (f"  ✅ {len(df_myynti)} laskua" if not df_myynti.empty else "")
    with st.expander(label, expanded=df_myynti.empty):
        st.caption("Netvisor → Myynti → Myyntireskontra → vie Exceliin")
        myynti_f = st.file_uploader("Myyntireskontra .xlsx", type=["xlsx"], key="myynti_up")
        if myynti_f:
            haku = projekti.split(",")[0].strip() if projekti else ""
            with st.spinner("Luetaan..."):
                df_m = lue_myyntireskontra(myynti_f, projekti_hakusana=haku)
            st.session_state["df_myynti"] = df_m
            st.success(f"Ladattu {len(df_m)} laskua.")
            st.rerun()

    df_myynti = _hae("df_myynti")
    if df_myynti.empty:
        st.info("Lataa myyntireskontra yllä.")
    else:
        df_pos = df_myynti[df_myynti["summa"] > 0].copy()
        c1, c2, c3 = st.columns(3)
        laskutettu = df_pos["summa"].sum()
        avoimena   = df_pos["avoimena"].sum()
        c1.metric("Laskutettu (alv 0%)", EURO(laskutettu))
        c2.metric("Maksettu",            EURO(laskutettu - avoimena))
        c3.metric("Avoimena",            EURO(avoimena),
                  delta="⚠️ erääntyneitä" if any("Erääntynyt" in str(t) for t in df_pos["tila"]) else None,
                  delta_color="inverse")
        st.divider()
        for kat in ["Lisätyö","Urakka","Muu"]:
            osa = df_pos[df_pos["kategoria"] == kat]
            if osa.empty:
                continue
            st.markdown(f"**── {kat.upper()} ──**")
            n = osa[["lasku_nro","lasku_pvm","sisalto","summa","avoimena","erapaiva","tila"]].copy()
            n["lasku_pvm"] = n["lasku_pvm"].dt.strftime("%d.%m.%Y")
            n["erapaiva"]  = n["erapaiva"].dt.strftime("%d.%m.%Y")
            n.columns = ["Lasku nro","Laskupvm","Sisältö","Summa (alv 0%)","Avoimena","Eräpäivä","Tila"]
            st.dataframe(n, use_container_width=True, hide_index=True)
            st.caption(f"Yhteensä: {EURO(osa['summa'].sum())} | Avoimena: {EURO(osa['avoimena'].sum())}")

# ══════════════════════════════════════════════════════════════════════════════
# TUNTISEURANTA (omat)
# ══════════════════════════════════════════════════════════════════════════════
with tab_tunnit:
    st.subheader(f"Tuntiseuranta (omat) – {projekti or '(projekti ei asetettu)'}")
    if not projekti:
        st.warning("Aseta projektin nimi sivupalkissa.")
        st.stop()

    if "tuntiseuranta" not in st.session_state or st.session_state.get("_projekti") != projekti:
        st.session_state["tuntiseuranta"] = lataa_tuntiseuranta(projekti)
        st.session_state["_projekti"] = projekti
    viikot: list = st.session_state["tuntiseuranta"]

    # Netvisor-tuonti
    df_tk_nyky = _hae("df_tuntikirjanpito")
    tk_label = "📥 Tuo Netvisor tuntikirjanpidosta" + (f"  ✅ {df_tk_nyky['Työtunnit'].sum():.0f} h" if not df_tk_nyky.empty else "")
    with st.expander(tk_label, expanded=False):
        st.caption("Netvisor → Palkka → Tuntikirjanpito → suodata laskentakohde → vie Exceliin")
        tunti_f = st.file_uploader("Tuntikirjanpito .xlsx", type=["xlsx"], key="tuntikirjanpito")
        if tunti_f:
            tulos = lue_tuntikirjanpito(tunti_f)
            st.session_state["df_tuntikirjanpito"] = tulos["df"]
            st.session_state["_tk_meta"] = tulos
            st.rerun()

    df_tk = _hae("df_tuntikirjanpito")
    if not df_tk.empty:
        meta  = st.session_state.get("_tk_meta", {})
        df_nn = df_tk[df_tk["Työtunnit"] > 0]
        st.caption(f"Projekti: **{meta.get('projekti','')}** | Jakso: {meta.get('jakso','')} | Tunnit: **{meta.get('yht_tunnit',0):.1f} h**")
        st.dataframe(df_nn, use_container_width=True, hide_index=True)
        st.markdown("**Lisää viikkona:**")
        ti1, ti2, ti3 = st.columns(3)
        ti_vko  = ti1.number_input("Viikko",1,53,int(date.today().strftime("%V")),key="ti_vko")
        ti_kuv  = ti1.text_input("Kuvaus", key="ti_kuv",
                    value=f"{meta.get('projekti','')} – vko {int(date.today().strftime('%V'))} | {len(df_nn)} tekijää")
        yht_h   = float(meta.get("yht_tunnit", 0))
        ti_ur   = ti2.number_input("Urakka (h)",     0.0, step=0.5, value=yht_h, key="ti_ur")
        ti_lt   = ti2.number_input("Lisätyö (h)",    0.0, step=0.5, key="ti_lt")
        ti_vv   = ti2.number_input("Vesivahinko (h)",0.0, step=0.5, key="ti_vv")
        ti_jt   = ti3.number_input("Jäte (€)",       0.0, step=1.0, key="ti_jt")
        ti_kl   = ti3.number_input("Kalusto (€)",    0.0, step=1.0, key="ti_kl")
        ti3.caption("ℹ️ Jaa Urakka/Lisätyö itse.")
        if st.button("Tuo viikkona", type="primary", key="tuo_vko"):
            yht = ti_ur + ti_lt + ti_vv
            u   = {"viikko":int(ti_vko),"kuvaus":ti_kuv,
                   "urakka_h":ti_ur,"lisatyo_h":ti_lt,"vesivahinko_h":ti_vv,
                   "yht_h":yht,"tuntikust_eur":yht*tuntihinta,
                   "jate_eur":ti_jt,"kalusto_eur":ti_kl,
                   "kaikki_yht_eur":yht*tuntihinta+ti_jt+ti_kl,"tuntihinta":tuntihinta,
                   "tyontekijat":df_nn[["Työntekijä","Työtunnit"]].to_dict("records")}
            viikot = sorted([v for v in viikot if v["viikko"]!=int(ti_vko)]+[u], key=lambda v:v["viikko"])
            st.session_state["tuntiseuranta"] = viikot
            tallenna_tuntiseuranta(projekti, viikot)
            st.success(f"Viikko {ti_vko} tuotu ({yht:.1f} h)!")
            st.rerun()
        st.divider()

    # Käsin lisäys
    with st.expander("➕ Lisää viikko käsin", expanded=len(viikot)==0):
        k1,k2 = st.columns(2)
        uv = k1.number_input("Viikko",1,53,int(date.today().strftime("%V")),key="kv")
        uk = k1.text_input("Kuvaus",placeholder="esim. Tenholantie 15 – vko 21",key="kk")
        ur = k2.number_input("Urakka (h)",    0.0,step=0.5,key="ku")
        lt = k2.number_input("Lisätyö (h)",   0.0,step=0.5,key="kl")
        vv = k2.number_input("Vesivahinko (h)",0.0,step=0.5,key="kvv")
        k3,k4 = st.columns(2)
        jt = k3.number_input("Jäte (€)",   0.0,step=1.0,key="kjt")
        kl = k4.number_input("Kalusto (€)",0.0,step=1.0,key="kkl")
        if st.button("Tallenna viikko", type="primary",key="ktall"):
            yh = ur+lt+vv
            u  = {"viikko":int(uv),"kuvaus":uk,"urakka_h":ur,"lisatyo_h":lt,"vesivahinko_h":vv,
                  "yht_h":yh,"tuntikust_eur":yh*tuntihinta,"jate_eur":jt,"kalusto_eur":kl,
                  "kaikki_yht_eur":yh*tuntihinta+jt+kl,"tuntihinta":tuntihinta}
            viikot = sorted([v for v in viikot if v["viikko"]!=int(uv)]+[u], key=lambda v:v["viikko"])
            st.session_state["tuntiseuranta"] = viikot
            tallenna_tuntiseuranta(projekti, viikot)
            st.success(f"Viikko {uv} tallennettu!")
            st.rerun()

    if viikot:
        df_t = pd.DataFrame(viikot)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Tunnit yht.",  f"{df_t['yht_h'].sum():.1f} h")
        c2.metric("Urakka",       f"{df_t['urakka_h'].sum():.1f} h")
        c3.metric("Lisätyö",      f"{df_t['lisatyo_h'].sum():.1f} h")
        c4.metric("Tuntikust.",   EURO(df_t["tuntikust_eur"].sum()))
        st.divider()
        n = df_t[["viikko","kuvaus","urakka_h","lisatyo_h","vesivahinko_h",
                  "yht_h","tuntikust_eur","jate_eur","kalusto_eur","kaikki_yht_eur"]].copy()
        n.columns = ["Viikko","Kuvaus","Urakka(h)","Lisätyö(h)","Vesivahinko(h)",
                     "Yht.(h)","Tuntikust.(€)","Jäte(€)","Kalusto(€)","KAIKKI YHT.(€)"]
        yr = pd.DataFrame([{"Viikko":"YHTEENSÄ","Kuvaus":"",
            "Urakka(h)":df_t["urakka_h"].sum(),"Lisätyö(h)":df_t["lisatyo_h"].sum(),
            "Vesivahinko(h)":df_t["vesivahinko_h"].sum(),"Yht.(h)":df_t["yht_h"].sum(),
            "Tuntikust.(€)":df_t["tuntikust_eur"].sum(),"Jäte(€)":df_t["jate_eur"].sum(),
            "Kalusto(€)":df_t["kalusto_eur"].sum(),"KAIKKI YHT.(€)":df_t["kaikki_yht_eur"].sum()}])
        st.dataframe(pd.concat([n,yr],ignore_index=True), use_container_width=True, hide_index=True)
        st.caption(f"Tuntiveloitus: {tuntihinta} €/h")
        with st.expander("🗑️ Poista viikko"):
            pv = st.selectbox("Viikko",[v["viikko"] for v in viikot],key="pvk")
            if st.button("Poista",type="secondary",key="pvkb"):
                viikot=[v for v in viikot if v["viikko"]!=pv]
                st.session_state["tuntiseuranta"]=viikot
                tallenna_tuntiseuranta(projekti,viikot)
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ALI-TUNTIKIRJA
# ══════════════════════════════════════════════════════════════════════════════
with tab_ali_tunnit:
    st.subheader(f"Aliurakoitsijoiden tuntikirja – {projekti or '(projekti ei asetettu)'}")
    if not projekti:
        st.warning("Aseta projektin nimi sivupalkissa.")
        st.stop()

    if "ali_tunnit" not in st.session_state or st.session_state.get("_projekti") != projekti:
        st.session_state["ali_tunnit"] = lataa_ali_tunnit(projekti)
    ali_rivit: list = st.session_state["ali_tunnit"]

    st.info("ℹ️ Netvisor ei tue aliurakoitsijoiden tuntikirjanpitoa — tunnit syötetään käsin.")

    with st.expander("➕ Lisää tuntikirjaus", expanded=len(ali_rivit)==0):
        a1,a2 = st.columns(2)
        av  = a1.number_input("Viikko",1,53,int(date.today().strftime("%V")),key="av")
        an  = a1.text_input("Työntekijän nimi",key="an")
        ay  = a1.text_input("Yritys",key="ay")
        akat= a1.selectbox("Kategoria",["Urakka","Lisätyö","Vesivahinko"],key="akat")
        a2.markdown("**Tunnit (h) päivittäin**")
        d1,d2,d3,d4 = a2.columns(4)
        ama=d1.number_input("Ma",0.0,24.0,0.0,0.5,key="ama")
        ati=d2.number_input("Ti",0.0,24.0,0.0,0.5,key="ati")
        ake=d3.number_input("Ke",0.0,24.0,0.0,0.5,key="ake")
        ato=d4.number_input("To",0.0,24.0,0.0,0.5,key="ato")
        d5,d6,d7,_ = a2.columns(4)
        ape=d5.number_input("Pe",0.0,24.0,0.0,0.5,key="ape")
        ala=d6.number_input("La",0.0,24.0,0.0,0.5,key="ala")
        asu=d7.number_input("Su",0.0,24.0,0.0,0.5,key="asu")
        ayht = ama+ati+ake+ato+ape+ala+asu
        a2.metric("Yhteensä",f"{ayht:.1f} h")
        b1,b2,b3 = st.columns(3)
        alk = b1.selectbox("Laskutustapa",["Vain tunnit","Tuntihinta (€/h)","Kiinteä hinta (€)"],key="alk")
        ath,akh = None,None
        if alk=="Tuntihinta (€/h)":
            ath = b2.number_input("€/h",0.0,step=1.0,value=38.0,key="ath")
            b2.caption(f"Summa: {ayht*ath:,.2f} €")
        elif alk=="Kiinteä hinta (€)":
            akh = b2.number_input("Kiinteä hinta (€)",0.0,step=10.0,key="akh")
        ahu = b3.text_input("Huomio",key="ahu")
        if st.button("Tallenna kirjaus",type="primary",key="atall"):
            if not an:
                st.error("Syötä nimi.")
            else:
                lm={"Vain tunnit":"tunnit","Tuntihinta (€/h)":"tuntihinta","Kiinteä hinta (€)":"kiintea"}
                u={"id":f"{av}_{an}_{ay}".replace(" ","_"),"viikko":int(av),"nimi":an,"yritys":ay,
                   "ma":ama,"ti":ati,"ke":ake,"to":ato,"pe":ape,"la":ala,"su":asu,"yht_h":ayht,
                   "kategoria":akat,"laskutustapa":lm[alk],"tuntihinta":ath,"kiintea_hinta":akh,"huomio":ahu}
                ali_rivit.append(u)
                st.session_state["ali_tunnit"]=ali_rivit
                tallenna_ali_tunnit(projekti,ali_rivit)
                st.success(f"Tallennettu: {an} vko {av} – {ayht:.1f} h")
                st.rerun()

    if ali_rivit:
        vl = sorted(set(r["viikko"] for r in ali_rivit),reverse=True)
        vv = st.selectbox("Näytä viikko",vl,key="avv")
        vkr = [r for r in ali_rivit if r["viikko"]==vv]
        tbl=[]
        for rv in vkr:
            h=rv.get("yht_h",0); lp=rv.get("laskutustapa","tunnit")
            if lp=="tuntihinta":   sm,hs=h*(rv.get("tuntihinta") or 0),f"{rv.get('tuntihinta',0):.0f} €/h"
            elif lp=="kiintea":    sm,hs=rv.get("kiintea_hinta") or 0,f"Kiinteä {rv.get('kiintea_hinta',0):.0f} €"
            else:                  sm,hs=None,"–"
            tbl.append({"Nimi":rv["nimi"],"Yritys":rv.get("yritys",""),
                "Ma":rv.get("ma") or "","Ti":rv.get("ti") or "","Ke":rv.get("ke") or "",
                "To":rv.get("to") or "","Pe":rv.get("pe") or "","La":rv.get("la") or "","Su":rv.get("su") or "",
                "Yht(h)":h,"Kategoria":rv.get("kategoria",""),"Hinta":hs,
                "Summa(€)":f"{sm:,.2f}" if sm else "–","Huomio":rv.get("huomio","")})
        st.dataframe(pd.DataFrame(tbl),use_container_width=True,hide_index=True)
        yhk=sum(r.get("yht_h",0) for r in vkr)
        yhe=sum((r.get("yht_h",0)*(r.get("tuntihinta") or 0) if r.get("laskutustapa")=="tuntihinta"
                 else (r.get("kiintea_hinta") or 0) if r.get("laskutustapa")=="kiintea" else 0) for r in vkr)
        c1,c2,c3=st.columns(3)
        c1.metric("Tekijöitä",len(vkr)); c2.metric("Tunteja",f"{yhk:.1f} h"); c3.metric("Summa",EURO(yhe) if yhe else "–")
        st.divider()
        rc1,rc2=st.columns([3,1])
        rc1.markdown("**📄 Viikkoraportti** — tulosta PDF:nä (Tiedosto → Tulosta → Tallenna PDF:nä)")
        vuv=rc2.number_input("Vuosi",value=date.today().year,step=1,key="avuosi")
        if st.button("Luo viikkoraportti",type="primary",key="arap"):
            x=luo_viikkoraportti(ali_rivit,viikko=vv,vuosi=int(vuv),projekti=projekti,yritys=yritys)
            nm=f"Ali-tuntikirja_vko{vv}_{(projekti or 'P').replace(' ','_').replace(',','')}.xlsx"
            st.download_button("⬇️ Lataa Excel-raportti",data=x,file_name=nm,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with st.expander("🗑️ Poista kirjaus"):
            va={f"vko{r['viikko']} – {r['nimi']} ({r.get('yritys','')}) – {r.get('yht_h',0):.1f}h":r["id"] for r in ali_rivit}
            pl=st.selectbox("Kirjaus",list(va.keys()),key="apl")
            if st.button("Poista",type="secondary",key="apb"):
                ali_rivit=[r for r in ali_rivit if r["id"]!=va[pl]]
                st.session_state["ali_tunnit"]=ali_rivit
                tallenna_ali_tunnit(projekti,ali_rivit)
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PALKKAKUSTANNUKSET
# ══════════════════════════════════════════════════════════════════════════════
with tab_palkat:
    st.subheader(f"Palkkakustannukset – {projekti or '(projekti ei asetettu)'}")
    if not projekti:
        st.warning("Aseta projektin nimi sivupalkissa.")
        st.stop()

    if "palkat" not in st.session_state or st.session_state.get("_projekti") != projekti:
        st.session_state["palkat"] = lataa_palkat(projekti)
    palkat: list = st.session_state["palkat"]

    st.info(f"Sivukulukerroin: **{sivukulukerroin}** (TyEL, sotu, tapaturmavakuutus) — muuta sivupalkissa.")

    with st.expander("📥 Tuo Netvisor palkkakirjanpidosta (tulossa)", expanded=False):
        st.info("Lähetä esimerkkitiedosto → rakennetaan automaattituonti.\n"
                "Netvisor → Palkka → Palkkakirjanpito → vie Exceliin")

    with st.expander("➕ Lisää palkkajakso", expanded=len(palkat)==0):
        p1,p2=st.columns(2)
        ppv = p1.date_input("Palkanmaksupäivä",value=date.today(),key="ppv")
        pts = p1.number_input("Tosite nro",min_value=1,step=1,key="pts")
        psl = p1.text_input("Selite",placeholder="esim. Palkkayhteenveto 11.5.–24.5.2026",key="psl")
        pkt = p1.selectbox("Kategoria",["Urakka","Lisätyö","Vesivahinko"],key="pkt")
        pbr = p2.number_input("Bruttopalkka (€)",0.0,step=0.01,key="pbr")
        pke = p2.number_input("Sivukulukerroin",value=float(sivukulukerroin),step=0.05,key="pke")
        p2.metric("Kokonaiskustannus",f"{pbr*pke:,.2f} €")
        p2.caption("= bruttopalkka × sivukulukerroin")
        if st.button("Tallenna palkkajakso",type="primary",key="ptall"):
            u={"id":f"{ppv}_{pts}","pvm":str(ppv),"tosite":int(pts),"selite":psl,
               "kategoria":pkt,"brutto":pbr,"kerroin":pke,"kokonaiskust":pbr*pke}
            palkat.append(u)
            st.session_state["palkat"]=palkat
            tallenna_palkat(projekti,palkat)
            st.success("Palkkajakso tallennettu!")
            st.rerun()

    if not palkat:
        st.info("Ei palkkajaksoja. Lisää yllä.")
    else:
        df_p=pd.DataFrame(palkat)
        c1,c2,c3=st.columns(3)
        c1.metric("Bruttopalkka yht.",  EURO(df_p["brutto"].sum()))
        c2.metric("Kokonaiskust. yht.", EURO(df_p["kokonaiskust"].sum()))
        c3.metric("Kerroin",            f"×{sivukulukerroin}")
        st.divider()
        for kat in ["Lisätyö","Urakka","Vesivahinko"]:
            osa=df_p[df_p["kategoria"]==kat]
            if osa.empty: continue
            st.markdown(f"**── {kat.upper()} ──**")
            n=osa[["pvm","tosite","selite","brutto","kerroin","kokonaiskust","kategoria"]].copy()
            n.columns=["Pvm","Tosite","Selite","Brutto (€)","Kerroin","Kokonaiskust. (€)","Kategoria"]
            st.dataframe(n,use_container_width=True,hide_index=True)
        st.markdown(f"**YHTEENSÄ — Brutto: {EURO(df_p['brutto'].sum())} | Kokonaiskust.: {EURO(df_p['kokonaiskust'].sum())}**")
        with st.expander("🗑️ Poista palkkajakso"):
            va={f"{r['pvm']} – {r['selite']} – {r['brutto']:.2f}€":r["id"] for r in palkat}
            pl=st.selectbox("Jakso",list(va.keys()),key="ppl")
            if st.button("Poista",type="secondary",key="ppb"):
                palkat=[r for r in palkat if r["id"]!=va[pl]]
                st.session_state["palkat"]=palkat
                tallenna_palkat(projekti,palkat)
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# OSTOT — oma tuonti
# ══════════════════════════════════════════════════════════════════════════════
with tab_ostot_v:
    st.subheader("Ostoseuranta – tarvikkeet ja materiaalit")
    _import_ostot("df_ostot","up_ostot",
        "Netvisor → Raportit → Laskentakohderaportti → suodata laskentakohde → vie Exceliin")
    df = _hae("df_ostot")
    if not df.empty:
        _nayta_kululaji(df,"Ostot",["pvm","tosite","lasku","selite","summa","kategoria","nimike_laji","alv_tunnus"])

# ══════════════════════════════════════════════════════════════════════════════
# JÄTEMAKSUT — oma tuonti
# ══════════════════════════════════════════════════════════════════════════════
with tab_jate:
    st.subheader("Jätemaksut – Kuljetusrinki Oy ja muut")
    _import_ostot("df_jate","up_jate",
        "Netvisor → Raportit → Laskentakohderaportti → suodata Kuljetusrinki/Labroc → vie Exceliin")
    df = _hae("df_jate")
    if not df.empty:
        _nayta_kululaji(df,"Jätemaksut",["pvm","tosite","lasku","selite","summa","kategoria","alv_tunnus"])

# ══════════════════════════════════════════════════════════════════════════════
# ALIURAKOITSIJAT — oma tuonti
# ══════════════════════════════════════════════════════════════════════════════
with tab_ali:
    st.subheader("Aliurakoitsijat – RAOS käänteinen ALV")
    _import_ostot("df_ali_osto","up_ali",
        "Netvisor → Raportit → Laskentakohderaportti → suodata RAOS-laskut → vie Exceliin")
    df = _hae("df_ali_osto")
    if not df.empty:
        _nayta_kululaji(df,"Aliurakoitsijat",
            ["pvm","tosite","lasku","selite","summa","kategoria","alv_tunnus","laskentakohteet"])

# ══════════════════════════════════════════════════════════════════════════════
# KALUSTO — oma tuonti
# ══════════════════════════════════════════════════════════════════════════════
with tab_kalusto:
    st.subheader("Kalusto / konevuokra")
    _import_ostot("df_kalusto","up_kalusto",
        "Netvisor → Raportit → Laskentakohderaportti → suodata RK Konevuokraamo → vie Exceliin")
    df = _hae("df_kalusto")
    if not df.empty:
        _nayta_kululaji(df,"Kalusto",["pvm","tosite","lasku","selite","summa","kategoria","alv_tunnus"])

# ══════════════════════════════════════════════════════════════════════════════
# KAIKKI RIVIT — yhdistää kaikki ladatut ostolaskut
# ══════════════════════════════════════════════════════════════════════════════
with tab_kaikki:
    st.subheader("Kaikki ostolaskurivit")
    _import_ostot("df_kaikki","up_kaikki",
        "Lataa tähän kaikki laskentakohderaportit kerralla — data näkyy myös muilla välilehdillä")

    # Yhdistä kaikki osioiden datat
    osat = [_hae(k) for k in ["df_ostot","df_jate","df_ali_osto","df_kalusto","df_kaikki"]
            if not _hae(k).empty]
    if not osat:
        st.info("Lataa aineistoa joltain välilehdeltä tai tästä yllä.")
    else:
        df_yhdistetty = pd.concat(osat, ignore_index=True).drop_duplicates(
            subset=["tosite","lasku","selite","summa"])
        f1,f2,f3 = st.columns(3)
        sk = f1.multiselect("Kategoria", df_yhdistetty["kategoria"].unique(),
                            default=list(df_yhdistetty["kategoria"].unique()))
        sl = f2.multiselect("Kululaji",  df_yhdistetty["kululaji"].unique(),
                            default=list(df_yhdistetty["kululaji"].unique()))
        hk = f3.text_input("Hae selitteestä")
        suod = df_yhdistetty[df_yhdistetty["kategoria"].isin(sk) & df_yhdistetty["kululaji"].isin(sl)].copy()
        if hk:
            suod = suod[suod["selite"].str.contains(hk,case=False,na=False)]
        n = suod[["pvm","tosite","lasku","selite","summa","kategoria","kululaji","alv_tunnus","laskentakohteet"]].copy()
        n["pvm"] = n["pvm"].dt.strftime("%d.%m.%Y")
        st.dataframe(n, use_container_width=True, hide_index=True)
        st.caption(f"{len(suod)} riviä | Yhteensä: {EURO(suod['summa'].sum())}")

# ══════════════════════════════════════════════════════════════════════════════
# YHTEENVETO
# ══════════════════════════════════════════════════════════════════════════════
with tab_yht:
    st.subheader(f"Yhteenveto – {projekti or '(projekti ei asetettu)'}")

    # Myynti
    df_m = _hae("df_myynti")
    if not df_m.empty:
        st.markdown("### 💰 Myynti")
        dp = df_m[df_m["summa"]>0]
        c1,c2,c3 = st.columns(3)
        c1.metric("Laskutettu (alv 0%)", EURO(dp["summa"].sum()))
        c2.metric("Maksettu",            EURO((dp["summa"]-dp["avoimena"]).sum()))
        c3.metric("Avoimena",            EURO(dp["avoimena"].sum()))
        st.divider()

    # Ostokustannukset — yhdistä kaikki
    dfs_osto = [_hae(k) for k in ["df_ostot","df_jate","df_ali_osto","df_kalusto","df_kaikki"] if not _hae(k).empty]
    if dfs_osto:
        df_all = pd.concat(dfs_osto,ignore_index=True).drop_duplicates(subset=["tosite","lasku","selite","summa"])
        st.markdown("### 🧾 Kustannukset kululajeittain")
        pivot = (df_all.groupby(["kululaji","kategoria"])["summa"]
                 .sum().unstack(fill_value=0).reset_index())
        pivot["Yhteensä"] = pivot.select_dtypes("number").sum(axis=1)
        st.dataframe(pivot, use_container_width=True, hide_index=True)
        kls = ["Ostot","Jätemaksut","Aliurakoitsijat","Kalusto"]
        cols = st.columns(len(kls))
        for i,kl in enumerate(kls):
            cols[i].metric(kl, EURO(df_all[df_all["kululaji"]==kl]["summa"].sum()))
        st.divider()
        koos = df_all[df_all["alv_tunnus"].str.upper().eq("KOOS")]["summa"].sum()
        raos = df_all[df_all["alv_tunnus"].str.upper().eq("RAOS")]["summa"].sum()
        st.markdown("### 🧮 ALV-kohtelu")
        st.dataframe(pd.DataFrame({
            "ALV-tunnus":["KOOS","RAOS"],
            "Kuvaus":["Normaali 25,5% – vähennetään tilityksessä","Käänteinen rakennusalan ALV"],
            "Summa (alv 0%)":[EURO(koos),EURO(raos)],
            "ALV-vähennysoikeus":[EURO(koos*0.255),"–"],
        }), use_container_width=True, hide_index=True)
        st.divider()

    # Tuntiseuranta
    viikot = st.session_state.get("tuntiseuranta", lataa_tuntiseuranta(projekti) if projekti else [])
    if viikot:
        df_t = pd.DataFrame(viikot)
        st.markdown("### ⏱️ Tuntiseuranta (omat)")
        c1,c2,c3 = st.columns(3)
        c1.metric("Tunnit yht.", f"{df_t['yht_h'].sum():.1f} h")
        c2.metric("Tuntikust.",  EURO(df_t["tuntikust_eur"].sum()))
        c3.metric("Kaikki yht.",EURO(df_t["kaikki_yht_eur"].sum()))
        st.divider()

    # Palkat
    palkat_y = st.session_state.get("palkat", lataa_palkat(projekti) if projekti else [])
    if palkat_y:
        df_p = pd.DataFrame(palkat_y)
        st.markdown("### 💼 Palkkakustannukset")
        c1,c2 = st.columns(2)
        c1.metric("Bruttopalkka",   EURO(df_p["brutto"].sum()))
        c2.metric(f"Kokonaiskust. (×{sivukulukerroin})", EURO(df_p["kokonaiskust"].sum()))

    if df_m.empty and not dfs_osto and not viikot and not palkat_y:
        st.info("Lataa aineistoa välilehdiltä — yhteenveto täyttyy automaattisesti.")

# ── EXCEL-LATAUS ───────────────────────────────────────────────────────────────
dfs_osto_dl = [_hae(k) for k in ["df_ostot","df_jate","df_ali_osto","df_kalusto","df_kaikki"] if not _hae(k).empty]
if dfs_osto_dl:
    st.divider()
    df_dl = pd.concat(dfs_osto_dl,ignore_index=True).drop_duplicates(subset=["tosite","lasku","selite","summa"])
    c1,c2 = st.columns([3,1])
    c1.markdown("**📥 Lataa kustannusseuranta Excelinä** (Ostot · Jätemaksut · Aliurakoitsijat · Yhteenveto)")
    if c2.button("Luo Excel",type="primary"):
        with st.spinner("Luodaan..."):
            x = luo_excel(df_dl, projekti=projekti or "Projekti", yritys=yritys)
        nm = f"Kustannusseuranta_{(projekti or 'P').replace(' ','_').replace(',','')}.xlsx"
        st.download_button("⬇️ Lataa Excel", data=x, file_name=nm,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ══════════════════════════════════════════════════════════════════════════════
# KÄYTTÄJÄT (vain admin)
# ══════════════════════════════════════════════════════════════════════════════
if tab_kayttajat is not None:
    with tab_kayttajat:
        A.nayta_kayttajahallinta()
