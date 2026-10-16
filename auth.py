"""
Käyttäjähallinta ja roolitukset — yhteinen tuntikirjalle ja kalustoseurannalle.

Roolit:
  admin       — hallitsee käyttäjiä, näkee kaiken
  tyonjohtaja — hyväksyy tunnit, luo projekteja, näkee kustannukset ja kaluston
  tyontekija  — kirjaa omat tuntinsa, näkee omat projektinsa
  katselija   — näkee raportit, ei muokkaa

Salasanat tallennetaan PBKDF2-HMAC-SHA256-hashattuna (100k kierrosta, satunnainen suola).
Käyttäjät tallennetaan storage-modulin globaaliin "kayttajat"-avaimeen.
"""

import hashlib
import hmac
import os
import time
from datetime import datetime
import streamlit as st

from storage import lataa_globaali, tallenna_globaali

ROOLIT = {
    "admin":       {"nimi": "Pääkäyttäjä",   "jarjestys": 0},
    "tyonjohtaja": {"nimi": "Työnjohtaja",   "jarjestys": 1},
    "tyontekija":  {"nimi": "Työntekijä",    "jarjestys": 2},
    "katselija":   {"nimi": "Katselija",     "jarjestys": 3},
}

MIN_SALASANA = 8             # merkkiä — koskee uusia ja vaihdettuja salasanoja
MAX_YRITYKSET = 5            # epäonnistunutta kirjautumista ...
LUKITUS_MIN = 15             # ... johtaa tunnuksen lukitukseen näin moneksi minuutiksi
ISTUNNON_TARKISTUS_S = 30    # kuinka usein avoimen istunnon käyttäjätiedot tarkistetaan rekisteristä
VIRHE_KIRJAUTUMINEN = "Väärä käyttäjätunnus tai salasana."

# Oikeudet rooleittain
def voi_hallita_kayttajia(rooli: str) -> bool:
    return rooli == "admin"

def voi_hyvaksya(rooli: str) -> bool:
    return rooli in ("admin", "tyonjohtaja")

def voi_muokata_tunteja(rooli: str) -> bool:
    return rooli in ("admin", "tyonjohtaja", "tyontekija")

def voi_hallita_projekteja(rooli: str) -> bool:
    return rooli in ("admin", "tyonjohtaja")

def nakee_kaikki_projektit(rooli: str) -> bool:
    return rooli in ("admin", "tyonjohtaja", "katselija")


# ── Salasanan hashays ──────────────────────────────────────────────────────────

def _hash(salasana: str, suola: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", salasana.encode("utf-8"), bytes.fromhex(suola), 100_000
    ).hex()

def _luo_suola() -> str:
    return os.urandom(16).hex()

_TYHJA_SUOLA = "00" * 16

def tarkista_salasana(salasana: str, kayttaja: dict) -> bool:
    if not kayttaja:
        # Lasketaan hash silti, ettei vastausaika paljasta onko tunnus olemassa
        _hash(salasana, _TYHJA_SUOLA)
        return False
    return hmac.compare_digest(_hash(salasana, kayttaja.get("suola", "")), kayttaja.get("hash", ""))


def _salasanavirhe(salasana: str) -> str:
    """Palauttaa virheviestin tai tyhjän jos salasana kelpaa."""
    if len(salasana or "") < MIN_SALASANA:
        return f"Salasanan oltava vähintään {MIN_SALASANA} merkkiä."
    return ""


def _jaisi_ilman_adminia(kayttajat: list, tunnus: str, rooli: str, aktiivinen: bool) -> bool:
    """True jos muutos poistaisi viimeisen aktiivisen pääkäyttäjän."""
    muut = [k for k in kayttajat if k["tunnus"] != tunnus
            and k.get("rooli") == "admin" and k.get("aktiivinen", True)]
    return not muut and not (rooli == "admin" and aktiivinen)


