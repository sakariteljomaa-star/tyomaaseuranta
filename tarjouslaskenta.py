"""
Tarjouslaskenta Cateva-kohteille.

Periaate: tarjous lasketaan AINA samalla tavalla — vakiopaketti hinnastosta +
tapauskohtaiset rivit. Summaa verrataan minimiveloitukseen (1 000 €), ja
pienempi summa korotetaan minimiin.

Hinnasto ja asetukset tallennetaan globaaliin avaimeen `asbesti_hinnasto`
(muokattavissa appissa) — tämän tiedoston arvot ovat oletukset ensimmäisellä
käynnistyksellä. Hinnat ALV 0 % (rakentamispalvelun käännetty verovelvollisuus).
"""

import io
import re

# Sovittu hinnoitteluperusta (8/2026)
OLETUSHINNASTO = [
    {"koodi": "vastaanotto",  "nimi": "Työn vastaanotto ja ennakkoilmoitus",                    "yksikko": "erä", "hinta": 250.0},
    {"koodi": "osastointi",   "nimi": "Osastointi ja suojaukset (sis. alipaineistuslaitteet)",  "yksikko": "erä", "hinta": 350.0},
    {"koodi": "purkutyo",     "nimi": "Asbestipurkutyö",                                        "yksikko": "h",   "hinta": 55.0},
    {"koodi": "loppumittaus", "nimi": "Loppumittaus ja dokumentointi",                          "yksikko": "erä", "hinta": 175.0},
    {"koodi": "puhdastila",   "nimi": "Puhdastilamittaus (ellei sisälly suojauksiin)",          "yksikko": "erä", "hinta": 150.0},
    {"koodi": "jate",         "nimi": "Asbestijätteen käsittely paketoituna (minimi)",          "yksikko": "erä", "hinta": 90.0},
    {"koodi": "matka",        "nimi": "Matkakulut",                                             "yksikko": "km",  "hinta": 1.0},
    {"koodi": "kulut_pk",     "nimi": "Kulukorvaus pk-seutu (pysäköinti ym.)",                  "yksikko": "erä", "hinta": 25.0},
    {"koodi": "lisatyo_tt",   "nimi": "Lisätyö, työntekijä",                                    "yksikko": "h",   "hinta": 55.0},
    {"koodi": "lisatyo_tj",   "nimi": "Lisätyö, työnjohto",                                     "yksikko": "h",   "hinta": 75.0},
]

OLETUSASETUKSET = {
    "minimiveloitus": 1000.0,
    "voimassaolo_vrk": 30,
    "maksuehto": "14 pv netto",
}

# Vakiopaketti: rivit ja oletusmäärät, joilla jokainen tarjous aloitetaan.
VAKIOPAKETTI = [
    ("vastaanotto", 1), ("osastointi", 1), ("purkutyo", 4),
    ("loppumittaus", 1), ("jate", 1), ("kulut_pk", 1), ("matka", 0),
]


def oletustarjousrivit(hinnasto: list) -> list:
    """Vakiopaketin rivit tarjouksen pohjaksi."""
    h = {r["koodi"]: r for r in hinnasto}
    rivit = []
    for koodi, maara in VAKIOPAKETTI:
        r = h.get(koodi)
        if r:
            rivit.append({"nimi": r["nimi"], "yksikko": r["yksikko"],
                          "maara": float(maara), "a_hinta": float(r["hinta"])})
    return rivit


def laske_summat(rivit: list, minimiveloitus: float):
    """Palauttaa (rivit joissa summa, välisumma, loppusumma, minimi_kaytossa)."""
    ulos = []
    valisumma = 0.0
    for r in rivit:
        try:
            maara = float(r.get("maara") or 0)
            a_hinta = float(r.get("a_hinta") or 0)
        except (TypeError, ValueError):
            maara, a_hinta = 0.0, 0.0
        summa = round(maara * a_hinta, 2)
        if not str(r.get("nimi", "")).strip():
            continue
        ulos.append({**r, "maara": maara, "a_hinta": a_hinta, "summa": summa})
        valisumma += summa
    valisumma = round(valisumma, 2)
    minimi_kaytossa = 0 < valisumma < minimiveloitus
    loppusumma = minimiveloitus if minimi_kaytossa else valisumma
    return ulos, valisumma, round(loppusumma, 2), minimi_kaytossa


def parsi_cateva_kartoitus(data: bytes, tiedostonimi: str = "") -> dict:
    """
    Poimii Catevan asbesti- ja haitta-ainekartoitusraportista laskennan
    lähtötiedot. Sietää puuttuvia kenttiä — palauttaa mitä irti saa.
    """
    tulos = {"tyonumero": "", "kohde": "", "osoite": "", "tilaaja": "",
             "kartoittaja": "", "kartoitus_pvm": "", "materiaalit": [],
             "toimenpide": ""}

    m = re.match(r"(\d{5,8})", tiedostonimi or "")
    if m:
        tulos["tyonumero"] = m.group(1)

    try:
        from pypdf import PdfReader
        teksti = "\n".join((s.extract_text() or "")
                           for s in PdfReader(io.BytesIO(data)).pages)
    except Exception:
        return tulos

    def _poimi(kuvio):
        m = re.search(kuvio, teksti)
        return m.group(1).strip() if m else ""

    tulos["kohde"] = _poimi(r"Kohde\s+(.+)")
    tulos["osoite"] = _poimi(r"Osoite\s+(.+)")
    tulos["tilaaja"] = _poimi(r"Tilaaja\s+(.+)")
    tulos["kartoittaja"] = _poimi(r"N[äa]ytt?een ?ottaja\s+(.+)")
    tulos["kartoitus_pvm"] = _poimi(r"N[äa]ytt?eenotto p[äa]iv[äa]m[äa][äa]r[äa]\s+([\d.]+)")
    if not tulos["kartoitus_pvm"]:
        tulos["kartoitus_pvm"] = _poimi(r"^(\d{2}\.\d{2}\.\d{4})")

    # Näytteet joissa asbestia: Sijainti / Materiaali / Asbestilaatu -kolmikot
    lohkot = re.findall(
        r"Sijainti\s+(.+?)\s*\nMateriaali\s+(.+?)\s*\n(?:.*?\n)?(?:Asbestilaatu\s+(.+?)\s*\n)?",
        teksti)
    for sijainti, materiaali, laatu in lohkot:
        tulos["materiaalit"].append({
            "sijainti": sijainti.strip(),
            "materiaali": materiaali.strip(),
            "laatu": (laatu or "").strip(),
        })

    # Toimenpide-ehdotuskoodit massaluettelosta (esim. "3,4")
    m = re.search(r"Toimenpide-?\s*ehdotus[\s\S]{0,400}?(\d(?:\s*,\s*\d)+|\b[1-7]\b)\s*\n",
                  teksti)
    if m:
        tulos["toimenpide"] = m.group(1).replace(" ", "")

    return tulos


def kuvaus_kartoituksesta(k: dict) -> str:
    """Lyhyt tekstikuvaus kohteelle kartoituksen tiedoista."""
    osat = []
    for mt in k.get("materiaalit", []):
        rivi = mt.get("sijainti", "")
        if mt.get("materiaali"):
            rivi += f": {mt['materiaali']}"
        if mt.get("laatu"):
            rivi += f" ({mt['laatu']})"
        osat.append(rivi)
    if k.get("toimenpide"):
        osat.append(f"Toimenpide-ehdotus {k['toimenpide']}")
    return ". ".join(o for o in osat if o)
