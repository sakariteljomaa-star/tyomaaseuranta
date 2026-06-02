"""
Kalustoseuranta — QR-pohjainen laitekirjanpito
Uudenmaan Asbestipurku Oy

Käynnistys:
    python3 -m streamlit run kalusto_app.py --server.port 8503

QR-koodi osoittaa: https://{app_url}/?kalusto=AP-001
"""

import streamlit as st
import pandas as pd
import qrcode
import io
from datetime import date, datetime
from pathlib import Path

from storage import lataa_globaali, tallenna_globaali
from parser_kalusto import lue_kalustorekisteri

# ── Apufunktiot ────────────────────────────────────────────────────────────────

def lataa_laitteet() -> list:
    return lataa_globaali("kalusto_laitteet")

def tallenna_laitteet(laitteet: list):
    tallenna_globaali("kalusto_laitteet", laitteet)

def lataa_tapahtumat() -> list:
    return lataa_globaali("kalusto_tapahtumat")

def tallenna_tapahtumat(tapahtumat: list):
    tallenna_globaali("kalusto_tapahtumat", tapahtumat)

def _hae_laite(nro: str, laitteet: list) -> dict:
    return next((l for l in laitteet if l["nro"] == nro), {})

def _luo_qr_png(url: str) -> bytes:
    qr = qrcode.QRCode(version=1, box_size=8, border=3,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def _viimeisin_tapahtuma(nro: str, tapahtumat: list) -> dict:
    rivit = [t for t in tapahtumat if t.get("laite_nro") == nro]
    return rivit[-1] if rivit else {}

def _nykyinen_sijainti(nro: str, laitteet: list, tapahtumat: list) -> str:
    laite = _hae_laite(nro, laitteet)
    vt = _viimeisin_tapahtuma(nro, tapahtumat)
    if vt.get("tyyppi") == "checkout":
        return vt.get("tyomaa", "—")
    return laite.get("sijainti", "Varasto")

def _lisaa_tapahtuma(nro: str, tyyppi: str, tyomaa: str, tekija: str,
                     huomio: str, tapahtumat: list) -> list:
    nyt = datetime.now()
    tapahtumat.append({
        "id":        f"{nro}_{nyt.strftime('%Y%m%d_%H%M%S')}",
        "laite_nro": nro,
        "tyyppi":    tyyppi,
        "tyomaa":    tyomaa,
        "pvm":       nyt.strftime("%d.%m.%Y"),
        "klo":       nyt.strftime("%H:%M"),
        "tekija":    tekija,
        "huomio":    huomio,
    })
    return tapahtumat

KUNTO_EMOJI = {"OK": "✅", "Varoitus": "⚠️", "Rikki": "❌", "Huolto": "🔧"}
TYYPPI_LABEL = {
    "checkout": "📤 Lähti työmaakohtaisesti",
    "return":   "📥 Palautettu",
    "vika":     "🔴 Vikailmoitus",
    "kunto":    "🔧 Kuntopäivitys",
}

# ── Sivun asetukset ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Kalustoseuranta", page_icon="🔧", layout="wide")

st.markdown("""
<style>
    .laitekortti { border-radius:12px; padding:20px; margin:8px 0; }
    .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Auth: hallintanäkymä salasanalla, QR-skannaus julkinen ────────────────────
def _hae_hallinta_salasana() -> str:
    try:
        return st.secrets.get("auth", {}).get("kalusto_salasana", "")
    except Exception:
        return ""

# ── URL-parametri: onko QR-skannaus? ─────────────────────────────────────────
params = st.query_params
skannaus_nro = params.get("kalusto", "").upper().strip()

laitteet   = lataa_laitteet()
tapahtumat = lataa_tapahtumat()

# ══════════════════════════════════════════════════════════════════════════════
# QR-SKANNAUSNÄKYMÄ — julkinen, ei vaadi kirjautumista
# ══════════════════════════════════════════════════════════════════════════════
if skannaus_nro:
    laite = _hae_laite(skannaus_nro, laitteet)

    st.title(f"🔧 {skannaus_nro}")

    if not laite:
        st.error(f"Laitetta {skannaus_nro} ei löydy rekisteristä.")
        st.caption("Jos laite on uusi, pyydä työnjohtajaa lisäämään se järjestelmään.")
        st.stop()

    sijainti_nyt = _nykyinen_sijainti(skannaus_nro, laitteet, tapahtumat)
    vt           = _viimeisin_tapahtuma(skannaus_nro, tapahtumat)
    on_tyomaalla = vt.get("tyyppi") == "checkout"

    # Laitekortti
    kunto_e = KUNTO_EMOJI.get(laite.get("kunto","OK"), "✅")
    tila_css = ("background:#E8F5E9;border:2px solid #43A047" if not on_tyomaalla
                else "background:#FFF8E1;border:2px solid #F9A825")
    tila_txt = (f"📦 Varastossa" if not on_tyomaalla
                else f"🏗️ Työmaa: **{sijainti_nyt}**")

    st.markdown(f"""
    <div class='laitekortti' style='{tila_css}'>
    <h2 style='margin:0'>{kunto_e} {laite['laite']}</h2>
    <p style='margin:4px 0;color:#555'>{laite['kategoria']} · {laite.get('merkki','')} · SN: {laite.get('sarjanumero','—')}</p>
    <p style='margin:4px 0;font-size:1.1em'>{tila_txt}</p>
    </div>
    """, unsafe_allow_html=True)

    if laite.get("huomiot"):
        st.info(f"ℹ️ {laite['huomiot']}")

    st.divider()

    # ── Toiminnot ─────────────────────────────────────────────────────────────
    tekija = st.text_input("Nimesi", placeholder="Etunimi", key="sk_tekija")

    if not on_tyomaalla:
        # Laite varastossa → voi lähettää työmaakohtaisesti
        st.subheader("📤 Lähetä työmaakohtaisesti")
        tyomaa = st.text_input("Työmaa / kohde", placeholder="esim. Valteri-koulu", key="sk_tyomaa")
        if st.button("✅ Ota käyttöön", type="primary", use_container_width=True, key="sk_checkout"):
            if not tekija:
                st.error("Syötä nimesi.")
            elif not tyomaa:
                st.error("Syötä työmaan nimi.")
            else:
                tapahtumat = _lisaa_tapahtuma(skannaus_nro, "checkout", tyomaa, tekija, "", tapahtumat)
                tallenna_tapahtumat(tapahtumat)
                st.success(f"✅ {skannaus_nro} merkitty työmaakohtaisesti: {tyomaa}")
                st.rerun()
    else:
        # Laite työmaakohtaisesti → voi palauttaa
        st.subheader("📥 Palauta varastolle")
        palautus_huomio = st.text_input("Huomio palautuksesta (vapaaehtoinen)",
                                         placeholder="Kaikki OK / Suodatin vaihdettu / ...", key="sk_pal_hm")
        if st.button("📥 Palauta varastolle", type="primary", use_container_width=True, key="sk_return"):
            if not tekija:
                st.error("Syötä nimesi.")
            else:
                tapahtumat = _lisaa_tapahtuma(skannaus_nro, "return", "", tekija, palautus_huomio, tapahtumat)
                tallenna_tapahtumat(tapahtumat)
                st.success(f"✅ {skannaus_nro} palautettu varastolle.")
                st.rerun()

    st.divider()

    # ── Vikailmoitus ──────────────────────────────────────────────────────────
    with st.expander("🔴 Ilmoita viasta tai vahingoittumisesta"):
        vika_kuvaus = st.text_area("Kuvaa vika tai vahinko", key="sk_vika",
                                    placeholder="esim. Imurin letku on halki, laite ei käynnisty...")
        if st.button("🔴 Lähetä vikailmoitus", type="secondary", use_container_width=True, key="sk_vika_btn"):
            if not tekija:
                st.error("Syötä nimesi.")
            elif not vika_kuvaus:
                st.error("Kuvaa vika.")
            else:
                tapahtumat = _lisaa_tapahtuma(skannaus_nro, "vika", sijainti_nyt, tekija, vika_kuvaus, tapahtumat)
                # Päivitä laitteen kunto
                for l in laitteet:
                    if l["nro"] == skannaus_nro:
                        l["kunto"] = "Varoitus"
                tallenna_laitteet(laitteet)
                tallenna_tapahtumat(tapahtumat)
                st.success("Vikailmoitus lähetetty työnjohtajalle.")
                st.rerun()

    # ── Historia ──────────────────────────────────────────────────────────────
    historia = [t for t in tapahtumat if t.get("laite_nro") == skannaus_nro]
    if historia:
        with st.expander(f"📋 Historia ({len(historia)} tapahtumaa)"):
            for t in reversed(historia[-10:]):
                label = TYYPPI_LABEL.get(t["tyyppi"], t["tyyppi"])
                kohde = f" → {t['tyomaa']}" if t.get("tyomaa") else ""
                huom  = f"  _{t['huomio']}_" if t.get("huomio") else ""
                st.markdown(f"**{t['pvm']} {t['klo']}** — {label}{kohde}  \n"
                            f"*{t.get('tekija','')}*{huom}")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# HALLINTANÄKYMÄ — salasanalla tai paikallisesti
# ══════════════════════════════════════════════════════════════════════════════
hallinta_pw = _hae_hallinta_salasana()

if hallinta_pw and not st.session_state.get("kalusto_kirjautunut"):
    st.title("🔧 Kalustoseuranta")
    st.markdown("---")
    pw = st.text_input("Hallintasalasana", type="password")
    if st.button("Kirjaudu", type="primary"):
        if pw == hallinta_pw:
            st.session_state["kalusto_kirjautunut"] = True
            st.rerun()
        else:
            st.error("Väärä salasana.")
    st.stop()

st.title("🔧 Kalustoseuranta — Hallinta")
st.caption("Uudenmaan Asbestipurku Oy")

# App URL (käytetään QR-koodin generointiin)
try:
    app_url = st.secrets.get("kalusto", {}).get("app_url", "http://localhost:8503")
except Exception:
    app_url = "http://localhost:8503"

tab_yht, tab_qr, tab_laitteet, tab_tuo, tab_historia = st.tabs([
    "📊 Tilannekuva",
    "📱 QR-koodit",
    "🔧 Laiterekisteri",
    "📥 Tuo Excel",
    "📋 Tapahtumahistoria",
])

# ── TILANNEKUVA ───────────────────────────────────────────────────────────────
with tab_yht:
    st.subheader("Kaluston tilannekuva")

    if not laitteet:
        st.info("Tuo ensin laiterekisteri Excel-tiedostosta (Tuo Excel -välilehti).")
    else:
        # Laske missä kukin laite on
        tilanne = []
        for l in laitteet:
            sij = _nykyinen_sijainti(l["nro"], laitteet, tapahtumat)
            vt  = _viimeisin_tapahtuma(l["nro"], tapahtumat)
            tilanne.append({
                "Nro":       l["nro"],
                "Laite":     l["laite"],
                "Kategoria": l["kategoria"],
                "Sijainti":  sij,
                "Kunto":     KUNTO_EMOJI.get(l.get("kunto","OK"),"✅") + " " + l.get("kunto","OK"),
                "Viimeksi":  f"{vt.get('pvm','')} {vt.get('tekija','')}" if vt else "—",
            })

        df_t = pd.DataFrame(tilanne)

        # Metriikat
        varastossa   = sum(1 for t in tilanne if t["Sijainti"] == "Varasto")
        tyomaalla    = len(tilanne) - varastossa
        vikoja       = sum(1 for l in laitteet if l.get("kunto") != "OK")

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Laitteita yht.", len(tilanne))
        c2.metric("📦 Varastossa",  varastossa)
        c3.metric("🏗️ Työmaakohtaisesti",  tyomaalla)
        c4.metric("⚠️ Vikoja",       vikoja)

        st.divider()

        # Suodatus
        f1, f2 = st.columns(2)
        suod_kat = f1.multiselect("Kategoria", sorted(df_t["Kategoria"].unique()),
                                   default=list(df_t["Kategoria"].unique()))
        suod_sij = f2.multiselect("Sijainti", sorted(df_t["Sijainti"].unique()),
                                   default=list(df_t["Sijainti"].unique()))
        suod = df_t[df_t["Kategoria"].isin(suod_kat) & df_t["Sijainti"].isin(suod_sij)]
        st.dataframe(suod, use_container_width=True, hide_index=True)

# ── QR-KOODIT ─────────────────────────────────────────────────────────────────
with tab_qr:
    st.subheader("📱 QR-koodit tulostettavaksi")
    st.caption(f"App URL: `{app_url}` — muuta Streamlit Secrets -asetuksissa")

    if not laitteet:
        st.info("Tuo ensin laiterekisteri.")
    else:
        # Valitse mitkä laitteet tulostetaan
        kategoriat_qr = sorted(set(l["kategoria"] for l in laitteet if l.get("kategoria")))
        valitut_kat   = st.multiselect("Kategoriat", kategoriat_qr, default=kategoriat_qr, key="qr_kat")
        valitut       = [l for l in laitteet if l.get("kategoria") in valitut_kat]

        st.info(f"{len(valitut)} laitteen QR-koodit — lataa kuvat ja tulosta tarraan tai paperille")

        # Näytä QR-koodit ruudukossa
        cols_per_row = 4
        rivit = [valitut[i:i+cols_per_row] for i in range(0, len(valitut), cols_per_row)]
        for rivi in rivit:
            cols = st.columns(cols_per_row)
            for j, laite in enumerate(rivi):
                url = f"{app_url}/?kalusto={laite['nro']}"
                qr_png = _luo_qr_png(url)
                cols[j].image(qr_png, caption=f"{laite['nro']}\n{laite['laite']}", width=140)

        # Lataa kaikki zip-tiedostona
        if st.button("📦 Lataa kaikki QR-koodit (ZIP)", type="primary"):
            import zipfile
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w") as zf:
                for laite in valitut:
                    url     = f"{app_url}/?kalusto={laite['nro']}"
                    qr_png  = _luo_qr_png(url)
                    zf.writestr(f"{laite['nro']}_{laite['laite'][:20]}.png", qr_png)
            st.download_button("⬇️ Lataa ZIP", data=zip_buf.getvalue(),
                               file_name="qr_koodit.zip", mime="application/zip")

# ── LAITEREKISTERI ────────────────────────────────────────────────────────────
with tab_laitteet:
    st.subheader("🔧 Laiterekisteri")

    if not laitteet:
        st.info("Tuo laiterekisteri Excel-välilehdeltä.")
    else:
        df_l = pd.DataFrame(laitteet)
        # Muokkaus
        muokattava = st.selectbox("Muokkaa laitteen tietoja", [l["nro"] for l in laitteet], key="ml_nro")
        ml = _hae_laite(muokattava, laitteet)
        if ml:
            m1, m2 = st.columns(2)
            ml_kunto  = m1.selectbox("Kunto", ["OK","Varoitus","Rikki","Huolto"],
                                      index=["OK","Varoitus","Rikki","Huolto"].index(ml.get("kunto","OK")),
                                      key="ml_kunto")
            ml_sijainti = m1.text_input("Vakiosijainti (varasto)", value=ml.get("sijainti","Varasto"), key="ml_sij")
            ml_huomiot  = m2.text_area("Huomiot", value=ml.get("huomiot",""), key="ml_hm")
            if st.button("Tallenna muutokset", type="primary", key="ml_tall"):
                for l in laitteet:
                    if l["nro"] == muokattava:
                        l["kunto"]   = ml_kunto
                        l["sijainti"] = ml_sijainti
                        l["huomiot"] = ml_huomiot
                tallenna_laitteet(laitteet)
                st.success(f"✅ {muokattava} päivitetty.")
                st.rerun()

        st.divider()
        st.dataframe(pd.DataFrame(laitteet), use_container_width=True, hide_index=True)

# ── TUO EXCEL ─────────────────────────────────────────────────────────────────
with tab_tuo:
    st.subheader("📥 Tuo laiterekisteri Excel-tiedostosta")
    st.caption("Hyväksyy Kalustonhallinta-XLSX:n sellaisenaan — tunnistaa AP-, IH-, ES- jne. tunnukset automaattisesti.")

    xlsx_f = st.file_uploader("Kalustonhallinta .xlsx", type=["xlsx"], key="kalusto_xlsx")
    if xlsx_f:
        uudet = lue_kalustorekisteri(xlsx_f)
        st.success(f"Löydettiin {len(uudet)} laitetta.")
        st.dataframe(pd.DataFrame(uudet), use_container_width=True, hide_index=True)
        if st.button("✅ Tallenna rekisteriin", type="primary", key="kalusto_tall"):
            # Säilytä olemassa olevien laitteiden kunto- ja sijaintitiedot
            vanhat = {l["nro"]: l for l in laitteet}
            for u in uudet:
                if u["nro"] in vanhat:
                    u["kunto"]   = vanhat[u["nro"]].get("kunto", "OK")
                    u["sijainti"] = vanhat[u["nro"]].get("sijainti", "Varasto")
            tallenna_laitteet(uudet)
            st.success(f"✅ {len(uudet)} laitetta tallennettu rekisteriin!")
            st.rerun()

    st.divider()
    st.subheader("➕ Lisää laite käsin")
    n1, n2 = st.columns(2)
    n_nro   = n1.text_input("Laitetunnus (esim. AP-021)", key="n_nro").upper()
    n_kat   = n1.text_input("Kategoria", placeholder="esim. Alipaineistaja", key="n_kat")
    n_laite = n1.text_input("Laite / Malli", placeholder="esim. Pullman A600U", key="n_laite")
    n_sn    = n2.text_input("Sarjanumero", key="n_sn")
    n_hm    = n2.text_input("Huomiot", key="n_hm")
    n_omist = n2.selectbox("Omistus", ["oma","vuokra"], key="n_omist")
    if st.button("Lisää laite", type="primary", key="n_lisaa"):
        if not n_nro or not n_laite:
            st.error("Syötä laitetunnus ja laite.")
        elif any(l["nro"] == n_nro for l in laitteet):
            st.error(f"{n_nro} on jo rekisterissä.")
        else:
            laitteet.append({"nro":n_nro,"kategoria":n_kat,"laite":n_laite,
                              "merkki":"","sarjanumero":n_sn,"kunto":"OK",
                              "sijainti":"Varasto","huomiot":n_hm,"omistus":n_omist})
            tallenna_laitteet(laitteet)
            st.success(f"✅ {n_nro} lisätty!")
            st.rerun()

# ── TAPAHTUMAHISTORIA ─────────────────────────────────────────────────────────
with tab_historia:
    st.subheader("📋 Tapahtumahistoria")

    if not tapahtumat:
        st.info("Ei tapahtumia vielä.")
    else:
        df_tap = pd.DataFrame(tapahtumat)
        # Suodatus
        h1, h2 = st.columns(2)
        suod_tyyppi = h1.multiselect("Tyyppi", df_tap["tyyppi"].unique(),
                                      default=list(df_tap["tyyppi"].unique()), key="ht")
        suod_laite  = h2.text_input("Hae laitteesta", key="hl")
        df_s = df_tap[df_tap["tyyppi"].isin(suod_tyyppi)]
        if suod_laite:
            df_s = df_s[df_s["laite_nro"].str.contains(suod_laite.upper())]

        df_s = df_s.sort_values(["pvm","klo"], ascending=False).copy()
        df_s["tyyppi"] = df_s["tyyppi"].map(TYYPPI_LABEL).fillna(df_s["tyyppi"])
        st.dataframe(df_s[["pvm","klo","laite_nro","tyyppi","tyomaa","tekija","huomio"]],
                     use_container_width=True, hide_index=True)
        st.caption(f"{len(df_s)} tapahtumaa")
