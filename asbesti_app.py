"""
Asbestikohteet (Cateva) — aliurakkakohteiden hallinta ja dokumentointi
Uudenmaan Asbestipurku Oy

Käynnistys:
    python3 -m streamlit run asbesti_app.py --server.port 8504

Työnkulku (ks. CATEVA_DOKUMENTTIPOHJAT.md):
    Cateva tilaa (työnumero) → kohde järjestelmään → turvallisuussuunnitelma +
    ennakkoilmoituksen esitäyttö AVIin → työmaan aloitus-/lopetusdokumentointi
    puhelimella → puhdastilamittaus (Labroc) + jätetodistus → aloitus- ja
    lopetusraportti PDF → lähetys Catevalle.
"""

import io
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from storage import (
    lataa_globaali, tallenna_globaali,
    lataa_projekti_avain, tallenna_projekti_avain,
    tallenna_tiedosto, lataa_tiedosto, listaa_tiedostot, poista_tiedosto,
    pakkaa_kuva, tiedosto_slug,
)
from translations import tr
import asbesti_dokumentit as DOK

SOVELLUS = "Asbestikohteet"

# ── Tilakone ───────────────────────────────────────────────────────────────────

TILAT_ASB = {
    "uusi":               {"emoji": "🆕", "nimi": "Uusi",                  "väri": "#ECEFF1", "reuna": "#607D8B"},
    "ilmoitettu":         {"emoji": "📨", "nimi": "Ilmoitukset tehty",     "väri": "#E3F0FF", "reuna": "#1E88E5"},
    "kaynnissa":          {"emoji": "🚧", "nimi": "Työ käynnissä",         "väri": "#FFF8E1", "reuna": "#F9A825"},
    "purku_valmis":       {"emoji": "🧹", "nimi": "Purku valmis",          "väri": "#F3E5F5", "reuna": "#8E24AA"},
    "mittaukset_ok":      {"emoji": "🧪", "nimi": "Mittaukset ja jäte ok", "väri": "#E0F2F1", "reuna": "#00897B"},
    "raportti_lahetetty": {"emoji": "✅", "nimi": "Raportti lähetetty",    "väri": "#E8F5E9", "reuna": "#43A047"},
}

ALOITUS_KOHDAT = [
    ("lahtotilanne",  "asb_lahtotilanne"),
    ("suojaukset",    "asb_suojaukset"),
    ("alipaineistus", "asb_alipaineistus"),
    ("mittari",       "asb_mittari"),
    ("kalusto",       "asb_kalusto"),
]

CATEVA_OLETUS = {
    "tilaaja_yritys":        "Cateva Oy",
    "tilaaja_ytunnus":       "1927433-5",
    "tilaaja_yhteyshenkilo": "Pasi Rytkönen",
}


def _badge(tila: str) -> str:
    t = TILAT_ASB.get(tila, TILAT_ASB["uusi"])
    return f"{t['emoji']} {t['nimi']}"


def _badge_html(tila: str) -> str:
    t = TILAT_ASB.get(tila, TILAT_ASB["uusi"])
    tyyli = (f"background:{t['väri']};border:1px solid {t['reuna']};"
             f"border-radius:12px;padding:2px 10px;font-size:0.85em;white-space:nowrap;")
    return f"<span style='{tyyli}'>{t['emoji']} {t['nimi']}</span>"


# ── Data-apufunktiot ───────────────────────────────────────────────────────────

def lataa_kohteet() -> list:
    return lataa_globaali("cateva_kohteet")

def tallenna_kohteet(kohteet: list):
    tallenna_globaali("cateva_kohteet", kohteet)

def _hae_kohde(nro: str, kohteet: list) -> dict:
    return next((k for k in kohteet if k["tyonumero"] == nro), {})

def _projekti(nro: str) -> str:
    return f"cateva_{tiedosto_slug(nro)}"

def lataa_dok(nro: str) -> dict:
    rivit = lataa_projekti_avain(_projekti(nro), "asbesti_dok")
    return rivit[0] if rivit else {"kuvat": [], "havainnot": "", "purku_kuitattu": ""}

def tallenna_dok(nro: str, dok: dict):
    tallenna_projekti_avain(_projekti(nro), "asbesti_dok", [dok])

def lataa_ilmoitustiedot(nro: str) -> dict:
    rivit = lataa_projekti_avain(_projekti(nro), "asbesti_ilmoitukset")
    return rivit[0] if rivit else {}

def tallenna_ilmoitustiedot(nro: str, tiedot: dict):
    tallenna_projekti_avain(_projekti(nro), "asbesti_ilmoitukset", [tiedot])

def lataa_patevyydet() -> list:
    return lataa_globaali("asbesti_patevyydet")

def tallenna_patevyydet(rivit: list):
    tallenna_globaali("asbesti_patevyydet", rivit)


def _liitteet(nro: str) -> list:
    return listaa_tiedostot(f"{tiedosto_slug(nro)}/liitteet")

def _mittaus_ok(liitteet: list) -> bool:
    return any("puhdastila" in p for p in liitteet)

def _jate_ok(liitteet: list) -> bool:
    return any("jatetodistus" in p for p in liitteet)


def _aloitus_puuttuvat(dok: dict) -> list:
    vaiheet = {k.get("vaihe") for k in dok.get("kuvat", [])}
    return [avain for avain, _ in ALOITUS_KOHDAT if avain not in vaiheet]

def _lopetus_kuvia(dok: dict) -> int:
    return sum(1 for k in dok.get("kuvat", []) if k.get("vaihe") == "lopetus")


def laske_tila(kohde: dict, dok: dict, liitteet: list) -> str:
    if kohde.get("raportti_lahetetty"):
        return "raportti_lahetetty"
    if _mittaus_ok(liitteet) and _jate_ok(liitteet):
        return "mittaukset_ok"
    if dok.get("purku_kuitattu"):
        return "purku_valmis"
    if not _aloitus_puuttuvat(dok) and dok.get("kuvat"):
        return "kaynnissa"
    if kohde.get("ennakkoilmoitus_jatetty") and kohde.get("suunnitelma_luotu"):
        return "ilmoitettu"
    return "uusi"


def paivita_tila(nro: str):
    """Laskee kohteen tilan uudelleen ja tallentaa sen rekisteriin."""
    kohteet = lataa_kohteet()
    kohde = _hae_kohde(nro, kohteet)
    if not kohde:
        return
    uusi = laske_tila(kohde, lataa_dok(nro), _liitteet(nro))
    if uusi != kohde.get("tila"):
        kohde["tila"] = uusi
        tallenna_kohteet(kohteet)


def _pvm_fi(iso: str) -> str:
    try:
        return date.fromisoformat(iso).strftime("%-d.%-m.%Y")
    except Exception:
        return iso or "—"


def _loki(toiminto: str, kohde: str = ""):
    try:
        from loki import kirjaa
        kirjaa(st.session_state.get("kayttaja", {}), SOVELLUS, toiminto, kohde)
    except Exception:
        pass


