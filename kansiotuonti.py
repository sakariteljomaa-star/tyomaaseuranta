"""
Lukee Netvisor-XLSX-tiedostot suoraan kansiosta.
Tunnistaa tiedostotyypin automaattisesti sisällön perusteella.
"""

import os
from pathlib import Path
from datetime import datetime
import pandas as pd


def _tunnista_tyyppi(polku: str) -> str:
    """Tunnistaa Netvisor-viennin tyypin ensimmäisen otsikko/datasolun perusteella."""
    try:
        df = pd.read_excel(polku, sheet_name=0, header=None, nrows=5)
        teksti = " ".join(str(v) for v in df.values.flatten() if pd.notna(v)).lower()
        if "laskunumero" in teksti or "myyntireskont" in teksti:
            return "myynti"
        if "palkansaaja" in teksti or "tuntikirjanpito" in teksti or "normaali tuntityö" in teksti:
            return "tunnit"
        if "päiväys" in teksti and "tositelaji" in teksti and "debet" in teksti:
            return "ostot"
    except Exception:
        pass
    return "tuntematon"


def lue_kansio(kansio: str) -> dict:
    """
    Lukee kaikki .xlsx-tiedostot kansiosta.

    Palauttaa:
      {
        "ostot":  [(polku, muokattu, df), ...],
        "myynti": [(polku, muokattu, df), ...],
        "tunnit": [(polku, muokattu, df), ...],
        "virheet": [(polku, virhe), ...],
      }
    """
    kansio_p = Path(kansio)
    tulos = {"ostot": [], "myynti": [], "tunnit": [], "tuntematon": [], "virheet": []}

    if not kansio_p.exists() or not kansio_p.is_dir():
        return tulos

    tiedostot = sorted(
        kansio_p.glob("*.xlsx"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,  # uusimmat ensin
    )

    for p in tiedostot:
        try:
            tyyppi = _tunnista_tyyppi(str(p))
            muokattu = datetime.fromtimestamp(p.stat().st_mtime).strftime("%d.%m.%Y %H:%M")
            tulos[tyyppi].append((str(p), muokattu, p.name))
        except Exception as e:
            tulos["virheet"].append((p.name, str(e)))

    return tulos


def oletus_kansio() -> str:
    """Palauttaa järkevän oletuskansion."""
    vaihtoehdot = [
        Path.home() / "Downloads",
        Path.home() / "Desktop",
    ]
    for v in vaihtoehdot:
        if v.exists():
            return str(v)
    return str(Path.home())
