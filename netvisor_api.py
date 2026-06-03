"""
Netvisor API -integraatio — hakee laskut suoraan rajapinnasta.

Tunnistus: Netvisorin MAC-autentikointi (SHA256-hash parametreista + avaimet).
Vaatii tunnukset (Streamlit secrets [netvisor]):
    sender          = "Integraation nimi"
    partner_id      = "..."         # Partner ID
    partner_key     = "..."         # Partner private key
    customer_id     = "..."         # Customer ID (yrityksen API-avain)
    customer_key    = "..."         # Customer private key
    organisation_id = "2817254-1"   # Y-tunnus
    base_url        = "https://isvapi.netvisor.fi"   # (oletus)

Tunnusten luonti Netvisorissa: Yritysasetukset → Rajapinta/Integraatiot →
luo integraatiotunnukset. Saat sender-, customer- ja partner-tiedot + avaimet.

HUOM: kenttien kohdistus (etenkin ALV-tunnus ja laskentakohde) voi vaatia
hienosäätöä oikean API-vastauksen perusteella — käytä "näytä raakavastaus".
"""

import hashlib
import uuid
import datetime
import xml.etree.ElementTree as ET
import requests
import pandas as pd

from classifier import luokittele_kategoria, luokittele_kululaji, luokittele_nimike_laji


# ── Tunnukset ──────────────────────────────────────────────────────────────────

def hae_tunnukset(st) -> dict:
    """Lukee Netvisor-tunnukset Streamlit secretsistä. Palauttaa {} jos puuttuu."""
    try:
        c = dict(st.secrets["netvisor"])
        c.setdefault("base_url", "https://isvapi.netvisor.fi")
        return c
    except Exception:
        return {}


def on_konfiguroitu(st) -> bool:
    c = hae_tunnukset(st)
    return all(c.get(k) for k in
               ["sender", "partner_id", "partner_key", "customer_id", "customer_key", "organisation_id"])


# ── MAC-autentikointi ──────────────────────────────────────────────────────────

def _timestamp() -> str:
    # Netvisor: UTC, muoto "YYYY-MM-DD HH:MM:SS.fff"
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def _laske_mac(url, sender, customer_id, timestamp, language,
               organisation_id, transaction_id, customer_key, partner_key) -> str:
    osat = [url, sender, customer_id, timestamp, language,
            organisation_id, transaction_id, customer_key, partner_key]
    mac_str = "&".join(osat)
    return hashlib.sha256(mac_str.encode("utf-8")).hexdigest()

def _otsikot(creds: dict, url: str) -> dict:
    ts  = _timestamp()
    tid = uuid.uuid4().hex
    lang = "FI"
    mac = _laske_mac(
        url, creds["sender"], creds["customer_id"], ts, lang,
        creds["organisation_id"], tid, creds["customer_key"], creds["partner_key"],
    )
    return {
        "X-Netvisor-Authentication-Sender":        creds["sender"],
        "X-Netvisor-Authentication-CustomerId":    creds["customer_id"],
        "X-Netvisor-Authentication-PartnerId":     creds["partner_id"],
        "X-Netvisor-Authentication-Timestamp":     ts,
        "X-Netvisor-Interface-Language":           lang,
        "X-Netvisor-Organisation-ID":              creds["organisation_id"],
        "X-Netvisor-Authentication-TransactionId": tid,
        "X-Netvisor-Authentication-MAC":           mac,
        "X-Netvisor-Authentication-MACHashCalculationAlgorithm": "SHA256",
    }


# ── Raaka pyyntö ───────────────────────────────────────────────────────────────

def pyynto(creds: dict, endpoint: str, params: dict = None) -> str:
    """Tekee GET-pyynnön Netvisor-endpointtiin. Palauttaa XML-tekstin."""
    base = creds["base_url"].rstrip("/")
    # Rakenna täysi URL ilman query-parametreja (MAC lasketaan perus-URLista)
    url = f"{base}/{endpoint}"
    headers = _otsikot(creds, url)
    r = requests.get(url, headers=headers, params=params or {}, timeout=30)
    r.raise_for_status()
    return r.text


def _tarkista_status(xml_teksti: str):
    """Nostaa virheen jos Netvisor palautti Failed-statuksen."""
    try:
        root = ET.fromstring(xml_teksti)
        status = root.findtext(".//ResponseStatus/Status")
        if status and status.lower() != "ok":
            viesti = root.findtext(".//ResponseStatus/Status[2]") or ""
            # Netvisor laittaa virheviestin toiseen Status-elementtiin
            kaikki = [e.text for e in root.findall(".//ResponseStatus/")]
            raise RuntimeError(f"Netvisor: {' '.join(t for t in kaikki if t)}")
    except ET.ParseError as e:
        raise RuntimeError(f"XML-jäsennysvirhe: {e}")


def testaa_yhteys(creds: dict) -> tuple:
    """Palauttaa (ok, viesti). Käyttää kevyttä endpointtia."""
    try:
        xml = pyynto(creds, "companyinformation.nv")
        _tarkista_status(xml)
        root = ET.fromstring(xml)
        nimi = root.findtext(".//Name") or root.findtext(".//CompanyInformation/Name") or "?"
        return True, f"Yhteys OK — {nimi}"
    except Exception as e:
        return False, f"Yhteys epäonnistui: {e}"


# ── Ostolaskut ─────────────────────────────────────────────────────────────────