# ── Kirjautumisyritysten rajoitus (globaali, ei istuntokohtainen) ──────────────

def _lataa_yritykset() -> dict:
    raja = time.time() - 24 * 3600   # vanhat merkinnät karsitaan
    return {r["tunnus"]: r for r in lataa_globaali("kirjautumisyritykset")
            if r.get("viimeisin", 0) > raja}

def _tallenna_yritykset(yritykset: dict):
    tallenna_globaali("kirjautumisyritykset", list(yritykset.values()))

def lukittu_asti(tunnus: str) -> float:
    """Palauttaa lukituksen päättymisajan (epoch) tai 0 jos tunnus ei ole lukittu."""
    r = _lataa_yritykset().get(tunnus.strip().lower(), {})
    return r.get("lukittu_asti", 0) if r.get("lukittu_asti", 0) > time.time() else 0

def _kirjaa_epaonnistunut(tunnus: str) -> bool:
    """Kirjaa epäonnistuneen yrityksen. Palauttaa True jos tunnus lukittiin nyt."""
    tunnus = tunnus.strip().lower()
    yritykset = _lataa_yritykset()
    nyt = time.time()
    r = yritykset.get(tunnus, {"tunnus": tunnus, "lkm": 0})
    if nyt - r.get("viimeisin", 0) > LUKITUS_MIN * 60:
        r["lkm"] = 0                  # edellisestä yrityksestä kauan → laskuri alusta
    r["lkm"] += 1
    r["viimeisin"] = nyt
    lukittiin = r["lkm"] >= MAX_YRITYKSET
    if lukittiin:
        r["lukittu_asti"] = nyt + LUKITUS_MIN * 60
        r["lkm"] = 0
    yritykset[tunnus] = r
    _tallenna_yritykset(yritykset)
    return lukittiin

def _nollaa_yritykset(tunnus: str):
    yritykset = _lataa_yritykset()
    if yritykset.pop(tunnus.strip().lower(), None) is not None:
        _tallenna_yritykset(yritykset)


# ── Käyttäjärekisteri ──────────────────────────────────────────────────────────

def lataa_kayttajat() -> list:
    return lataa_globaali("kayttajat")

def tallenna_kayttajat(kayttajat: list):
    tallenna_globaali("kayttajat", kayttajat)

def hae_kayttaja(tunnus: str) -> dict:
    tunnus = tunnus.strip().lower()
    return next((k for k in lataa_kayttajat() if k["tunnus"] == tunnus), {})

def luo_kayttaja(tunnus: str, nimi: str, salasana: str, rooli: str,
                 projektit: list = None) -> tuple:
    """Palauttaa (onnistui, viesti)."""
    tunnus = tunnus.strip().lower()
    if not tunnus or not salasana:
        return False, "Tunnus ja salasana vaaditaan."
    if _salasanavirhe(salasana):
        return False, _salasanavirhe(salasana)
    if rooli not in ROOLIT:
        return False, "Tuntematon rooli."
    kayttajat = lataa_kayttajat()
    if any(k["tunnus"] == tunnus for k in kayttajat):
        return False, f"Tunnus '{tunnus}' on jo käytössä."
    suola = _luo_suola()
    kayttajat.append({
        "tunnus":    tunnus,
        "nimi":      nimi or tunnus,
        "rooli":     rooli,
        "suola":     suola,
        "hash":      _hash(salasana, suola),
        "projektit": projektit or [],
        "aktiivinen": True,
    })
    tallenna_kayttajat(kayttajat)
    return True, f"Käyttäjä '{tunnus}' luotu."

