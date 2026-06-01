"""
Lukee Netvisor-laskentakohderaportti XLSX:n ja palauttaa siistin DataFramen.
"""

import pandas as pd
from classifier import luokittele_kategoria, luokittele_kululaji, luokittele_nimike_laji


SARAKKEET = {
    0: "pvm",
    1: "tositelaji",
    2: "tosite",
    3: "lasku",
    4: "alv_pct",
    5: "alv_tunnus",
    6: "debet",
    7: "kredit",
    8: "saldo",
    9: "selite",
    10: "laskentakohteet",
}


def lue_netvisor(tiedosto) -> pd.DataFrame:
    """Lukee yhden Netvisor-XLSX-tiedoston, palauttaa luokiteltujen rivien DataFramen."""
    df = pd.read_excel(tiedosto, sheet_name=0, header=None)

    # Otsikkorivi on rivi 0, data alkaa rivistä 2 (rivi 1 = alkusaldo)
    df = df.iloc[2:].reset_index(drop=True)
    df = df.rename(columns=SARAKKEET)

    # Poista tyhjät rivit
    df = df[df["debet"].notna() | df["kredit"].notna()].copy()

    # Muunna tyypit
    df["pvm"] = pd.to_datetime(df["pvm"], errors="coerce")
    df["debet"] = pd.to_numeric(df["debet"], errors="coerce").fillna(0)
    df["kredit"] = pd.to_numeric(df["kredit"], errors="coerce").fillna(0)
    df["summa"] = df["debet"] - df["kredit"]

    # Luokittelu
    df["kategoria"] = df["laskentakohteet"].apply(luokittele_kategoria)
    df["kululaji"] = df.apply(
        lambda r: luokittele_kululaji(r["selite"], r["alv_tunnus"], r.get("alv_pct")), axis=1
    )
    df["nimike_laji"] = df["selite"].apply(luokittele_nimike_laji)

    return df


def yhdista_tiedostot(tiedostot) -> pd.DataFrame:
    osat = []
    for t in tiedostot:
        try:
            osat.append(lue_netvisor(t))
        except Exception as e:
            print(f"Virhe tiedostossa {getattr(t, 'name', t)}: {e}")
    if not osat:
        return pd.DataFrame()
    yhdistetty = pd.concat(osat, ignore_index=True)
    # Poista duplikaatit saman tosite+lasku+selite-yhdistelmän perusteella
    yhdistetty = yhdistetty.drop_duplicates(subset=["tosite", "lasku", "selite", "summa"])
    return yhdistetty.sort_values("pvm")