def hae_ostolaskut(creds: dict, alkupvm: str, loppupvm: str) -> pd.DataFrame:
    """
    Hakee ostolaskut aikaväliltä ja palauttaa parser.py:n kanssa
    yhteensopivan DataFramen (rivi per laskurivi laskentakohteineen).
    alkupvm/loppupvm: 'YYYY-MM-DD'
    """
    lista_xml = pyynto(creds, "purchaseinvoicelist.nv",
                       {"begininvoicedate": alkupvm, "endinvoicedate": loppupvm})
    _tarkista_status(lista_xml)
    root = ET.fromstring(lista_xml)

    netvisor_keys = [e.text for e in root.findall(".//PurchaseInvoice/NetvisorKey") if e.text]

    rivit = []
    for nk in netvisor_keys:
        try:
            inv_xml = pyynto(creds, "getpurchaseinvoice.nv", {"netvisorkey": nk})
            _tarkista_status(inv_xml)
            rivit.extend(_jasenna_ostolasku(inv_xml))
        except Exception:
            continue  # ohita yksittäinen epäonnistunut lasku

    df = pd.DataFrame(rivit)
    if df.empty:
        return df

    df["pvm"] = pd.to_datetime(df["pvm"], errors="coerce")
    df["summa"] = pd.to_numeric(df["summa"], errors="coerce").fillna(0)
    df["debet"] = df["summa"]
    df["kredit"] = 0
    df["kategoria"]   = df["laskentakohteet"].apply(luokittele_kategoria)
    df["kululaji"]    = df.apply(lambda r: luokittele_kululaji(r["selite"], r["alv_tunnus"], r.get("alv_pct")), axis=1)
    df["nimike_laji"] = df["selite"].apply(luokittele_nimike_laji)
    return df


def _jasenna_ostolasku(inv_xml: str) -> list:
    """Poimii yhden ostolaskun riveistä parser-yhteensopivat dictit."""
    root = ET.fromstring(inv_xml)
    pi = root.find(".//PurchaseInvoice")
    if pi is None:
        return []

    toimittaja = pi.findtext("InvoiceSupplierName") or ""
    lasku_nro  = pi.findtext("InvoiceNumber") or ""
    pvm        = pi.findtext("InvoiceDate") or ""
    tosite     = pi.findtext("Voucher/VoucherNumber") or pi.findtext("InvoiceNumber") or ""

    rivit = []
    for rl in pi.findall(".//InvoiceLine/PurchaseInvoiceLine"):
        selite = rl.findtext("ProductName") or rl.findtext("Description") or toimittaja
        summa  = rl.findtext("AmountWithoutVat") or rl.findtext("LineSum") or "0"
        alv_pct = rl.findtext("VatPercent") or ""
        alv_tunnus = rl.findtext("VatCode") or rl.findtext("AccountName") or ""
        # Laskentakohde (dimensio)
        lk = rl.findtext(".//Dimension/DimensionItem") or ""
        rivit.append({
            "pvm": pvm, "tositelaji": "Ostolasku", "tosite": tosite,
            "lasku": lasku_nro, "alv_pct": alv_pct, "alv_tunnus": alv_tunnus,
            "summa": summa, "selite": f"{toimittaja} – {selite}".strip(" –"),
            "laskentakohteet": lk,
        })
    return rivit


# ── Myyntilaskut ───────────────────────────────────────────────────────────────

def hae_myyntilaskut(creds: dict, alkupvm: str, loppupvm: str, projekti_hakusana: str = "") -> pd.DataFrame:
    """Hakee myyntilaskut aikaväliltä → parser_myynti.py-yhteensopiva DataFrame."""
    lista_xml = pyynto(creds, "salesinvoicelist.nv",
                       {"begininvoicedate": alkupvm, "endinvoicedate": loppupvm})
    _tarkista_status(lista_xml)
    root = ET.fromstring(lista_xml)

    from datetime import date as _date
    rivit = []
    for si in root.findall(".//SalesInvoice"):
        nro   = si.findtext("NetvisorKey") or ""
        lasku_nro = si.findtext("InvoiceNumber") or nro
        pvm   = si.findtext("InvoiceDate") or ""
        summa = si.findtext("InvoiceSum") or si.findtext("SumWithoutVat") or "0"
        avoin = si.findtext("OpenSum") or "0"
        asiakas = si.findtext("InvoiceStatus") or ""
        teksti = si.findtext("AdditionalInformation") or si.findtext("FreeText") or ""
        rivit.append({
            "lasku_nro": lasku_nro, "lasku_pvm": pvm, "erapaiva": si.findtext("DueDate") or "",
            "summa": summa, "avoimena": avoin, "vapaa_teksti": teksti,
            "tila_netvisor": si.findtext("InvoiceStatus") or "",
        })

    df = pd.DataFrame(rivit)
    if df.empty:
        return df
    df["lasku_pvm"] = pd.to_datetime(df["lasku_pvm"], errors="coerce")
    df["erapaiva"]  = pd.to_datetime(df["erapaiva"], errors="coerce")
    df["summa"]     = pd.to_numeric(df["summa"], errors="coerce").fillna(0)
    df["avoimena"]  = pd.to_numeric(df["avoimena"], errors="coerce").fillna(0)
    if projekti_hakusana:
        df = df[df["vapaa_teksti"].str.lower().str.contains(projekti_hakusana.lower(), na=False)]
    return df.reset_index(drop=True)