def _laheta_email(aihe: str, runko: str, liite_nimi: str, liite_data: bytes):
    """Lähettää sähköpostin [smtp]-secretsien asetuksilla. Palauttaa (ok, viesti)."""
    import smtplib
    from email.message import EmailMessage
    try:
        conf = st.secrets["smtp"]
        host, user = conf["host"], conf["user"]
        salasana = conf["password"]
        vastaanottaja = conf["cateva_vastaanottaja"]
        portti = int(conf.get("port", 465))
    except Exception:
        return False, ("Sähköpostiasetukset puuttuvat. Lisää Streamlit Secretsiin "
                       "[smtp] host, port, user, password, cateva_vastaanottaja.")
    try:
        msg = EmailMessage()
        msg["From"] = user
        msg["To"] = vastaanottaja
        msg["Subject"] = aihe
        msg.set_content(runko)
        msg.add_attachment(liite_data, maintype="application", subtype="pdf",
                           filename=liite_nimi)
        if portti == 465:
            with smtplib.SMTP_SSL(host, portti, timeout=30) as s:
                s.login(user, salasana)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, portti, timeout=30) as s:
                s.starttls()
                s.login(user, salasana)
                s.send_message(msg)
        return True, f"Lähetetty: {vastaanottaja}"
    except Exception as e:
        return False, f"Lähetys epäonnistui: {e}"


def _patevyys_varoitukset(patevyydet: list) -> list:
    """Palauttaa varoitusrivit vanhenevista pätevyyksistä (alle 60 vrk)."""
    varoitukset = []
    raja = date.today() + timedelta(days=60)
    for p in patevyydet:
        for kentta, nimi in [("terveystarkastus_voimassa", "terveystarkastus")]:
            arvo = p.get(kentta, "")
            try:
                voimassa = date.fromisoformat(arvo)
            except Exception:
                continue
            if voimassa < date.today():
                varoitukset.append(f"🔴 {p.get('nimi','?')}: {nimi} VANHENTUNUT {_pvm_fi(arvo)}")
            elif voimassa <= raja:
                varoitukset.append(f"🟠 {p.get('nimi','?')}: {nimi} vanhenee {_pvm_fi(arvo)}")
    return varoitukset


def _ilmoitus_varoitus(kohde: dict) -> str:
    """7 vrk sääntö: varoitus jos aloitus lähellä eikä ennakkoilmoitusta jätetty."""
    if kohde.get("ennakkoilmoitus_jatetty") or kohde.get("raportti_lahetetty"):
        return ""
    try:
        aloitus = date.fromisoformat(kohde.get("aloitus_pvm", ""))
    except Exception:
        return ""
    paivia = (aloitus - date.today()).days
    if paivia < 0:
        return (f"🔴 {kohde['tyonumero']} {kohde.get('osoite','')}: aloitus ohitettu "
                f"eikä ennakkoilmoitusta ole kuitattu jätetyksi!")
    if paivia < 7:
        return (f"🔴 {kohde['tyonumero']} {kohde.get('osoite','')}: aloitukseen {paivia} vrk "
                f"— ennakkoilmoitusta EI ole jätetty (vaatimus 7 vrk ennen, VNa 798/2015)!")
    return ""


# ── Sivun asetukset ja kirjautuminen ───────────────────────────────────────────

_LOGO = str(Path(__file__).parent / "logo.png")
_FAVI = str(Path(__file__).parent / "favicon.png")
st.set_page_config(page_title="Asbestikohteet",
                   page_icon=_FAVI if Path(_FAVI).exists() else "☣️", layout="wide")
if Path(_LOGO).exists():
    try:
        st.logo(_LOGO, size="large")
    except Exception:
        pass
st.markdown("""
<style>
    img[data-testid='stLogo']{height:3rem;}
    .block-container { padding-top: 1rem; }
    h1 { font-size: 1.5rem !important; }
    .stButton button { min-height: 2.6rem; }
</style>
""", unsafe_allow_html=True)

import auth as A

kayttaja = A.kirjaudu_gate("Asbestikohteet (Cateva)")
rooli    = kayttaja["rooli"]
on_tj    = A.voi_hyvaksya(rooli)             # admin + työnjohtaja
on_admin = A.voi_hallita_kayttajia(rooli)    # vain admin
on_tyontekija = rooli == "tyontekija"

with st.sidebar:
    st.caption(f"👤 {kayttaja.get('nimi', kayttaja['tunnus'])} · {A.ROOLIT[rooli]['nimi']}")
    # Kielivalinta (työntekijän dokumentointinäkymä on kaksikielinen)
    c_fi, c_ru = st.columns(2)
    if c_fi.button("🇫🇮 Suomi", use_container_width=True,
                   type="primary" if st.session_state.get("kieli", "fi") == "fi" else "secondary"):
        st.session_state["kieli"] = "fi"
        st.rerun()
    if c_ru.button("🇷🇺 Русский", use_container_width=True,
                   type="primary" if st.session_state.get("kieli", "fi") == "ru" else "secondary"):
        st.session_state["kieli"] = "ru"
        st.rerun()
    if st.button("🔓 Kirjaudu ulos", use_container_width=True):
        A.kirjaudu_ulos()
        st.rerun()

kieli = st.session_state.get("kieli", "fi")
kohteet = lataa_kohteet()


# ══════════════════════════════════════════════════════════════════════════════
# DOKUMENTOINTINÄKYMÄ (työntekijä + työnjohto) — prompti 4
# ══════════════════════════════════════════════════════════════════════════════

def _tallenna_kuvat(nro: str, vaihe: str, tiedostot: list, teksti: str):
    dok = lataa_dok(nro)
    aika = datetime.now().strftime("%Y%m%d_%H%M%S")
    for i, f in enumerate(tiedostot):
        data = pakkaa_kuva(f.getvalue())
        polku = f"{tiedosto_slug(nro)}/{vaihe}/{aika}_{i}.jpg"
        tallenna_tiedosto(polku, data, "image/jpeg")
        dok.setdefault("kuvat", []).append({
            "polku":  polku,
            "vaihe":  vaihe,
            "teksti": teksti.strip(),
            "aika":   datetime.now().strftime("%d.%m.%Y %H:%M"),
            "tekija": kayttaja.get("nimi", kayttaja["tunnus"]),
        })
    tallenna_dok(nro, dok)
    paivita_tila(nro)
    _loki("Tallensi kuvia", f"{nro}/{vaihe} ({len(tiedostot)} kpl)")


def _kuvakohta(nro: str, vaihe: str, otsikko: str, dok: dict, pakollinen: bool = True):
    """Yksi tarkistuslistan kohta: tila + kuvien lataus."""
    kuvat = [k for k in dok.get("kuvat", []) if k.get("vaihe") == vaihe]
    if kuvat:
        tila_txt = f"🟢 {len(kuvat)} {tr('asb_kuvia', kieli)}"
    elif pakollinen:
        tila_txt = f"🔴 {tr('asb_puuttuu', kieli)}"
    else:
        tila_txt = "⚪"
    with st.expander(f"{otsikko} — {tila_txt}", expanded=not kuvat and pakollinen):
        nollaus = st.session_state.get(f"reset_{nro}_{vaihe}", 0)
        uudet = st.file_uploader(
            tr("asb_ota_kuva", kieli), type=["jpg", "jpeg", "png"],
            accept_multiple_files=True, key=f"up_{nro}_{vaihe}_{nollaus}")
        kamera = st.camera_input("📷", key=f"cam_{nro}_{vaihe}_{nollaus}",
                                 label_visibility="collapsed")
        if kamera:
            uudet = list(uudet or []) + [kamera]
        teksti = st.text_input(tr("asb_kuvateksti", kieli), key=f"txt_{nro}_{vaihe}_{nollaus}")
        if uudet and st.button(tr("asb_tallenna_kuvat", kieli), type="primary",
                               key=f"save_{nro}_{vaihe}", use_container_width=True):
            _tallenna_kuvat(nro, vaihe, uudet, teksti)
            st.session_state[f"reset_{nro}_{vaihe}"] = nollaus + 1
            st.success(tr("asb_tallennettu", kieli))
            st.rerun()
        if kuvat and st.checkbox("🖼️", key=f"show_{nro}_{vaihe}",
                                 help="Näytä tallennetut kuvat"):
            sarakkeet = st.columns(3)
            for i, k in enumerate(kuvat):
                data = lataa_tiedosto(k["polku"])
                if data:
                    sarakkeet[i % 3].image(
                        data, caption=f"{k.get('aika','')} {k.get('teksti','')}".strip(),
                        use_container_width=True)


