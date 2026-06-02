"""
Lukee Kalustonhallinta-XLSX:n ja palauttaa laiterekisterin listana.
"""

import pandas as pd
import re


def lue_kalustorekisteri(tiedosto) -> list:
    """Palauttaa list[dict] kaikista laitteista."""
    df = pd.read_excel(tiedosto, sheet_name=0, header=None)

    laitteet = []
    for _, row in df.iterrows():
        nro = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        if not re.match(r'^[A-Z]{2}-\d+', nro):
            continue
        kategoria   = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        laite       = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        merkki      = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
        sarjanumero = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ""
        huomiot     = str(row.iloc[7]).strip() if pd.notna(row.iloc[7]) else ""

        if not laite:
            continue  # tyhjä paikka rekisterissä

        laitteet.append({
            "nro":         nro,
            "kategoria":   kategoria,
            "laite":       laite,
            "merkki":      merkki,
            "sarjanumero": sarjanumero,
            "kunto":       "OK",
            "sijainti":    "Varasto",
            "huomiot":     huomiot,
            "omistus":     "vuokra" if "VUOKRA" in huomiot.upper() else "oma",
        })

    return laitteet
