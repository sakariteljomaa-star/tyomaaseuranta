"""
Labroc-tulosten automaattinen nouto sähköpostista (IMAP) ja PDF:n tulkinta.

Tulokset saapuvat osoitteeseen info@uudenmaanasbestipurku.fi lähettäjältä
laboratorio.helsinki@labroc.fi, aihe "Tutkimustuloksia kohteesta: <kohde>".

Raporttityypit erotetaan sisällöstä/tiedostonimestä (ks. CATEVA_DOKUMENTTIPOHJAT.md):
  - "ASBESTIANALYYSI ILMANÄYTTEESTÄ" (*_ilma.pdf) = puhdastilamittaus
  - "ASBESTIANALYYSI"                (*ASB.pdf)   = materiaalinäyte (kartoitus)

Streamlit secrets:
    [labroc_email]
    host = "imap.gmail.com"
    user = "..."
    password = "...(Gmailin sovellussalasana)..."
    kansio = "INBOX"          # vapaaehtoinen

Tulkinta ei koskaan hyväksy epäselvää tulosta automaattisesti — jos arvoja ei
saada varmasti luettua, tulos_ok on None ja rivi jää käsin tarkistettavaksi.
"""

import email
import imaplib
import io
import re
from email.header import decode_header

LABROC_LAHETTAJA = "laboratorio.helsinki@labroc.fi"
RAJA_ARVO = 0.01  # kuitua/cm³, VNa 798/2015


def _dekoodaa(arvo) -> str:
    if not arvo:
        return ""
    osat = []
    for teksti, koodaus in decode_header(arvo):
        if isinstance(teksti, bytes):
            osat.append(teksti.decode(koodaus or "utf-8", errors="replace"))
        else:
            osat.append(teksti)
    return "".join(osat).strip()


def parsi_labroc_pdf(data: bytes) -> dict:
    """
    Palauttaa: {"onko_ilma": bool, "kohde": str, "projektinro": str,
                "tulos_ok": True/False/None, "tulos_teksti": str}
    """
    try:
        from pypdf import PdfReader
        teksti = "\n".join((s.extract_text() or "") for s in PdfReader(io.BytesIO(data)).pages)
    except Exception:
        return {"onko_ilma": False, "kohde": "", "projektinro": "",
                "tulos_ok": None, "tulos_teksti": "PDF:ää ei voitu lukea"}

    iso = teksti.upper()
    onko_ilma = ("ILMANÄYTTEESTÄ" in iso or "ILMA-ANALYYSIVASTAUS" in iso
                 or "ILMANÄYTTEET" in iso)

    m = (re.search(r"Kohde:\s*(.+?)\s*(?:Toimitettu laboratorioon|$)", teksti)
         or re.search(r"KOHDE\s*[:|]?\s*(.+)", teksti))
    kohde = (m.group(1).strip() if m else "").splitlines()[0].strip() if m else ""

    m = re.search(r"(\d{5,7})\s*/\s*ASB", teksti)
    projektinro = m.group(1) if m else ""

    tulos_ok, tulos_teksti = None, ""

    if onko_ilma:
        # Tulososio otsikkorivin ja alaviitteen välistä
        alku = re.search(r"Tulos\s*\*?|Asbestikuitua/cm", teksti)
        loppu = re.search(r"\*\s*Valtioneuvoston|Kuitulaskenta on tehty", teksti)
        osio = teksti[alku.end() if alku else 0:loppu.start() if loppu else len(teksti)]
        arvot = []
        for etu, num in re.findall(r"([<≤]?)\s*(\d+[.,]\d+)", osio):
            try:
                arvo = float(num.replace(",", "."))
            except ValueError:
                continue
            if arvo > 100:      # ilmamäärät tms., ei kuitupitoisuus
                continue
            arvot.append((etu, arvo))
        if arvot:
            ylitykset = [a for etu, a in arvot if not etu and a > RAJA_ARVO]
            tulos_ok = not ylitykset
            if tulos_ok:
                tulos_teksti = f"Kaikki näytteet ≤ {RAJA_ARVO} kuitua/cm³ — HYVÄKSYTTY"
            else:
                pahin = max(ylitykset)
                tulos_teksti = f"Raja-arvo ylittyy ({pahin} kuitua/cm³) — HYLÄTTY"
        else:
            tulos_teksti = "Tulosarvoja ei saatu luettua — tarkista käsin"
    else:
        loydot = re.findall(r"(Sisältää asbestia[^\n]*|Ei sisällä asbestia\.?)", teksti)
        tulos_teksti = "; ".join(dict.fromkeys(loydot)) or "Materiaalianalyysi — katso PDF"

    return {"onko_ilma": onko_ilma, "kohde": kohde, "projektinro": projektinro,
            "tulos_ok": tulos_ok, "tulos_teksti": tulos_teksti}


