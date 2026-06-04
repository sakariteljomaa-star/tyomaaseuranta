"""
Lukee Netvisor myyntireskontra-XLSX:n ja palauttaa siistin DataFramen.
Käyttää sarakkeiden nimiä indeksien sijaan — toimii eri Netvisor-vientiversioilla.
"""

import pandas as pd
from datetime import date


def _luokittele_kategoria(teksti: str) -> str:
    t = teksti.lower() if isinstance(teksti, str) else ""
    if any(s in t for s in ["tuntityöt", "lisätyö", "tuntitöt", "viikko", "vko"]):
        return "Lisätyö"
    if "urakka" in t:
        return "Urakka"
    return "Muu"


def _tila_badge(tila: str, erapaiva) -> str:
    if isinstance(tila, str) and tila.lower() == "maksettu":
        return "✅ Maksettu"
    if isinstance(tila, str) and tila.lower() == "lähettämätön":
        return "📝 Lähettämätön"
    if pd.notna(erapaiva):
        try:
            if pd.to_datetime(erapaiva).date() < date.today():
                return "⚠️ Erääntynyt"
        except Exception:
            pass
    return "🔵 Avoin"


# Sarakkeiden tunnistus nimien perusteella (osittainen vastaavuus)
_SARAKE_HAKU = {
    "lasku_nro":      ["laskunumero"],
    "lasku_pvm":      ["laskupäivä"],
    "toimitus_pvm":   ["toimituspäivä"],
    "erapaiva":       ["eräpäivä"],
    "veroton_summa":  ["veroton summa"],
    "avoimena":       ["avoimena"],
    "vapaa_teksti":   ["vapaa teksti ennen"],
    "maksu_pvm":      ["maksupäivä"],
    "asiakas":        ["asiakas"],
    "tosite":         ["tosite"],
    "tila":           ["tila"],  # täsmähaulla, ei osittaisella
}

# Sarakkeet jotka vaativat täsmähaun (ei osittaista) erottaakseen esim. "Tila" vs "Perinnän tila"
_TARKKAHAKU = {"tila", "tosite", "asiakas"}


def _etsi_sarake(otsikot: list, vaihtoehdot: list, tarkka: bool = False):
    """Palauttaa ensimmäisen sarakeindeksin jonka otsikko vastaa jotain vaihtoehtoa."""
    for i, ot in enumerate(otsikot):
        ot_lower = str(ot).lower().strip()
        for v in vaihtoehdot:
            if tarkka:
                if ot_lower == v:
                    return i
            else:
                if v in ot_lower:
                    return i
    return None


def _lue_laskentakohde_myynti(df_raw, projekti_hakusana: str = "") -> pd.DataFrame:
    """
    Lukee myyntilaskut LASKENTAKOHDERAPORTISTA (11-sarakkeinen muoto, sama kuin ostot).
    Poimii ML Myyntilasku -rivit (summa Kredit-sarakkeessa).
    Sarakkeet: 0 Päiväys, 1 Tositelaji, 3 Lasku, 6 Debet, 7 Kredit, 9 Selite, 10 Laskentakohteet.
    """
    df = df_raw.iloc[1:].reset_index(drop=True)  # ohita otsikkorivi
    df.columns = range(len(df.columns))
    df = df.dropna(how="all").reset_index(drop=True)

    # Vain myyntilaskurivit
    df = df[df[1].astype(str).str.contains("Myyntilasku", case=False, na=False)].copy()
    if df.empty:
        return pd.DataFrame()

    tulos = pd.DataFrame()
    tulos["lasku_nro"]     = df[3]
    tulos["lasku_pvm"]     = pd.to_datetime(df[0], errors="coerce")
    tulos["erapaiva"]      = pd.NaT
    debet  = pd.to_numeric(df[6], errors="coerce").fillna(0)
    kredit = pd.to_numeric(df[7], errors="coerce").fillna(0)
    tulos["summa"]         = kredit - debet           # myynti = kredit
    tulos["avoimena"]      = 0                          # tila ei ole tässä raportissa
    tulos["vapaa_teksti"]  = (df[10].astype(str) + " " + df[9].astype(str))
    tulos["sisalto"]       = df[9].astype(str)
    tulos["tila_netvisor"] = ""
    tulos["_laskentakohde"] = df[10].astype(str)

    if projekti_hakusana:
        maski = tulos["vapaa_teksti"].str.lower().str.contains(projekti_hakusana.lower(), na=False)
        tulos = tulos[maski].copy()

    # Kategoria laskentakohteen mukaan: LISÄTYÖT → Lisätyö, muuten Urakka
    from classifier import luokittele_kategoria
    tulos["kategoria"] = tulos["_laskentakohde"].apply(luokittele_kategoria)
    tulos = tulos.drop(columns=["_laskentakohde"])
    tulos["tila"]      = "📄 Laskutettu"               # raportti ei kerro maksutilaa
    tulos = tulos[tulos["lasku_nro"].notna()].reset_index(drop=True)
    return tulos.sort_values("lasku_pvm", ascending=False).reset_index(drop=True)


