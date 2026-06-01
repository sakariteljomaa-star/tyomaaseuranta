"""
Tallennus — automaattinen pilvi/paikallinen valinta:
  - Paikallinen: JSON-tiedostot data/-kansiossa
  - Pilvi (Streamlit Cloud + Supabase): storage_supabase.py
"""

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
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
