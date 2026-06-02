"""
Tallennus — automaattinen pilvi/paikallinen valinta:
  - Paikallinen: JSON-tiedostot data/-kansiossa
  - Pilvi (Streamlit Cloud + Supabase): storage_supabase.py
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
try:
    DATA_DIR.mkdir(exist_ok=True)
except Exception:
    # Streamlit Cloud: lähdekoodi on read-only — käytä /tmp
    DATA_DIR = Path("/tmp/tyomaaseuranta_data")
    DATA_DIR.mkdir(exist_ok=True)


# ── Tunnistus: pilvi vai paikallinen ──────────────────────────────────────────

def _pilvessa() -> bool:
    try:
        from storage_supabase import on_pilvessa
        return on_pilvessa()
    except Exception:
        return False


# ── Paikalliset apufunktiot ───────────────────────────────────────────────────

def _slug(projekti: str) -> str:
    s = projekti.lower().strip()
    s = re.sub(r"[^a-z0-9äöå]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "projekti"


def _polku(projekti: str) -> Path:
    return DATA_DIR / f"{_slug(projekti)}.json"


def _lataa_json(projekti: str) -> dict:
    p = _polku(projekti)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _tallenna_json(projekti: str, data: dict) -> None:
    p = _polku(projekti)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


# ── Julkiset funktiot (sama rajapinta riippumatta tallennustavasta) ────────────

def lataa_ali_tunnit(projekti: str) -> list:
    if _pilvessa():
        from storage_supabase import lataa_projekti
        return lataa_projekti(projekti, "ali_tunnit")
    return _lataa_json(projekti).get("ali_tunnit", [])


def tallenna_ali_tunnit(projekti: str, rivit: list) -> None:
    if _pilvessa():
        from storage_supabase import tallenna_projekti
        tallenna_projekti(projekti, "ali_tunnit", rivit)
    else:
        data = _lataa_json(projekti)
        data["ali_tunnit"] = rivit
        _tallenna_json(projekti, data)


def lataa_tuntiseuranta(projekti: str) -> list:
    if _pilvessa():
        from storage_supabase import lataa_projekti
        return lataa_projekti(projekti, "tuntiseuranta")
    return _lataa_json(projekti).get("tuntiseuranta", [])


def tallenna_tuntiseuranta(projekti: str, viikot: list) -> None:
    if _pilvessa():
        from storage_supabase import tallenna_projekti
        tallenna_projekti(projekti, "tuntiseuranta", viikot)
    else:
        data = _lataa_json(projekti)
        data["tuntiseuranta"] = viikot
        _tallenna_json(projekti, data)


def lataa_palkat(projekti: str) -> list:
    if _pilvessa():
        from storage_supabase import lataa_projekti
        return lataa_projekti(projekti, "palkat")
    return _lataa_json(projekti).get("palkat", [])


def tallenna_palkat(projekti: str, rivit: list) -> None:
    if _pilvessa():
        from storage_supabase import tallenna_projekti
        tallenna_projekti(projekti, "palkat", rivit)
    else:
        data = _lataa_json(projekti)
        data["palkat"] = rivit
        _tallenna_json(projekti, data)


def hae_projektit() -> list:
    """Palauttaa tallennettujen projektien nimet."""
    if _pilvessa():
        from storage_supabase import hae_projektit as _hp
        return _hp()
    return [p.stem for p in DATA_DIR.glob("*.json") if not p.name.startswith("_")]


# ── Projektirekisteri ──────────────────────────────────────────────────────────

def lataa_projektirekisteri() -> list:
    """Palauttaa kaikki projektit koodeineen."""
    if _pilvessa():
        from storage_supabase import lataa_globaali
        return lataa_globaali("projektirekisteri")
    polku = DATA_DIR / "_projektirekisteri.json"
    if polku.exists():
        import json
        return json.loads(polku.read_text(encoding="utf-8"))
    return []


def tallenna_projektirekisteri(projektit: list) -> None:
    if _pilvessa():
        from storage_supabase import tallenna_globaali
        tallenna_globaali("projektirekisteri", projektit)
    else:
        import json
        polku = DATA_DIR / "_projektirekisteri.json"
        polku.write_text(json.dumps(projektit, ensure_ascii=False, indent=2), encoding="utf-8")


def hae_projekti_koodilla(koodi: str):
    """Palauttaa projektin dict:n koodin perusteella tai None."""
    for p in lataa_projektirekisteri():
        if p.get("koodi", "").upper() == koodi.upper():
            return p
    return None


def tallenna_projekti_yhteenveto(projekti_nimi: str, yhteenveto: dict) -> None:
    """Tallentaa valmistuneen projektin yhteenvedon historiatietokantaan."""
    if _pilvessa():
        from storage_supabase import tallenna_projekti
        tallenna_projekti(projekti_nimi, "yhteenveto", [yhteenveto])
    else:
        data = _lataa_json(projekti_nimi)
        data["yhteenveto"] = yhteenveto
        _tallenna_json(projekti_nimi, data)


# ── Ammattinimikkeet ───────────────────────────────────────────────────────────

def lataa_ammattinimikkeet() -> list:
    if _pilvessa():
        from storage_supabase import lataa_globaali
        return lataa_globaali("ammattinimikkeet")
    polku = DATA_DIR / "_ammattinimikkeet.json"
    if polku.exists():
        import json
        return json.loads(polku.read_text(encoding="utf-8"))
    # Oletukset
    return [
        {"nimike": "RAM",             "kuvaus": "Rakennusammattimiehen", "tuntihinta": 45.0},
        {"nimike": "RM",              "kuvaus": "Rakennusmies",          "tuntihinta": 40.0},
        {"nimike": "Purkutyöntekijä", "kuvaus": "",                      "tuntihinta": 38.0},
        {"nimike": "Siistijä",        "kuvaus": "",                      "tuntihinta": 35.0},
        {"nimike": "Apumies",         "kuvaus": "",                      "tuntihinta": 33.0},
    ]


def tallenna_ammattinimikkeet(nimikkeet: list) -> None:
    if _pilvessa():
        from storage_supabase import tallenna_globaali
        tallenna_globaali("ammattinimikkeet", nimikkeet)
    else:
        import json
        polku = DATA_DIR / "_ammattinimikkeet.json"
        polku.write_text(json.dumps(nimikkeet, ensure_ascii=False, indent=2), encoding="utf-8")


def lataa_projekti_yhteenveto(projekti_nimi: str) -> dict:
    if _pilvessa():
        from storage_supabase import lataa_projekti
        tulokset = lataa_projekti(projekti_nimi, "yhteenveto")
        return tulokset[0] if tulokset else {}
    data = _lataa_json(projekti_nimi)
    return data.get("yhteenveto", {})
