"""
Toimintaloki — kuka teki mitä ja milloin.

Pilvessä: Supabase-taulu `loki` (yksi rivi per tapahtuma).
Paikallisesti: data/_loki.json.

Loki ei KOSKAAN kaada sovellusta — kaikki kääritty try/exceptiin.

Supabase-taulu (aja SQL Editorissa):
    create table loki (
      id bigserial primary key,
      aika timestamptz default now(),
      kayttaja text,
      rooli text,
      sovellus text,
      toiminto text,
      kohde text
    );
"""

import json
import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
_LOKI_POLKU = DATA_DIR / "_loki.json"


def _pilvessa() -> bool:
    try:
        from storage_supabase import on_pilvessa
        return on_pilvessa()
    except Exception:
        return False


def kirjaa(kayttaja: dict, sovellus: str, toiminto: str, kohde: str = ""):
    """Kirjaa tapahtuman lokiin. kayttaja = session_staten käyttäjä-dict (tai {})."""
    try:
        rivi = {
            "kayttaja": (kayttaja or {}).get("tunnus", "?"),
            "rooli":    (kayttaja or {}).get("rooli", ""),
            "sovellus": sovellus,
            "toiminto": toiminto,
            "kohde":    kohde,
        }
        if _pilvessa():
            from storage_supabase import lisaa_loki
            lisaa_loki(rivi)
        else:
            try:
                DATA_DIR.mkdir(exist_ok=True)
                loki = json.loads(_LOKI_POLKU.read_text(encoding="utf-8")) if _LOKI_POLKU.exists() else []
            except Exception:
                loki = []
            rivi["aika"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            loki.append(rivi)
            loki = loki[-2000:]  # rajaa paikallisen lokin koko
            _LOKI_POLKU.write_text(json.dumps(loki, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass  # loki ei saa koskaan rikkoa toimintoa


def hae(rajoitus: int = 500) -> list:
    try:
        if _pilvessa():
            from storage_supabase import hae_loki
            return hae_loki(rajoitus)
        if _LOKI_POLKU.exists():
            loki = json.loads(_LOKI_POLKU.read_text(encoding="utf-8"))
            return list(reversed(loki))[:rajoitus]
    except Exception:
        pass
    return []