def paivita_kayttaja(tunnus: str, **muutokset) -> tuple:
    """Palauttaa (onnistui, viesti)."""
    kayttajat = lataa_kayttajat()
    for k in kayttajat:
        if k["tunnus"] == tunnus:
            if muutokset.get("salasana") and _salasanavirhe(muutokset["salasana"]):
                return False, _salasanavirhe(muutokset["salasana"])
            if _jaisi_ilman_adminia(kayttajat, tunnus,
                                    muutokset.get("rooli", k.get("rooli")),
                                    muutokset.get("aktiivinen", k.get("aktiivinen", True))):
                return False, "Vähintään yksi aktiivinen pääkäyttäjä vaaditaan."
            if "salasana" in muutokset and muutokset["salasana"]:
                k["suola"] = _luo_suola()
                k["hash"]  = _hash(muutokset.pop("salasana"), k["suola"])
            else:
                muutokset.pop("salasana", None)
            k.update(muutokset)
            tallenna_kayttajat(kayttajat)
            return True, "Tallennettu."
    return False, "Käyttäjää ei löydy."

def poista_kayttaja(tunnus: str) -> bool:
    kayttajat = lataa_kayttajat()
    uudet = [k for k in kayttajat if k["tunnus"] != tunnus]
    if len(uudet) != len(kayttajat):
        tallenna_kayttajat(uudet)
        return True
    return False


# ── Kirjautuminen (käytetään sovelluksen alussa) ───────────────────────────────

