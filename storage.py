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


def lukuvirhe(avain: str, projekti: str = "") -> bool:
    """True jos tiedon viimeisin luku pilvestä epäonnistui (tyhjä lista ei ole luotettava)."""
    if not _pilvessa():
        return False
    from storage_supabase import lukuvirhe as _lv
    return _lv(f"{projekti}/{avain}" if projekti else avain)


def tallennustila() -> str:
    """Palauttaa 'pilvi' tai 'paikallinen' — kertoo säilyykö data restartissa."""
    return "pilvi" if _pilvessa() else "paikallinen"


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


def lataa_projekti_avain(projekti: str, avain: str) -> list:
    """Yleiskäyttöinen projektikohtaisen datan luku (esim. asbesti_dok)."""
    if _pilvessa():
        from storage_supabase import lataa_projekti
        return lataa_projekti(projekti, avain)
    return _lataa_json(projekti).get(avain, [])


def tallenna_projekti_avain(projekti: str, avain: str, data: list) -> None:
    if _pilvessa():
        from storage_supabase import tallenna_projekti
        tallenna_projekti(projekti, avain, data)
    else:
        d = _lataa_json(projekti)
        d[avain] = data
        _tallenna_json(projekti, d)


def lataa_globaali(avain: str) -> list:
    """Globaali (ei-projektikohtainen) data, esim. kalustorekisteri."""
    if _pilvessa():
        from storage_supabase import lataa_globaali as _lg
        return _lg(avain)
    polku = DATA_DIR / f"_{avain}.json"
    if polku.exists():
        return json.loads(polku.read_text(encoding="utf-8"))
    return []


def tallenna_globaali(avain: str, data: list) -> None:
    if _pilvessa():
        from storage_supabase import tallenna_globaali as _tg
        _tg(avain, data)
    else:
        polku = DATA_DIR / f"_{avain}.json"
        polku.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


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


# ── Tiedostot (kuvat ja liitteet) ──────────────────────────────────────────────
#
# Pilvessä: Supabase Storage -bucket "tyomaakuvat" (ks. storage_supabase.py).
# Paikallisesti: data/kuvat/-kansio.
# Polkukäytäntö: <työnumero>/<vaihe>/<aikaleima>_<juokseva>.jpg

KUVA_DIR = DATA_DIR / "kuvat"


def tiedosto_slug(osa: str) -> str:
    """Siivoaa polun osan tiedostojärjestelmälle turvalliseksi."""
    s = re.sub(r"[^A-Za-z0-9äöåÄÖÅ._-]", "_", str(osa).strip())
    return re.sub(r"_+", "_", s).strip("._") or "x"


def tallenna_tiedosto(polku: str, sisalto: bytes,
                      mime: str = "application/octet-stream") -> bool:
    if _pilvessa():
        from storage_supabase import tallenna_tiedosto as _tt
        return _tt(polku, sisalto, mime)
    p = KUVA_DIR / polku
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(sisalto)
    return True


def lataa_tiedosto(polku: str):
    """Palauttaa tiedoston sisällön (bytes) tai None jos ei löydy."""
    if _pilvessa():
        from storage_supabase import lataa_tiedosto as _lt
        return _lt(polku)
    p = KUVA_DIR / polku
    return p.read_bytes() if p.exists() else None


def listaa_tiedostot(etuliite: str) -> list:
    """Listaa tiedostopolut annetun etuliitteen (kansion) alta."""
    if _pilvessa():
        from storage_supabase import listaa_tiedostot as _lf
        return _lf(etuliite)
    juuri = KUVA_DIR / etuliite
    if not juuri.exists():
        return []
    return sorted(str(p.relative_to(KUVA_DIR)) for p in juuri.rglob("*") if p.is_file())


def poista_tiedosto(polku: str) -> bool:
    if _pilvessa():
        from storage_supabase import poista_tiedosto as _pt
        return _pt(polku)
    p = KUVA_DIR / polku
    if p.exists():
        p.unlink()
        return True
    return False


def pakkaa_kuva(sisalto: bytes, max_sivu: int = 1600, laatu: int = 80) -> bytes:
    """Pakkaa kuvan puhelinkäyttöä varten JPEG-muotoon (pisin sivu max_sivu px)."""
    try:
        import io
        from PIL import Image, ImageOps
        img = Image.open(io.BytesIO(sisalto))
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.thumbnail((max_sivu, max_sivu))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=laatu)
        return buf.getvalue()
    except Exception:
        return sisalto  # jos pakkaus epäonnistuu, tallenna alkuperäinen


def lataa_projekti_yhteenveto(projekti_nimi: str) -> dict:
    if _pilvessa():
        from storage_supabase import lataa_projekti
        tulokset = lataa_projekti(projekti_nimi, "yhteenveto")
        return tulokset[0] if tulokset else {}
    data = _lataa_json(projekti_nimi)
    return data.get("yhteenveto", {})
