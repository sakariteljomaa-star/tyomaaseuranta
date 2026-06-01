"""
Luokittelee Netvisor-rivit automaattisesti kululajeihin ja kategorioihin.
"""

JATE_TOIMITTAJAT = ["kuljetusrinki", "labroc"]
KALUSTO_TOIMITTAJAT = ["konevuokraamo", "rk rakentajan"]
SUOJAIN_SANAT = ["haalari", "suojalasi", "hengityssuojain", "ffp3", "kulmaletku", "promask"]

NIMIKE_LAJI_MAP = {
    "haalari": "Suojaimet",
    "suojalasi": "Suojaimet",
    "hengityssuojain": "Suojaimet",
    "ffp3": "Suojaimet",
    "kulmaletku": "Suojaimet",
    "promask": "Suojaimet",
    "purkusäkki": "Kalusto/tarvike",
    "bigbag": "Kalusto/tarvike",
    "suursäkki": "Kalusto/tarvike",
    "muovikalvo": "Kalusto/tarvike",
    "teippi": "Tarvike",
    "rima": "Tarvike",
    "rakennusmuovi": "Tarvike",
    "sinkilä": "Tarvike",
    "kenkäsuoja": "Tarvike",
    "mattoveitsen": "Tarvike",
    "apuvoima": "Apuvoima",
}


def luokittele_kategoria(laskentakohteet: str) -> str:
    if isinstance(laskentakohteet, str) and "LISÄTYÖT" in laskentakohteet.upper():
        return "Lisätyö"
    return "Urakka"


def luokittele_kululaji(selite: str, alv_tunnus: str, alv_pct=None) -> str:
    """Palauttaa kululajin: Aliurakoitsijat, Jätemaksut, Kalusto, Ostot."""
    s = selite.lower() if isinstance(selite, str) else ""
    alv = alv_tunnus.upper() if isinstance(alv_tunnus, str) else ""

    if alv == "RAOS":
        return "Aliurakoitsijat"

    # Ostopalvelu ALV 0% — "Työ (vko XX)" tai "aloitus pvm" selitteissä
    try:
        alv_num = float(str(alv_pct).replace(",", ".")) if alv_pct is not None else None
    except (ValueError, TypeError):
        alv_num = None
    if alv_num == 0 and (s.startswith("työ") or "aloitus pvm" in s):
        return "Aliurakoitsijat"

    for toimittaja in JATE_TOIMITTAJAT:
        if toimittaja in s:
            return "Jätemaksut"

    for toimittaja in KALUSTO_TOIMITTAJAT:
        if toimittaja in s:
            return "Kalusto"

    if "a-voima" in s:
        return "Ostot"

    return "Ostot"


def luokittele_nimike_laji(selite: str) -> str:
    s = selite.lower() if isinstance(selite, str) else ""
    for avain, laji in NIMIKE_LAJI_MAP.items():
        if avain in s:
            return laji
    return "Tarvike"
