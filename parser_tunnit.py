"""
Lukee Netvisor tuntikirjanpito-XLSX:n (laskentakohde-suodatettuna).
Palauttaa: projektin nimi, jakso, ja DataFrame työntekijöistä + tunneista.
"""

import pandas as pd


# Sarakkeet joista kerätään työtunnit (indeksi → lyhyt nimi)
TUNTIKOLUMNIT = {
    1:  "Normaali",
    21: "Lisätyö",
    29: "Urakkatyö",
    53: "Työtunnit",
    54: "Yhteensä",
}


def lue_tuntikirjanpito(tiedosto) -> dict:
    """
    Palauttaa dict:
      - projekti: str
      - jakso: str
      - df: DataFrame (työntekijä + tunnit)
      - yht_tunnit: float
    """
    df_raw = pd.read_excel(tiedosto, sheet_name=0, header=None)

    # Metadata riveistä 0-2
    jakso = ""
    projekti = ""
    for i in range(3):
        arvo = str(df_raw.iloc[i, 1]) if pd.notna(df_raw.iloc[i, 1]) else ""
        if "." in arvo and "-" in arvo:
            jakso = arvo.strip()
        elif arvo and arvo != "nan":
            projekti = arvo.strip()

    # Otsikkorivi = rivi 3
    otsikot = df_raw.iloc[3].tolist()

    # Datarivit: rivit 4 … viimeinen ei-tyhjä ennen "Raportti yhteensä"
    data = df_raw.iloc[4:].copy()
    data = data[data[0].notna() & ~data[0].astype(str).str.startswith("Raportti")]
    data = data.reset_index(drop=True)

    if data.empty:
        return {"projekti": projekti, "jakso": jakso, "df": pd.DataFrame(), "yht_tunnit": 0}

    # Kootaan siisti DataFrame
    rivit = []
    for _, row in data.iterrows():
        nimi = str(row[0]).strip()
        if not nimi or nimi == "nan":
            continue
        r = {"Työntekijä": nimi}
        for idx, sarake in TUNTIKOLUMNIT.items():
            r[sarake] = float(row[idx]) if pd.notna(row[idx]) else 0.0
        rivit.append(r)

    df = pd.DataFrame(rivit)
    yht = df["Työtunnit"].sum() if "Työtunnit" in df.columns else 0

    return {
        "projekti": projekti,
        "jakso": jakso,
        "df": df,
        "yht_tunnit": yht,
    }