def nayta_dokumentointi(sallitut_kohteet: list):
    st.subheader(tr("asb_title", kieli))
    if not sallitut_kohteet:
        st.info(tr("asb_ei_kohteita", kieli))
        return

    valinnat = {f"{k['tyonumero']} — {k.get('osoite','')}": k["tyonumero"]
                for k in sallitut_kohteet}
    valittu = st.selectbox(tr("asb_valitse_kohde", kieli), list(valinnat.keys()))
    nro = valinnat[valittu]
    kohde = _hae_kohde(nro, sallitut_kohteet)
    dok = lataa_dok(nro)

    st.markdown(f"**{tr('asb_tyonumero', kieli)}:** {nro} &nbsp;·&nbsp; "
                f"{_badge_html(kohde.get('tila', 'uusi'))}", unsafe_allow_html=True)
    st.divider()

    # ── Aloitusdokumentointi ──────────────────────────────────────────────────
    st.markdown(f"### {tr('asb_aloitus', kieli)}")
    for vaihe, avain in ALOITUS_KOHDAT:
        _kuvakohta(nro, vaihe, tr(avain, kieli), dok)

    puuttuvat = _aloitus_puuttuvat(dok)
    if not puuttuvat:
        st.success(tr("asb_aloitus_ok", kieli))
    st.divider()

    # ── Lopetusdokumentointi ──────────────────────────────────────────────────
    st.markdown(f"### {tr('asb_lopetus', kieli)}")
    _kuvakohta(nro, "lopetus", tr("asb_lopetuskuvat", kieli), dok,
               pakollinen=bool(not puuttuvat))

    havainnot = st.text_area(tr("asb_havainnot", kieli),
                             value=dok.get("havainnot", ""),
                             placeholder=tr("asb_havainnot_ph", kieli), height=100)
    if st.button(tr("asb_tallenna_hav", kieli), use_container_width=True):
        dok["havainnot"] = havainnot
        tallenna_dok(nro, dok)
        _loki("Tallensi havainnot", nro)
        st.success(tr("asb_tallennettu", kieli))

    if _lopetus_kuvia(dok) > 0 and not dok.get("purku_kuitattu"):
        if st.button(tr("asb_purku_valmis", kieli), type="primary", use_container_width=True):
            dok["purku_kuitattu"] = datetime.now().strftime("%d.%m.%Y %H:%M")
            dok["havainnot"] = havainnot
            tallenna_dok(nro, dok)
            paivita_tila(nro)
            _loki("Kuittasi purun valmiiksi", nro)
            st.rerun()
    elif dok.get("purku_kuitattu"):
        st.success(f"✅ {tr('asb_purku_kuitattu', kieli)}: {dok['purku_kuitattu']}")


# Työntekijä näkee VAIN dokumentointinäkymän omista kohteistaan
if on_tyontekija:
    st.title(f"☣️ {tr('asb_title', kieli)}")
    omat = [k for k in kohteet
            if kayttaja["tunnus"] in k.get("tyontekijat", [])
            and not k.get("raportti_lahetetty")]
    nayta_dokumentointi(omat)
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# TYÖNJOHDON NÄKYMÄT
# ══════════════════════════════════════════════════════════════════════════════

st.title("☣️ Asbestikohteet — Cateva-aliurakat")
st.caption("Uudenmaan Asbestipurku Oy · työnumero on kaiken avain")

valilehti_nimet = ["📋 Kohteet", "📄 Ilmoitukset", "📸 Dokumentointi",
                   "📑 Raportti", "🧪 Labroc-tulokset", "🎓 Pätevyydet"]
if on_admin:
    valilehti_nimet.append("👤 Käyttäjät")
_vl = st.tabs(valilehti_nimet)
tab_kohteet, tab_ilmoitukset, tab_dok, tab_raportti, tab_labroc, tab_patevyydet = _vl[:6]
tab_kayttajat = _vl[6] if on_admin else None

patevyydet = lataa_patevyydet()


# ── KOHTEET (prompti 1) ───────────────────────────────────────────────────────