def kirjaudu_gate(sovellus_nimi: str = "Työmaaseuranta") -> dict:
    """
    Näyttää kirjautumissivun ja palauttaa kirjautuneen käyttäjän dictin.
    Pysäyttää sovelluksen jos ei kirjautunut.
    """
    if st.session_state.get("kayttaja"):
        # Tarkista määräajoin, että tunnus on yhä voimassa ja rooli ajan tasalla —
        # käytöstä poisto tai roolin muutos vaikuttaa myös jo kirjautuneeseen.
        if time.time() - st.session_state.get("_kayttaja_tarkistettu", 0) < ISTUNNON_TARKISTUS_S:
            return st.session_state["kayttaja"]
        k = hae_kayttaja(st.session_state["kayttaja"].get("tunnus", ""))
        if k and k.get("aktiivinen", True):
            st.session_state["kayttaja"] = {kk: vv for kk, vv in k.items() if kk not in ("hash", "suola")}
            st.session_state["_kayttaja_tarkistettu"] = time.time()
            return st.session_state["kayttaja"]
        kirjaudu_ulos()
        st.warning("Istunto päättyi: käyttäjätunnus on poistettu käytöstä. Kirjaudu uudelleen.")

    kayttajat = lataa_kayttajat()

    # Lukuvirhe ≠ tyhjä rekisteri: älä tarjoa alkuasennusta, ettei uusi admin korvaa rekisteriä
    from storage import lukuvirhe
    if not kayttajat and lukuvirhe("kayttajat"):
        st.title(f"🔒 {sovellus_nimi}")
        st.error("Käyttäjärekisteriä ei saatu luettua — tietokantayhteys ei toimi juuri nyt. "
                 "Kirjautuminen ei ole mahdollista. Yritä hetken päästä uudelleen; jos vika "
                 "jatkuu, ilmoita pääkäyttäjälle.")
        if st.button("🔄 Yritä uudelleen"):
            st.rerun()
        st.stop()

    # ── Ensikäynnistys: luo pääkäyttäjä jos rekisteri tyhjä ────────────────
    if not kayttajat:
        st.title(f"🔧 {sovellus_nimi} — alkuasennus")
        try:
            from storage import tallennustila
            if tallennustila() != "pilvi":
                st.error("⚠️ TALLENNUS EI OLE PILVESSÄ! Tämän sovelluksen Streamlit "
                         "Secretsistä puuttuu toimiva [supabase]-osio (secret-avain). "
                         "Jos luot käyttäjän nyt, se KATOAA uudelleenkäynnistyksessä. "
                         "Korjaa secrets ensin.")
        except Exception:
            pass
        st.info("Ei käyttäjiä vielä. Luo ensimmäinen pääkäyttäjä (admin).")
        with st.form("luo_admin"):
            a_tunnus = st.text_input("Käyttäjätunnus", placeholder="esim. etunimi.sukunimi")
            a_nimi   = st.text_input("Koko nimi", placeholder="Etunimi Sukunimi")
            a_pw1    = st.text_input("Salasana", type="password")
            a_pw2    = st.text_input("Salasana uudelleen", type="password")
            if st.form_submit_button("Luo pääkäyttäjä", type="primary"):
                if a_pw1 != a_pw2:
                    st.error("Salasanat eivät täsmää.")
                elif _salasanavirhe(a_pw1):
                    st.error(_salasanavirhe(a_pw1))
                else:
                    ok, viesti = luo_kayttaja(a_tunnus, a_nimi, a_pw1, "admin")
                    # Varmista että tallennus meni perille (lue takaisin)
                    if ok and hae_kayttaja(a_tunnus):
                        st.success(viesti + " Kirjaudu nyt sisään.")
                        st.rerun()
                    else:
                        virhe = st.session_state.get("_sb_virhe", "")
                        st.error("Pääkäyttäjän tallennus epäonnistui. "
                                 + (f"Syy: {virhe}" if virhe else viesti))
                        st.info("Todennäköinen syy: Supabasen RLS estää kirjoituksen. "
                                "Aja Supabasen SQL Editorissa:\n\n"
                                "ALTER TABLE globaali_data DISABLE ROW LEVEL SECURITY;\n"
                                "ALTER TABLE projekti_data DISABLE ROW LEVEL SECURITY;")
        st.stop()

    # ── Normaali kirjautuminen ─────────────────────────────────────────────
    st.title(f"🔒 {sovellus_nimi}")
    st.caption("Kirjaudu sisään")
    with st.form("kirjautuminen"):
        tunnus = st.text_input("Käyttäjätunnus", placeholder="esim. etunimi.sukunimi")
        pw     = st.text_input("Salasana", type="password")
        if st.form_submit_button("Kirjaudu", type="primary"):
            tunnus = tunnus.strip().lower()
            lukko = lukittu_asti(tunnus)
            k = hae_kayttaja(tunnus)
            # Sama virheviesti kaikissa tapauksissa → tunnuksia ei voi arvata
            if lukko:
                klo = datetime.fromtimestamp(lukko).strftime("%H:%M")
                st.error(f"Liian monta epäonnistunutta yritystä. Yritä uudelleen klo {klo} "
                         "tai pyydä pääkäyttäjää avaamaan lukitus.")
            elif tarkista_salasana(pw, k) and k.get("aktiivinen", True):
                _nollaa_yritykset(tunnus)
                # Älä tallenna hashia session_stateen
                julkinen = {kk: vv for kk, vv in k.items() if kk not in ("hash", "suola")}
                st.session_state["kayttaja"] = julkinen
                st.session_state["_kayttaja_tarkistettu"] = time.time()
                try:
                    from loki import kirjaa
                    kirjaa(julkinen, sovellus_nimi, "Kirjautui sisään")
                except Exception:
                    pass
                st.rerun()
            else:
                lukittiin = _kirjaa_epaonnistunut(tunnus)
                time.sleep(1)   # hidastaa arvailua
                if lukittiin:
                    try:
                        from loki import kirjaa
                        kirjaa({"tunnus": tunnus, "rooli": "—"}, sovellus_nimi,
                               f"Tunnus lukittu {LUKITUS_MIN} min (liikaa vääriä salasanoja)")
                    except Exception:
                        pass
                    st.error(f"Liian monta epäonnistunutta yritystä — tunnus lukittu {LUKITUS_MIN} minuutiksi.")
                else:
                    st.error(VIRHE_KIRJAUTUMINEN)
    st.stop()


def kirjaudu_ulos():
    for avain in ("kayttaja", "_kayttaja_tarkistettu"):
        st.session_state.pop(avain, None)