def hae_uudet_tulokset(host: str, user: str, password: str, kansio: str = "INBOX",
                       ohita_idt: set = None, max_viestit: int = 50) -> list:
    """
    Hakee IMAP:lla Labrocin viestit ja palauttaa uudet PDF-liitteet.

    Palauttaa listan: {"viesti_id": str, "aihe": str, "aihe_kohde": str,
                       "pvm": str, "tiedostonimi": str, "data": bytes}
    ohita_idt: jo käsiteltyjen Message-ID:iden joukko.
    """
    ohita_idt = ohita_idt or set()
    tulokset = []

    posti = imaplib.IMAP4_SSL(host)
    try:
        posti.login(user, password)
        posti.select(kansio, readonly=True)
        ok, data = posti.search(None, "FROM", f'"{LABROC_LAHETTAJA}"')
        if ok != "OK":
            return []
        viesti_nrot = data[0].split()
        for nro in reversed(viesti_nrot[-max_viestit * 2:]):
            if len(tulokset) >= max_viestit:
                break
            ok, osat = posti.fetch(nro, "(RFC822)")
            if ok != "OK" or not osat or not osat[0]:
                continue
            viesti = email.message_from_bytes(osat[0][1])
            viesti_id = _dekoodaa(viesti.get("Message-ID", "")) or f"nro-{nro.decode()}"
            if viesti_id in ohita_idt:
                continue
            aihe = _dekoodaa(viesti.get("Subject", ""))
            aihe_kohde = re.sub(r"^Tutkimustuloksia kohteesta:\s*", "", aihe, flags=re.I).strip()
            pvm = _dekoodaa(viesti.get("Date", ""))
            for osa in viesti.walk():
                nimi = osa.get_filename()
                if not nimi:
                    continue
                nimi = _dekoodaa(nimi)
                if not nimi.lower().endswith(".pdf"):
                    continue
                sisalto = osa.get_payload(decode=True)
                if not sisalto:
                    continue
                tulokset.append({
                    "viesti_id": viesti_id,
                    "aihe": aihe,
                    "aihe_kohde": aihe_kohde,
                    "pvm": pvm,
                    "tiedostonimi": nimi,
                    "data": sisalto,
                })
    finally:
        try:
            posti.logout()
        except Exception:
            pass

    return tulokset


def kohdista_kohteeseen(tulos: dict, parsittu: dict, kohteet: list):
    """
    Yrittää kohdistaa tuloksen Cateva-kohteeseen.
    Ensisijaisesti työnumerolla (aihe/tiedostonimi/PDF:n kohde), toissijaisesti
    osoitteella. Palauttaa kohteen dictin tai None.
    """
    haku = " ".join([tulos.get("aihe", ""), tulos.get("aihe_kohde", ""),
                     tulos.get("tiedostonimi", ""), parsittu.get("kohde", "")]).lower()

    for kohde in kohteet:
        nro = str(kohde.get("tyonumero", "")).strip().lower()
        if nro and nro in haku:
            return kohde

    def _norm(s):
        return re.sub(r"[^a-z0-9äöå]", "", str(s).lower())

    ehdokkaat = [_norm(tulos.get("aihe_kohde", "")), _norm(parsittu.get("kohde", ""))]
    for kohde in kohteet:
        osoite = _norm(kohde.get("osoite", ""))
        if len(osoite) < 6:
            continue
        if osoite in _norm(haku):
            return kohde
        # Sama osoite ilman kaupunkiliitettä: "koroistentie8c19" ⊂ "koroistentie8c19helsinki"
        for e in ehdokkaat:
            if len(e) >= 6 and (e in osoite or osoite in e):
                return kohde
    return None