with tab_kohteet:
    aktiiviset = [k for k in kohteet if not k.get("raportti_lahetetty")]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kohteita yhteensä", len(kohteet))
    c2.metric("Aktiivisia", len(aktiiviset))
    c3.metric("Käynnissä", sum(1 for k in kohteet if k.get("tila") == "kaynnissa"))
    c4.metric("Valmiita", sum(1 for k in kohteet if k.get("tila") == "raportti_lahetetty"))

    # Varoitukset: 7 vrk -sääntö ja vanhenevat pätevyydet
    varoitukset = [v for v in (_ilmoitus_varoitus(k) for k in kohteet) if v]
    varoitukset += _patevyys_varoitukset(patevyydet)
    for v in varoitukset:
        st.error(v) if v.startswith("🔴") else st.warning(v)

    st.divider()

    if kohteet:
        rivit = []
        for k in sorted(kohteet, key=lambda x: x.get("aloitus_pvm", ""), reverse=True):
            rivit.append({
                "Työnumero": k["tyonumero"],
                "Osoite": k.get("osoite", ""),
                "Tila": _badge(k.get("tila", "uusi")),
                "Aloitus": _pvm_fi(k.get("aloitus_pvm", "")),
                "Lopetus": _pvm_fi(k.get("lopetus_pvm", "")),
                "Vastuuhenkilö": k.get("vastuuhenkilo", ""),
                "Työntekijät": ", ".join(k.get("tyontekijat", [])),
                "Ennakkoilm.": "✅ " + _pvm_fi(k["ennakkoilmoitus_jatetty"])
                               if k.get("ennakkoilmoitus_jatetty") else "—",
            })
        st.dataframe(pd.DataFrame(rivit), use_container_width=True, hide_index=True)
    else:
        st.info("Ei kohteita vielä. Lisää ensimmäinen Cateva-kohde alta.")

    if on_tj:
        tyontekija_tunnukset = [k["tunnus"] for k in A.lataa_kayttajat()
                                if k.get("rooli") == "tyontekija" and k.get("aktiivinen", True)]

        with st.expander("➕ Lisää kohde", expanded=not kohteet):
            u1, u2 = st.columns(2)
            u_nro    = u1.text_input("Catevan työnumero / yksilöintiviite *", key="ak_nro")
            u_osoite = u1.text_input("Osoite *", key="ak_osoite",
                                     placeholder="esim. Koroistentie 8 C 19, Helsinki")
            u_kunta  = u1.text_input("Sijaintikunta", key="ak_kunta")
            u_nimi   = u1.text_input("Työmaan nimi (tyhjä = osoite)", key="ak_nimi")
            u_vastuu = u2.text_input("Meidän vastuuhenkilö",
                                     value=kayttaja.get("nimi", ""), key="ak_vastuu")
            u_aloitus = u2.date_input("Suunniteltu aloitus", value=None, key="ak_aloitus",
                                      format="DD.MM.YYYY")
            u_lopetus = u2.date_input("Suunniteltu lopetus", value=None, key="ak_lopetus",
                                      format="DD.MM.YYYY")
            u_tt      = u2.multiselect("Työntekijät", tyontekija_tunnukset, key="ak_tt")
            u_kuvaus  = st.text_area("Kuvaus / Catevan kartoituksen tiedot", key="ak_kuvaus",
                                     placeholder="esim. C19 kph lattia: betonin pikisively, antofylliitti")
            y1, y2, y3 = st.columns(3)
            u_t_hlo = y1.text_input("Catevan yhteyshenkilö",
                                    value=CATEVA_OLETUS["tilaaja_yhteyshenkilo"], key="ak_thlo")
            u_t_puh = y2.text_input("Yhteyshenkilön puhelin", key="ak_tpuh")
            u_t_em  = y3.text_input("Yhteyshenkilön sähköposti", key="ak_tem")

            if st.button("Luo kohde", type="primary", key="ak_luo"):
                nro = u_nro.strip()
                if not nro or not u_osoite.strip():
                    st.error("Työnumero ja osoite vaaditaan.")
                elif any(k["tyonumero"] == nro for k in kohteet):
                    st.error(f"Työnumero {nro} on jo rekisterissä.")
                else:
                    kohteet.append({
                        "tyonumero": nro,
                        "osoite": u_osoite.strip(),
                        "kunta": u_kunta.strip(),
                        "kohde_nimi": u_nimi.strip() or u_osoite.strip(),
                        "vastuuhenkilo": u_vastuu.strip(),
                        "aloitus_pvm": u_aloitus.isoformat() if u_aloitus else "",
                        "lopetus_pvm": u_lopetus.isoformat() if u_lopetus else "",
                        "tyontekijat": u_tt,
                        "kuvaus": u_kuvaus.strip(),
                        "tilaaja_yritys": CATEVA_OLETUS["tilaaja_yritys"],
                        "tilaaja_ytunnus": CATEVA_OLETUS["tilaaja_ytunnus"],
                        "tilaaja_yhteyshenkilo": u_t_hlo.strip(),
                        "tilaaja_puhelin": u_t_puh.strip(),
                        "tilaaja_email": u_t_em.strip(),
                        "tila": "uusi",
                        "luotu": date.today().isoformat(),
                    })
                    tallenna_kohteet(kohteet)
                    _loki("Loi kohteen", nro)
                    st.success(f"✅ Kohde {nro} luotu.")
                    st.rerun()

        if kohteet:
            with st.expander("✏️ Muokkaa kohdetta"):
                m_nro = st.selectbox("Kohde", [k["tyonumero"] for k in kohteet], key="am_nro")
                mk = _hae_kohde(m_nro, kohteet)
                m1, m2 = st.columns(2)
                mk_osoite = m1.text_input("Osoite", value=mk.get("osoite", ""), key="am_osoite")
                mk_kunta  = m1.text_input("Sijaintikunta", value=mk.get("kunta", ""), key="am_kunta")
                mk_vastuu = m1.text_input("Vastuuhenkilö", value=mk.get("vastuuhenkilo", ""), key="am_vastuu")

                def _pvm_arvo(iso):
                    try:
                        return date.fromisoformat(iso)
                    except Exception:
                        return None
                mk_aloitus = m2.date_input("Aloitus", value=_pvm_arvo(mk.get("aloitus_pvm", "")),
                                           key="am_aloitus", format="DD.MM.YYYY")
                mk_lopetus = m2.date_input("Lopetus", value=_pvm_arvo(mk.get("lopetus_pvm", "")),
                                           key="am_lopetus", format="DD.MM.YYYY")
                mk_tt = m2.multiselect("Työntekijät", tyontekija_tunnukset,
                                       default=[t for t in mk.get("tyontekijat", [])
                                                if t in tyontekija_tunnukset], key="am_tt")
                mk_kuvaus = st.text_area("Kuvaus", value=mk.get("kuvaus", ""), key="am_kuvaus")

                b1, b2 = st.columns(2)
                if b1.button("💾 Tallenna muutokset", type="primary", key="am_tall"):
                    mk.update({
                        "osoite": mk_osoite.strip(), "kunta": mk_kunta.strip(),
                        "vastuuhenkilo": mk_vastuu.strip(),
                        "aloitus_pvm": mk_aloitus.isoformat() if mk_aloitus else "",
                        "lopetus_pvm": mk_lopetus.isoformat() if mk_lopetus else "",
                        "tyontekijat": mk_tt, "kuvaus": mk_kuvaus.strip(),
                    })
                    tallenna_kohteet(kohteet)
                    _loki("Muokkasi kohdetta", m_nro)
                    st.success("Tallennettu.")
                    st.rerun()
                if on_admin and b2.button("🗑️ Poista kohde", key="am_poista"):
                    if st.session_state.get("am_poisto_varmistus") == m_nro:
                        tallenna_kohteet([k for k in kohteet if k["tyonumero"] != m_nro])
                        _loki("Poisti kohteen", m_nro)
                        st.session_state.pop("am_poisto_varmistus", None)
                        st.rerun()
                    else:
                        st.session_state["am_poisto_varmistus"] = m_nro
                        st.warning(f"Paina uudelleen vahvistaaksesi kohteen {m_nro} poiston. "
                                   "Kuvat ja dokumentit säilyvät tallennustilassa.")


# ── ILMOITUKSET (prompti 3) ───────────────────────────────────────────────────