# ── Käyttäjähallinnan UI (vain admin) ──────────────────────────────────────────

def _loki(toiminto: str, kohde: str = ""):
    """Kirjaa käyttäjähallinnan tapahtuman lokiin (turvallinen)."""
    try:
        from loki import kirjaa
        kirjaa(st.session_state.get("kayttaja", {}), "Käyttäjähallinta", toiminto, kohde)
    except Exception:
        pass


def nayta_loki():
    """Toimintaloki — vain admin."""
    st.subheader("📜 Toimintaloki")
    try:
        from loki import hae
        import pandas as pd
        rivit = hae(500)
        if not rivit:
            st.info("Ei lokitapahtumia (tai loki-taulua ei ole vielä luotu Supabaseen).")
            return
        df = pd.DataFrame(rivit)
        sarakkeet = [c for c in ["aika","kayttaja","rooli","sovellus","toiminto","kohde"] if c in df.columns]
        df = df[sarakkeet]
        # Suodattimet
        c1, c2 = st.columns(2)
        if "kayttaja" in df.columns:
            k = c1.multiselect("Käyttäjä", sorted(df["kayttaja"].dropna().unique()))
            if k:
                df = df[df["kayttaja"].isin(k)]
        if "sovellus" in df.columns:
            s = c2.multiselect("Sovellus", sorted(df["sovellus"].dropna().unique()))
            if s:
                df = df[df["sovellus"].isin(s)]
        st.dataframe(df, width="stretch", hide_index=True)
        st.caption(f"{len(df)} tapahtumaa (uusimmat ensin, max 500)")
    except Exception as e:
        st.info(f"Lokia ei voitu ladata: {e}")