def lue_myyntireskontra(tiedosto, projekti_hakusana: str = "") -> pd.DataFrame:
    df_raw = pd.read_excel(tiedosto, sheet_name=0, header=None)

    # Tunnista muoto otsikkorivistä
    otsikot_kaikki = " ".join(str(v).lower() for v in df_raw.iloc[0].tolist() if pd.notna(v))
    if "laskunumero" not in otsikot_kaikki and "tositelaji" in otsikot_kaikki:
        # Laskentakohderaportti-muoto (11 saraketta, ML Myyntilasku -rivit)
        return _lue_laskentakohde_myynti(df_raw, projekti_hakusana)

    # Otsikkorivi: etsitään rivi jossa on "Laskunumero"
    otsikkorivi = 0
    for i, row in df_raw.iterrows():
        if any("laskunumero" in str(v).lower() for v in row if pd.notna(v)):
            otsikkorivi = i
            break

    otsikot = df_raw.iloc[otsikkorivi].tolist()
    df = df_raw.iloc[otsikkorivi + 1:].reset_index(drop=True)
    df.columns = range(len(df.columns))

    # Poista täysin tyhjät rivit
    df = df.dropna(how="all").reset_index(drop=True)

    # Etsi sarakkeet nimien perusteella
    idx = {kentta: _etsi_sarake(otsikot, vaihtoehdot, tarkka=(kentta in _TARKKAHAKU))
           for kentta, vaihtoehdot in _SARAKE_HAKU.items()}

    def _hae(kentta):
        i = idx.get(kentta)
        return df[i] if i is not None else pd.Series([None] * len(df))

    tulos = pd.DataFrame()
    tulos["lasku_nro"]    = _hae("lasku_nro")
    tulos["lasku_pvm"]    = pd.to_datetime(_hae("lasku_pvm"), errors="coerce")
    tulos["erapaiva"]     = pd.to_datetime(_hae("erapaiva"), errors="coerce")
    tulos["maksu_pvm"]    = pd.to_datetime(_hae("maksu_pvm"), errors="coerce")
    tulos["summa"]        = pd.to_numeric(_hae("veroton_summa"), errors="coerce").fillna(0)
    tulos["avoimena"]     = pd.to_numeric(_hae("avoimena"), errors="coerce").fillna(0)
    tulos["asiakas"]      = _hae("asiakas").astype(str)
    tulos["vapaa_teksti"] = _hae("vapaa_teksti").astype(str)
    tulos["tosite"]       = _hae("tosite")
    tulos["tila_netvisor"]= _hae("tila").astype(str)

    # Suodata projektin mukaan
    if projekti_hakusana:
        maski = tulos["vapaa_teksti"].str.lower().str.contains(
            projekti_hakusana.lower(), na=False)
        tulos = tulos[maski].copy()

    # Luokittelu
    tulos["kategoria"] = tulos["vapaa_teksti"].apply(_luokittele_kategoria)
    tulos["tila"] = tulos.apply(
        lambda r: _tila_badge(r["tila_netvisor"], r["erapaiva"]), axis=1)

    def _lyhenna(t):
        if not isinstance(t, str): return ""
        osat = [o.strip() for o in t.replace("\\n", "\n").split("\n") if o.strip()]
        return " | ".join(osat[1:]) if len(osat) > 1 else (osat[0] if osat else "")

    tulos["sisalto"] = tulos["vapaa_teksti"].apply(_lyhenna)

    # Poistetaan täysin tyhjät lasku_nro-rivit
    tulos = tulos[tulos["lasku_nro"].notna()].reset_index(drop=True)

    return tulos.sort_values("lasku_pvm", ascending=False).reset_index(drop=True)