with tab_ilmoitukset:
    if not on_tj:
        st.info("Vain työnjohto voi hallita ilmoituksia.")
    elif not kohteet:
        st.info("Lisää ensin kohde Kohteet-välilehdellä.")
    else:
        i_nro = st.selectbox("Kohde", [f"{k['tyonumero']} — {k.get('osoite','')}" for k in kohteet],
                             key="ilm_nro").split(" — ")[0]
        ik = _hae_kohde(i_nro, kohteet)
        ilm = lataa_ilmoitustiedot(i_nro)

        varoitus = _ilmoitus_varoitus(ik)
        if varoitus:
            st.error(varoitus)
        if ik.get("ennakkoilmoitus_jatetty"):
            st.success(f"✅ Ennakkoilmoitus kuitattu jätetyksi {_pvm_fi(ik['ennakkoilmoitus_jatetty'])}")

        st.markdown("#### Kohteen ja työn tiedot")
        f1, f2 = st.columns(2)
        i_tarkenne = f1.text_area("Tarkenne (kartoituksen löydös)", height=80,
                                  value=ilm.get("tarkenne", ik.get("kuvaus", "")), key="i_tarkenne")
        i_materiaali = f1.text_input("Purettava asbestipitoinen materiaali",
                                     value=ilm.get("materiaali", ""), key="i_materiaali",
                                     placeholder="esim. Vaalea asbesti, antofylliitti")
        i_sijainti = f1.text_input("Asbestin sijainti",
                                   value=ilm.get("sijainti", ""), key="i_sijainti",
                                   placeholder="esim. kph lattian pikisively")
        i_alueet = f1.text_input("Yksilöidyt alueet, joilla työ tehdään",
                                 value=ilm.get("alueet", ""), key="i_alueet")
        i_menetelma = f2.selectbox("Purkutyömenetelmä",
                                   ["Osastointimenetelmä", "Purkupussimenetelmä",
                                    "Kokonaisena irrottamalla", "Upotusmenetelmä",
                                    "Märkäpurku", "Muu menetelmä"],
                                   index=["Osastointimenetelmä", "Purkupussimenetelmä",
                                          "Kokonaisena irrottamalla", "Upotusmenetelmä",
                                          "Märkäpurku", "Muu menetelmä"].index(
                                              ilm.get("menetelma", "Osastointimenetelmä")),
                                   key="i_menetelma")
        i_men_kuvaus = f2.text_area("Menetelmän kuvaus", height=80,
                                    value=ilm.get("menetelma_kuvaus", ""), key="i_men_kuvaus")
        i_osastointi = f2.text_input("Osastointi",
                                     value=ilm.get("osastointi", "Osastoidaan"), key="i_osastointi")
        i_rajaaminen = f2.text_input("Altistumisalueen rajaaminen",
                                     value=ilm.get("rajaaminen",
                                                   "Purkutilat merkitään ja pääsy purkualueelle estetään työn aikana."),
                                     key="i_rajaaminen")

        f3, f4 = st.columns(2)
        i_suojaimet = f3.text_area("Henkilösuojainten valinta", height=80,
                                   value=ilm.get("suojaimet",
                                                 "Hengityksensuojaimet tarkastetaan päällisin puolin joka kerta ennen "
                                                 "osastoinnin sisään menoa. Purkutyössä käytetään moottoroitua "
                                                 "hengityksensuojainta ja kokomaskia."), key="i_suojaimet")
        i_jate = f3.text_input("Jätteiden lopullinen sijoituspaikka",
                               value=ilm.get("jatteen_sijoituspaikka",
                                             "Kiimassuon jätekeskus Forssa, Kuljetusrinki Oy"), key="i_jate")
        i_mittaaja = f4.text_input("Ilmamittauksen suorittaja kohteessa",
                                   value=ilm.get("ilmamittaus_suorittaja", ""), key="i_mittaaja")
        i_labra = f4.text_input("Näytteen analysointipaikka",
                                value=ilm.get("analysointipaikka", "Labroc Oy, Helsinki"), key="i_labra")

        st.markdown("#### Kartoitus (Catevan raportista)")
        k1, k2, k3 = st.columns(3)
        i_kart_hav = k1.text_input("Havainnot (sijainti, määrä, laatu)",
                                   value=ilm.get("kartoitus_havainnot", ""), key="i_kart_hav")
        i_kart_pvm = k2.text_input("Kartoituksen suorituspäivä",
                                   value=ilm.get("kartoitus_pvm", ""), key="i_kart_pvm")
        i_kartoittaja = k3.text_input("Kartoittaja + yhteystiedot",
                                      value=ilm.get("kartoittaja", ""), key="i_kartoittaja",
                                      placeholder="esim. Tom Laxén / Cateva Oy")

        st.markdown("#### Työntekijät ja kalusto ilmoitukseen")
        v1, v2 = st.columns(2)
        pat_nimet = [p.get("nimi", "") for p in patevyydet]
        i_tt = v1.multiselect("Purkutyöntekijät (pätevyysrekisteristä)", pat_nimet,
                              default=[n for n in ilm.get("tyontekijat", []) if n in pat_nimet],
                              key="i_tt")
        laitteet_kaikki = lataa_globaali("kalusto_laitteet")
        laite_valinnat = {f"{l.get('nro','')} {l.get('laite','')}": l for l in laitteet_kaikki}
        i_laitteet = v2.multiselect("Ilmankäsittelylaitteet (kalustorekisteristä)",
                                    list(laite_valinnat.keys()),
                                    default=[v for v in ilm.get("laitteet", [])
                                             if v in laite_valinnat], key="i_laitteet")

        if st.button("💾 Tallenna ilmoitustiedot", key="i_tallenna"):
            ilm.update({
                "tarkenne": i_tarkenne, "materiaali": i_materiaali, "sijainti": i_sijainti,
                "alueet": i_alueet, "menetelma": i_menetelma, "menetelma_kuvaus": i_men_kuvaus,
                "osastointi": i_osastointi, "rajaaminen": i_rajaaminen,
                "suojaimet": i_suojaimet, "jatteen_sijoituspaikka": i_jate,
                "ilmamittaus_suorittaja": i_mittaaja, "analysointipaikka": i_labra,
                "kartoitus_havainnot": i_kart_hav, "kartoitus_pvm": i_kart_pvm,
                "kartoittaja": i_kartoittaja, "tyontekijat": i_tt, "laitteet": i_laitteet,
            })
            tallenna_ilmoitustiedot(i_nro, ilm)
            st.success("Ilmoitustiedot tallennettu.")

        st.divider()
        g1, g2 = st.columns(2)

        def _yhteiset_tiedot():
            return {
                "kohde_nimi": ik.get("kohde_nimi", ik.get("osoite", "")),
                "tyonumero": i_nro,
                "pvm": date.today().strftime("%-d.%-m.%Y"),
                "osoite": ik.get("osoite", ""), "kunta": ik.get("kunta", ""),
                "aloitus_pvm": _pvm_fi(ik.get("aloitus_pvm", "")),
                "lopetus_pvm": _pvm_fi(ik.get("lopetus_pvm", "")),
                "tilaaja_yritys": ik.get("tilaaja_yritys", ""),
                "tilaaja_ytunnus": ik.get("tilaaja_ytunnus", ""),
                "tilaaja_yhteyshenkilo": ik.get("tilaaja_yhteyshenkilo", ""),
                "tilaaja_puhelin": ik.get("tilaaja_puhelin", ""),
                "tilaaja_email": ik.get("tilaaja_email", ""),
                **{k: v for k, v in ilm.items() if isinstance(v, str)},
            }

        with g1:
            if st.button("📄 Luo turvallisuussuunnitelma (PDF)", type="primary",
                         use_container_width=True, key="g_suunnitelma"):
                tiedot = _yhteiset_tiedot()
                tiedot["osallistujat"] = [(kayttaja.get("nimi", ""), f"{DOK.YRITYS['nimi']}, Työnjohto")] + \
                                         [(n, f"{DOK.YRITYS['nimi']}, Purkutyö") for n in i_tt]
                tiedot["vastuu_suorittaja"] = ik.get("vastuuhenkilo", "")
                tiedot["vastuu_tilaaja"] = ik.get("tilaaja_yhteyshenkilo", "")
                tiedot["paivitykset"] = kayttaja.get("nimi", "")
                tiedot["allekirjoittaja"] = kayttaja.get("nimi", "")
                tiedot["allekirjoittaja_titteli"] = "Työnjohto"
                pdf = DOK.luo_turvallisuussuunnitelma(tiedot)
                polku = f"{tiedosto_slug(i_nro)}/dokumentit/turvallisuussuunnitelma.pdf"
                tallenna_tiedosto(polku, pdf, "application/pdf")
                ik["suunnitelma_luotu"] = date.today().isoformat()
                tallenna_kohteet(kohteet)
                st.session_state["pdf_suunnitelma"] = pdf
                _loki("Loi turvallisuussuunnitelman", i_nro)
                paivita_tila(i_nro)
            if st.session_state.get("pdf_suunnitelma"):
                st.download_button("⬇️ Lataa turvallisuussuunnitelma",
                                   data=st.session_state["pdf_suunnitelma"],
                                   file_name=f"turvallisuussuunnitelma_{tiedosto_slug(i_nro)}.pdf",
                                   mime="application/pdf", use_container_width=True)

        with g2:
            if st.button("📄 Luo ennakkoilmoituksen esitäyttö (PDF)", type="primary",
                         use_container_width=True, key="g_ennakko"):
                tiedot = _yhteiset_tiedot()
                tiedot["ilmoittaja"] = kayttaja.get("nimi", "")
                valitut_pat = [p for p in patevyydet if p.get("nimi") in i_tt]
                valitut_laitteet = [laite_valinnat[v] for v in i_laitteet]
                pdf = DOK.luo_ennakkoilmoitus_esitaytto(tiedot, valitut_pat, valitut_laitteet)
                polku = f"{tiedosto_slug(i_nro)}/dokumentit/ennakkoilmoitus_esitaytto.pdf"
                tallenna_tiedosto(polku, pdf, "application/pdf")
                st.session_state["pdf_ennakko"] = pdf
                _loki("Loi ennakkoilmoituksen esitäytön", i_nro)
            if st.session_state.get("pdf_ennakko"):
                st.download_button("⬇️ Lataa esitäyttö",
                                   data=st.session_state["pdf_ennakko"],
                                   file_name=f"ennakkoilmoitus_esitaytto_{tiedosto_slug(i_nro)}.pdf",
                                   mime="application/pdf", use_container_width=True)

        st.divider()
        st.markdown("#### Ennakkoilmoituksen jättö AVIin")
        st.caption("Ilmoitus jätetään AVIn sähköiseen asiointiin käsin esitäytön tiedoilla. "
                   "Kuittaa tähän kun se on jätetty — 7 vrk -valvonta perustuu kuittaukseen.")
        j1, j2 = st.columns([1, 2])
        j_pvm = j1.date_input("Jättöpäivä", value=date.today(), key="j_pvm", format="DD.MM.YYYY")
        if not ik.get("ennakkoilmoitus_jatetty"):
            if j2.button("✅ Merkitse ennakkoilmoitus jätetyksi", type="primary", key="j_kuittaa"):
                ik["ennakkoilmoitus_jatetty"] = j_pvm.isoformat()
                tallenna_kohteet(kohteet)
                paivita_tila(i_nro)
                _loki("Kuittasi ennakkoilmoituksen jätetyksi", i_nro)
                st.rerun()
        elif on_admin and j2.button("↩️ Peru kuittaus", key="j_peru"):
            ik["ennakkoilmoitus_jatetty"] = ""
            tallenna_kohteet(kohteet)
            paivita_tila(i_nro)
            st.rerun()