def nayta_kayttajahallinta():
    st.subheader("👤 Käyttäjähallinta")
    try:
        from storage import tallennustila
        if tallennustila() == "pilvi":
            st.caption("💾 Tallennus: ☁️ Supabase (säilyy)")
        else:
            st.error("⚠️ Tallennus: PAIKALLINEN — data katoaa uudelleenkäynnistyksessä! "
                     "Lisää [supabase]-secret tähän sovellukseen.")
    except Exception:
        pass
    kayttajat = lataa_kayttajat()

    # Lista
    import pandas as pd
    if kayttajat:
        taul = [{
            "Tunnus": k["tunnus"],
            "Nimi": k.get("nimi",""),
            "Rooli": ROOLIT.get(k["rooli"], {}).get("nimi", k["rooli"]),
            "Projektit": ", ".join(k.get("projektit", [])) or "kaikki",
            "Tila": "✅" if k.get("aktiivinen", True) else "⛔",
        } for k in kayttajat]
        st.dataframe(pd.DataFrame(taul), width="stretch", hide_index=True)

    # Lukitut tunnukset (liikaa vääriä salasanoja)
    lukitut = [r for r in _lataa_yritykset().values() if r.get("lukittu_asti", 0) > time.time()]
    if lukitut:
        st.warning("🔒 Lukitut tunnukset: " + ", ".join(
            f"{r['tunnus']} (klo {datetime.fromtimestamp(r['lukittu_asti']).strftime('%H:%M')} asti)"
            for r in lukitut))
        avattava = st.selectbox("Avaa lukitus", [r["tunnus"] for r in lukitut], key="avaa_lukko")
        if st.button("🔓 Avaa lukitus", key="avaa_lukko_btn"):
            _nollaa_yritykset(avattava)
            _loki("Avasi tunnuksen lukituksen", avattava)
            st.rerun()

    # Uusi käyttäjä
    with st.expander("➕ Lisää käyttäjä", expanded=len(kayttajat) <= 1):
        c1, c2 = st.columns(2)
        u_tunnus = c1.text_input("Käyttäjätunnus", placeholder="esim. etunimi.sukunimi", key="uk_tunnus")
        u_nimi   = c1.text_input("Koko nimi", placeholder="Etunimi Sukunimi", key="uk_nimi")
        u_rooli  = c2.selectbox("Rooli",
                    options=list(ROOLIT.keys()),
                    format_func=lambda r: ROOLIT[r]["nimi"], key="uk_rooli")
        u_pw     = c2.text_input(f"Salasana (väh. {MIN_SALASANA} merkkiä)", type="password", key="uk_pw")

        # Projektirajaus työntekijälle
        u_projektit = []
        if u_rooli == "tyontekija":
            from storage import lataa_projektirekisteri
            proj_nimet = [p["nimi"] for p in lataa_projektirekisteri()]
            u_projektit = st.multiselect("Sallitut projektit (tyhjä = kaikki)",
                                          proj_nimet, key="uk_proj")
        if st.button("Luo käyttäjä", type="primary", key="uk_luo"):
            ok, viesti = luo_kayttaja(u_tunnus, u_nimi, u_pw, u_rooli, u_projektit)
            if ok:
                st.success(viesti)
            else:
                st.error(viesti)
            if ok:
                _loki("Loi käyttäjän", f"{u_tunnus} ({u_rooli})")
                st.rerun()

    # Muokkaa / poista
    if len(kayttajat) > 0:
        with st.expander("✏️ Muokkaa tai poista käyttäjä"):
            valittu = st.selectbox("Käyttäjä", [k["tunnus"] for k in kayttajat], key="muok_k")
            kobj = next((k for k in kayttajat if k["tunnus"] == valittu), {})
            m1, m2 = st.columns(2)
            m_nimi  = m1.text_input("Nimi", value=kobj.get("nimi",""), key="mk_nimi")
            m_rooli = m1.selectbox("Rooli", list(ROOLIT.keys()),
                       index=list(ROOLIT.keys()).index(kobj.get("rooli","tyontekija")),
                       format_func=lambda r: ROOLIT[r]["nimi"], key="mk_rooli")
            m_aktiivinen = m2.checkbox("Aktiivinen", value=kobj.get("aktiivinen", True), key="mk_akt")
            m_pw    = m2.text_input(f"Uusi salasana (tyhjä = ennallaan, väh. {MIN_SALASANA} merkkiä)",
                                    type="password", key="mk_pw")

            b1, b2 = st.columns(2)
            # Estä oman tai viimeisen adminin poisto/passivointi
            adminit = [k for k in kayttajat if k["rooli"] == "admin" and k.get("aktiivinen", True)]
            oma_tunnus = st.session_state.get("kayttaja", {}).get("tunnus")
            if b1.button("💾 Tallenna muutokset", type="primary", key="mk_tall"):
                if valittu == oma_tunnus and not m_aktiivinen:
                    st.error("Et voi poistaa omaa tunnustasi käytöstä.")
                else:
                    ok, viesti = paivita_kayttaja(valittu, nimi=m_nimi, rooli=m_rooli,
                                                  aktiivinen=m_aktiivinen, salasana=m_pw)
                    if ok:
                        muutos = "salasana vaihdettu" if m_pw else f"rooli={m_rooli}, aktiivinen={m_aktiivinen}"
                        _loki("Muokkasi käyttäjää", f"{valittu} ({muutos})")
                        st.success(viesti)
                        st.rerun()
                    else:
                        st.error(viesti)
            if b2.button("🗑️ Poista käyttäjä", type="secondary", key="mk_poista"):
                if valittu == oma_tunnus:
                    st.error("Et voi poistaa itseäsi.")
                elif kobj.get("rooli") == "admin" and len(adminit) <= 1:
                    st.error("Vähintään yksi pääkäyttäjä vaaditaan.")
                else:
                    poista_kayttaja(valittu)
                    _loki("Poisti käyttäjän", valittu)
                    st.success("Poistettu.")
                    st.rerun()
