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
import os
import streamlit as st

from storage import lataa_globaali, tallenna_globaali

ROOLIT = {
    "admin":       {"nimi": "Pääkäyttäjä",   "jarjestys": 0},
    "tyonjohtaja": {"nimi": "Työnjohtaja",   "jarjestys": 1},
    "tyontekija":  {"nimi": "Työntekijä",    "jarjestys": 2},
    "katselija":   {"nimi": "Katselija",     "jarjestys": 3},
}

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

def tarkista_salasana(salasana: str, kayttaja: dict) -> bool:
    if not kayttaja:
        return False
    return _hash(salasana, kayttaja.get("suola", "")) == kayttaja.get("hash", "")


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

def paivita_kayttaja(tunnus: str, **muutokset) -> bool:
    kayttajat = lataa_kayttajat()
    for k in kayttajat:
        if k["tunnus"] == tunnus:
            if "salasana" in muutokset and muutokset["salasana"]:
                k["suola"] = _luo_suola()
                k["hash"]  = _hash(muutokset.pop("salasana"), k["suola"])
            else:
                muutokset.pop("salasana", None)
            k.update(muutokset)
            tallenna_kayttajat(kayttajat)
            return True
    return False

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
        return st.session_state["kayttaja"]

    kayttajat = lataa_kayttajat()

    # ── Ensikäynnistys: luo pääkäyttäjä jos rekisteri tyhjä ────────────────
    if not kayttajat:
        st.title(f"🔧 {sovellus_nimi} — alkuasennus")
        st.info("Ei käyttäjiä vielä. Luo ensimmäinen pääkäyttäjä (admin).")
        with st.form("luo_admin"):
            a_tunnus = st.text_input("Käyttäjätunnus", placeholder="esim. sakari")
            a_nimi   = st.text_input("Koko nimi", placeholder="Sakari Teljomaa")
            a_pw1    = st.text_input("Salasana", type="password")
            a_pw2    = st.text_input("Salasana uudelleen", type="password")
            if st.form_submit_button("Luo pääkäyttäjä", type="primary"):
                if a_pw1 != a_pw2:
                    st.error("Salasanat eivät täsmää.")
                elif len(a_pw1) < 6:
                    st.error("Salasanan oltava vähintään 6 merkkiä.")
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
        tunnus = st.text_input("Käyttäjätunnus")
        pw     = st.text_input("Salasana", type="password")
        if st.form_submit_button("Kirjaudu", type="primary"):
            k = hae_kayttaja(tunnus)
            if not k or not k.get("aktiivinen", True):
                st.error("Tunnusta ei löydy tai se on poistettu käytöstä.")
            elif tarkista_salasana(pw, k):
                # Älä tallenna hashia session_stateen
                julkinen = {kk: vv for kk, vv in k.items() if kk not in ("hash", "suola")}
                st.session_state["kayttaja"] = julkinen
                try:
                    from loki import kirjaa
                    kirjaa(julkinen, sovellus_nimi, "Kirjautui sisään")
                except Exception:
                    pass
                st.rerun()
            else:
                st.error("Väärä salasana.")
    st.stop()


def kirjaudu_ulos():
    for avain in ("kayttaja",):
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
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{len(df)} tapahtumaa (uusimmat ensin, max 500)")
    except Exception as e:
        st.info(f"Lokia ei voitu ladata: {e}")


def nayta_kayttajahallinta():
    st.subheader("👤 Käyttäjähallinta")
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
        st.dataframe(pd.DataFrame(taul), use_container_width=True, hide_index=True)

    # Uusi käyttäjä
    with st.expander("➕ Lisää käyttäjä", expanded=len(kayttajat) <= 1):
        c1, c2 = st.columns(2)
        u_tunnus = c1.text_input("Käyttäjätunnus", key="uk_tunnus")
        u_nimi   = c1.text_input("Koko nimi", key="uk_nimi")
        u_rooli  = c2.selectbox("Rooli",
                    options=list(ROOLIT.keys()),
                    format_func=lambda r: ROOLIT[r]["nimi"], key="uk_rooli")
        u_pw     = c2.text_input("Salasana", type="password", key="uk_pw")

        # Projektirajaus työntekijälle
        u_projektit = []
        if u_rooli == "tyontekija":
            from storage import lataa_projektirekisteri
            proj_nimet = [p["nimi"] for p in lataa_projektirekisteri()]
            u_projektit = st.multiselect("Sallitut projektit (tyhjä = kaikki)",
                                          proj_nimet, key="uk_proj")
        if st.button("Luo käyttäjä", type="primary", key="uk_luo"):
            ok, viesti = luo_kayttaja(u_tunnus, u_nimi, u_pw, u_rooli, u_projektit)
            st.success(viesti) if ok else st.error(viesti)
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
            m_pw    = m2.text_input("Uusi salasana (tyhjä = ennallaan)", type="password", key="mk_pw")

            b1, b2 = st.columns(2)
            if b1.button("💾 Tallenna muutokset", type="primary", key="mk_tall"):
                paivita_kayttaja(valittu, nimi=m_nimi, rooli=m_rooli,
                                 aktiivinen=m_aktiivinen, salasana=m_pw)
                muutos = "salasana vaihdettu" if m_pw else f"rooli={m_rooli}, aktiivinen={m_aktiivinen}"
                _loki("Muokkasi käyttäjää", f"{valittu} ({muutos})")
                st.success("Tallennettu.")
                st.rerun()
            # Estä oman tai viimeisen adminin poisto
            adminit = [k for k in kayttajat if k["rooli"] == "admin" and k.get("aktiivinen", True)]
            oma_tunnus = st.session_state.get("kayttaja", {}).get("tunnus")
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