# ── DOKUMENTOINTI (prompti 4, työnjohdon näkymä) ──────────────────────────────

with tab_dok:
    nayta_dokumentointi([k for k in kohteet if not k.get("raportti_lahetetty")] or kohteet)


# ── RAPORTTI (prompti 5) ──────────────────────────────────────────────────────

with tab_raportti:
    if not on_tj:
        st.info("Vain työnjohto voi koota ja lähettää raportteja.")
    elif not kohteet:
        st.info("Lisää ensin kohde.")
    else:
        r_nro = st.selectbox("Kohde", [f"{k['tyonumero']} — {k.get('osoite','')}" for k in kohteet],
                             key="r_nro").split(" — ")[0]
        rk = _hae_kohde(r_nro, kohteet)
        r_dok = lataa_dok(r_nro)
        r_liitteet = _liitteet(r_nro)
        r_slug = tiedosto_slug(r_nro)

        st.markdown(f"**Tila:** {_badge_html(rk.get('tila','uusi'))}", unsafe_allow_html=True)
        st.divider()

        # ── Liitteiden lataus ────────────────────────────────────────────────
        l1, l2 = st.columns(2)
        with l1:
            st.markdown("**🧪 Puhdastilamittaus (ilma-analyysivastaus)**")
            if _mittaus_ok(r_liitteet):
                st.success("✅ Ladattu: " + ", ".join(
                    Path(p).name for p in r_liitteet if "puhdastila" in p))
            mittaus_f = st.file_uploader("Ilma-analyysivastaus (PDF)", type=["pdf"],
                                         key=f"up_mittaus_{r_nro}")
            if mittaus_f and st.button("💾 Tallenna mittaus", key="tall_mittaus"):
                tallenna_tiedosto(f"{r_slug}/liitteet/puhdastila.pdf",
                                  mittaus_f.getvalue(), "application/pdf")
                paivita_tila(r_nro)
                _loki("Latasi puhdastilamittauksen", r_nro)
                st.rerun()
        with l2:
            st.markdown("**♻️ Jätteenkäsittelyasiakirja (Kuljetusringin siirtoasiakirja)**")
            if _jate_ok(r_liitteet):
                st.success("✅ Ladattu: " + ", ".join(
                    Path(p).name for p in r_liitteet if "jatetodistus" in p))
            jate_f = st.file_uploader("Siirtoasiakirja (PDF tai kuva)",
                                      type=["pdf", "jpg", "jpeg", "png"], key=f"up_jate_{r_nro}")
            if jate_f and st.button("💾 Tallenna jätetodistus", key="tall_jate"):
                paate = Path(jate_f.name).suffix.lower() or ".pdf"
                mime = "application/pdf" if paate == ".pdf" else "image/jpeg"
                data = jate_f.getvalue() if paate == ".pdf" else pakkaa_kuva(jate_f.getvalue())
                tallenna_tiedosto(f"{r_slug}/liitteet/jatetodistus{paate}", data, mime)
                paivita_tila(r_nro)
                _loki("Latasi jätetodistuksen", r_nro)
                st.rerun()

        st.divider()

        # ── Puutelista ───────────────────────────────────────────────────────
        puutteet = []
        for vaihe, avain in ALOITUS_KOHDAT:
            if vaihe in _aloitus_puuttuvat(r_dok):
                puutteet.append(f"aloituskuva: {tr(avain, 'fi')}")
        if _lopetus_kuvia(r_dok) == 0:
            puutteet.append("lopetuskuvat")
        if not r_dok.get("purku_kuitattu"):
            puutteet.append("purun valmistumiskuittaus (työntekijä)")
        if not _mittaus_ok(r_liitteet):
            puutteet.append("puhdastilamittauksen tulokset")
        if not _jate_ok(r_liitteet):
            puutteet.append("jätteenkäsittelyasiakirja")

        if puutteet:
            st.error("**Raporttia ei voi vielä koota — puuttuu:**\n\n" +
                     "\n".join(f"- {p}" for p in puutteet))
        else:
            st.success("✅ Kaikki dokumentointi koossa — raportti voidaan koota.")

            r_huomiot = st.text_area(
                "Huomiot asbestipurkutyön aloituksesta ja lähtötilanteesta",
                value=rk.get("raportti_huomiot",
                             f"Aloitus {_pvm_fi(rk.get('aloitus_pvm',''))} ja "
                             f"lopetus {_pvm_fi(rk.get('lopetus_pvm',''))}. "
                             + rk.get("kuvaus", "")),
                height=90, key="r_huomiot")

            if st.button("📑 Kokoa aloitus- ja lopetusraportti (PDF)", type="primary",
                         key="r_kokoa", use_container_width=True):
                rk["raportti_huomiot"] = r_huomiot
                tallenna_kohteet(kohteet)
                with st.spinner("Kootaan raporttia…"):
                    # Kuvat järjestyksessä: aloituskohdat → muut → lopetus
                    jarjestys = [v for v, _ in ALOITUS_KOHDAT]
                    def _avain(k):
                        v = k.get("vaihe", "")
                        return (jarjestys.index(v) if v in jarjestys
                                else 90 if v != "lopetus" else 99, k.get("aika", ""))
                    kuvat = []
                    for k in sorted(r_dok.get("kuvat", []), key=_avain):
                        data = lataa_tiedosto(k["polku"])
                        if not data:
                            continue
                        vaihe_nimi = tr(dict(ALOITUS_KOHDAT).get(k["vaihe"], "asb_lopetuskuvat"), "fi") \
                            if k["vaihe"] != "lopetus" else tr("asb_lopetuskuvat", "fi")
                        teksti = f"{vaihe_nimi}. {k.get('teksti','')}".strip(". ")
                        kuvat.append({"data": data, "teksti": teksti})
                    liite_datat = [lataa_tiedosto(p) for p in r_liitteet
                                   if "puhdastila" in p or "jatetodistus" in p]
                    osallistujat = [(rk.get("vastuuhenkilo", ""), DOK.YRITYS["nimi"])] + \
                                   [(t, DOK.YRITYS["nimi"]) for t in rk.get("tyontekijat", [])]
                    tiedot = {
                        "kohde_nimi": rk.get("kohde_nimi", rk.get("osoite", "")),
                        "tyonumero": r_nro,
                        "pvm": date.today().strftime("%-d.%-m.%Y"),
                        "osallistujat": osallistujat,
                        "aloitus_pvm": _pvm_fi(rk.get("aloitus_pvm", "")),
                        "lopetus_pvm": _pvm_fi(rk.get("lopetus_pvm", "")),
                        "urakoitsija_vastuu": rk.get("vastuuhenkilo", ""),
                        "paatoteuttaja": rk.get("tilaaja_yritys", ""),
                        "paatoteuttaja_vastuu": rk.get("tilaaja_yhteyshenkilo", ""),
                        "huomiot_aloitus": r_huomiot,
                        "havainnot": r_dok.get("havainnot", ""),
                    }
                    pdf = DOK.luo_aloitus_lopetusraportti(tiedot, kuvat, liite_datat)
                    tallenna_tiedosto(f"{r_slug}/dokumentit/aloitus_lopetusraportti.pdf",
                                      pdf, "application/pdf")
                    st.session_state[f"pdf_raportti_{r_nro}"] = pdf
                    _loki("Kokosi raportin", r_nro)

            pdf_valmis = st.session_state.get(f"pdf_raportti_{r_nro}")
            if pdf_valmis:
                st.info(f"Raportti koottu: {len(pdf_valmis)//1024} kt, "
                        f"{len(r_dok.get('kuvat', []))} kuvaa + liitteet. "
                        "Esikatsele lataamalla ennen lähetystä.")
                st.download_button("⬇️ Esikatsele / lataa raportti", data=pdf_valmis,
                                   file_name=f"asbestipurkutyon_aloitus_ja_lopetusraportti_{r_slug}.pdf",
                                   mime="application/pdf", use_container_width=True)

                st.markdown("#### 📧 Lähetys Catevalle")
                aihe = f"Asbestityön aloitus- ja lopetusraportti {r_nro} — {rk.get('osoite','')}"
                st.caption(f"Aihe: {aihe}")
                runko = st.text_area("Saateviesti", key="r_saate", value=(
                    f"Hei,\n\nliitteenä asbestityön aloitus- ja lopetusraportti.\n"
                    f"Työnumero: {r_nro}\nKohde: {rk.get('osoite','')}\n\n"
                    f"Terveisin\n{kayttaja.get('nimi','')}\n{DOK.YRITYS['nimi']}"))
                varmistus = st.checkbox("Olen esikatsellut raportin", key="r_varmistus")
                if st.button("📧 Lähetä Catevalle", type="primary",
                             disabled=not varmistus, key="r_laheta"):
                    ok, viesti = _laheta_email(
                        aihe, runko,
                        f"asbestipurkutyon_aloitus_ja_lopetusraportti_{r_slug}.pdf",
                        pdf_valmis)
                    if ok:
                        rk["raportti_lahetetty"] = date.today().isoformat()
                        rk["tila"] = "raportti_lahetetty"
                        tallenna_kohteet(kohteet)
                        _loki("Lähetti raportin Catevalle", f"{r_nro} — {viesti}")
                        st.success(f"✅ Raportti lähetetty. {viesti}")
                        st.rerun()
                    else:
                        st.error(viesti)


# ── LABROC-TULOKSET (prompti 6) ───────────────────────────────────────────────

with tab_labroc:
    if not on_tj:
        st.info("Vain työnjohto käsittelee laboratoriotuloksia.")
    else:
        st.caption("Hakee Labrocin tulossähköpostit (laboratorio.helsinki@labroc.fi) ja "
                   "kohdistaa puhdastilamittaukset kohteisiin työnumerolla tai osoitteella. "
                   "ASB_ilma = puhdastilamittaus; pelkkä ASB = materiaalinäyte (kartoitus).")

        labroc_conf = {}
        try:
            labroc_conf = dict(st.secrets["labroc_email"])
        except Exception:
            st.warning("Lisää Streamlit Secretsiin: [labroc_email] host (imap.gmail.com), "
                       "user, password (Gmailin sovellussalasana), kansio (valinnainen).")

        if labroc_conf and st.button("📥 Hae uudet tulokset", type="primary", key="lb_hae"):
            from labroc_nouto import hae_uudet_tulokset, parsi_labroc_pdf, kohdista_kohteeseen
            kasitellyt = set(lataa_globaali("labroc_kasitellyt") or [])
            with st.spinner("Haetaan postilaatikosta…"):
                try:
                    uudet = hae_uudet_tulokset(
                        labroc_conf.get("host", "imap.gmail.com"),
                        labroc_conf["user"], labroc_conf["password"],
                        labroc_conf.get("kansio", "INBOX"), ohita_idt=kasitellyt)
                except Exception as e:
                    uudet = []
                    st.error(f"IMAP-haku epäonnistui: {e}")
            rivit = []
            for t in uudet:
                p = parsi_labroc_pdf(t["data"])
                osuma = kohdista_kohteeseen(t, p, kohteet)
                rivit.append({**t, "parsittu": p,
                              "ehdotus": osuma["tyonumero"] if osuma else None})
            st.session_state["labroc_rivit"] = rivit
            _loki("Haki Labroc-tulokset", f"{len(rivit)} uutta")

        rivit = st.session_state.get("labroc_rivit", [])
        if rivit:
            st.markdown(f"**{len(rivit)} uutta tulosta:**")
            kohde_valinnat = ["— ei kohdisteta —"] + [k["tyonumero"] for k in kohteet]
            for idx, rivi in enumerate(rivit):
                p = rivi["parsittu"]
                tyyppi = "🧪 Puhdastilamittaus" if p["onko_ilma"] else "🔬 Materiaalinäyte"
                if p["onko_ilma"]:
                    merkki = {True: "🟢", False: "🔴", None: "🟠"}[p["tulos_ok"]]
                else:
                    merkki = "⚪"
                with st.container(border=True):
                    st.markdown(f"{merkki} **{rivi['tiedostonimi']}** — {tyyppi}  \n"
                                f"Kohde: {p['kohde'] or rivi['aihe_kohde']} · {p['tulos_teksti']}")
                    s1, s2, s3 = st.columns([2, 1, 1])
                    oletus = (kohde_valinnat.index(rivi["ehdotus"])
                              if rivi.get("ehdotus") in kohde_valinnat else 0)
                    valittu_kohde = s1.selectbox("Kohdista kohteeseen", kohde_valinnat,
                                                 index=oletus, key=f"lb_kohde_{idx}")
                    if s2.button("💾 Tallenna", key=f"lb_tall_{idx}",
                                 disabled=valittu_kohde == kohde_valinnat[0]):
                        slug = tiedosto_slug(valittu_kohde)
                        etunimi = "puhdastila" if p["onko_ilma"] else "labroc_materiaali"
                        pdf_nimi = f"{slug}/liitteet/{etunimi}_{p['projektinro'] or idx}.pdf"
                        # Puhdastilamittaus tallennetaan raportin odottamalla nimellä
                        if p["onko_ilma"] and p["tulos_ok"]:
                            pdf_nimi = f"{slug}/liitteet/puhdastila.pdf"
                        tallenna_tiedosto(pdf_nimi, rivi["data"], "application/pdf")
                        kasitellyt = lataa_globaali("labroc_kasitellyt") or []
                        kasitellyt.append(rivi["viesti_id"])
                        tallenna_globaali("labroc_kasitellyt", kasitellyt)
                        paivita_tila(valittu_kohde)
                        _loki("Kohdisti Labroc-tuloksen",
                              f"{rivi['tiedostonimi']} → {valittu_kohde}")
                        rivit.pop(idx)
                        st.session_state["labroc_rivit"] = rivit
                        st.rerun()
                    if s3.button("🚫 Ohita", key=f"lb_ohita_{idx}"):
                        kasitellyt = lataa_globaali("labroc_kasitellyt") or []
                        kasitellyt.append(rivi["viesti_id"])
                        tallenna_globaali("labroc_kasitellyt", kasitellyt)
                        rivit.pop(idx)
                        st.session_state["labroc_rivit"] = rivit
                        st.rerun()
        elif labroc_conf:
            st.info("Paina *Hae uudet tulokset*. Käsin lataus onnistuu aina myös "
                    "Raportti-välilehdellä (esim. LAB-ACE:n tulokset).")


# ── PÄTEVYYDET (prompti 3) ────────────────────────────────────────────────────

with tab_patevyydet:
    if not on_tj:
        st.info("Vain työnjohto hallinnoi pätevyysrekisteriä.")
    else:
        st.caption("Ennakkoilmoituksen työntekijätiedot haetaan tästä rekisteristä. "
                   "Vanhenevista pätevyyksistä varoitetaan Kohteet-välilehdellä (alle 60 vrk).")
        for v in _patevyys_varoitukset(patevyydet):
            st.error(v) if v.startswith("🔴") else st.warning(v)

        if patevyydet:
            st.dataframe(pd.DataFrame([{
                "Nimi": p.get("nimi", ""),
                "Työnantaja": p.get("tyonantaja", ""),
                "Terveystarkastus": _pvm_fi(p.get("terveystarkastus_pvm", "")),
                "Voimassa": _pvm_fi(p.get("terveystarkastus_voimassa", "")),
                "Tiiviystestaus": _pvm_fi(p.get("tiiviystestaus_pvm", "")),
                "Koulutustodistus": _pvm_fi(p.get("koulutus_pvm", "")),
                "Rekisterissä": "✅" if p.get("rekisterissa") else "❌",
            } for p in patevyydet]), use_container_width=True, hide_index=True)

        nimet = [p.get("nimi", "") for p in patevyydet]
        with st.expander("➕ Lisää tai päivitä työntekijän pätevyydet",
                         expanded=not patevyydet):
            muokattava = st.selectbox("Työntekijä", ["— uusi —"] + nimet, key="p_valinta")
            pohja = next((p for p in patevyydet if p.get("nimi") == muokattava), {})

            def _pvm(avain):
                try:
                    return date.fromisoformat(pohja.get(avain, ""))
                except Exception:
                    return None
            p1, p2 = st.columns(2)
            p_nimi = p1.text_input("Nimi *", value=pohja.get("nimi", ""), key="p_nimi")
            p_tyonantaja = p1.text_input("Työnantaja",
                                         value=pohja.get("tyonantaja", DOK.YRITYS["nimi"]),
                                         key="p_tyonantaja")
            p_terveys = p1.date_input("Terveystarkastus suoritettu", value=_pvm("terveystarkastus_pvm"),
                                      key="p_terveys", format="DD.MM.YYYY")
            p_voimassa = p1.date_input("Terveystarkastus voimassa (asti)",
                                       value=_pvm("terveystarkastus_voimassa"),
                                       key="p_voimassa", format="DD.MM.YYYY")
            p_tiiviys = p2.date_input("Hengityksensuojaimen tiiviystestaus",
                                      value=_pvm("tiiviystestaus_pvm"),
                                      key="p_tiiviys", format="DD.MM.YYYY")
            p_koulutus = p2.date_input("Todistus erityisestä opetuksesta",
                                       value=_pvm("koulutus_pvm"),
                                       key="p_koulutus", format="DD.MM.YYYY")
            p_rek = p2.checkbox("Asbestipurkutyöhön pätevien henkilöiden rekisterissä",
                                value=pohja.get("rekisterissa", True), key="p_rek")

            b1, b2 = st.columns(2)
            if b1.button("💾 Tallenna", type="primary", key="p_tallenna"):
                if not p_nimi.strip():
                    st.error("Nimi vaaditaan.")
                else:
                    uusi = {
                        "nimi": p_nimi.strip(), "tyonantaja": p_tyonantaja.strip(),
                        "terveystarkastus_pvm": p_terveys.isoformat() if p_terveys else "",
                        "terveystarkastus_voimassa": p_voimassa.isoformat() if p_voimassa else "",
                        "tiiviystestaus_pvm": p_tiiviys.isoformat() if p_tiiviys else "",
                        "koulutus_pvm": p_koulutus.isoformat() if p_koulutus else "",
                        "rekisterissa": p_rek,
                    }
                    patevyydet = [p for p in patevyydet if p.get("nimi") != muokattava]
                    patevyydet.append(uusi)
                    tallenna_patevyydet(patevyydet)
                    _loki("Päivitti pätevyydet", p_nimi)
                    st.success("Tallennettu.")
                    st.rerun()
            if muokattava != "— uusi —" and b2.button("🗑️ Poista", key="p_poista"):
                tallenna_patevyydet([p for p in patevyydet if p.get("nimi") != muokattava])
                _loki("Poisti pätevyydet", muokattava)
                st.rerun()


# ── KÄYTTÄJÄT (vain admin) ────────────────────────────────────────────────────

if tab_kayttajat is not None:
    with tab_kayttajat:
        A.nayta_kayttajahallinta()
        st.divider()
        if hasattr(A, "nayta_loki"):
            A.nayta_loki()
