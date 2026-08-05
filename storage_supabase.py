"""
Supabase-tallennus suorilla REST-kutsuilla (PostgREST API).

EI käytä raskasta supabase-py -kirjastoa — vain `requests`. Tämä välttää
kaikki supabase/httpx/gotrue/pydantic-versioristiriidat Streamlit Cloudissa.

Supabase-taulut (luotu jo SQL Editorissa):
    projekti_data (projekti text, avain text, data jsonb, unique(projekti,avain))
    globaali_data (avain text primary key, data jsonb)
"""

import json
import streamlit as st
import requests


def _conf():
    """Palauttaa (base_url, headers) tai (None, None) jos ei konfiguroitu."""
    try:
        url = st.secrets["supabase"]["url"].rstrip("/")
        key = st.secrets["supabase"]["key"]
    except Exception:
        return None, None
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    return f"{url}/rest/v1", headers


def on_pilvessa() -> bool:
    base, _ = _conf()
    return base is not None


# ── Projektikohtainen data ─────────────────────────────────────────────────────

def lataa_projekti(projekti: str, avain: str) -> list:
    base, headers = _conf()
    if not base:
        return []
    try:
        r = requests.get(
            f"{base}/projekti_data",
            headers=headers,
            params={"select": "data", "projekti": f"eq.{projekti}", "avain": f"eq.{avain}"},
            timeout=10,
        )
        r.raise_for_status()
        rivit = r.json()
        if rivit:
            d = rivit[0]["data"]
            return d if isinstance(d, list) else json.loads(d)
    except Exception as e:
        st.error(f"Supabase-lukuvirhe ({avain}): {e}")
    return []


def tallenna_projekti(projekti: str, avain: str, data: list):
    base, headers = _conf()
    if not base:
        return
    try:
        h = dict(headers)
        h["Prefer"] = "resolution=merge-duplicates"
        r = requests.post(
            f"{base}/projekti_data",
            headers=h,
            params={"on_conflict": "projekti,avain"},
            data=json.dumps({"projekti": projekti, "avain": avain, "data": data}),
            timeout=10,
        )
        r.raise_for_status()
    except Exception as e:
        st.error(f"Supabase-tallennusvirhe ({avain}): {e}")


# ── Globaali data ──────────────────────────────────────────────────────────────

def lataa_globaali(avain: str) -> list:
    base, headers = _conf()
    if not base:
        return []
    try:
        r = requests.get(
            f"{base}/globaali_data",
            headers=headers,
            params={"select": "data", "avain": f"eq.{avain}"},
            timeout=10,
        )
        r.raise_for_status()
        rivit = r.json()
        if rivit:
            d = rivit[0]["data"]
            return d if isinstance(d, list) else json.loads(d)
    except Exception as e:
        st.error(f"Supabase-lukuvirhe ({avain}): {e}")
    return []


def tallenna_globaali(avain: str, data: list) -> bool:
    base, headers = _conf()
    if not base:
        return False
    try:
        h = dict(headers)
        h["Prefer"] = "resolution=merge-duplicates"
        r = requests.post(
            f"{base}/globaali_data",
            headers=h,
            params={"on_conflict": "avain"},
            data=json.dumps({"avain": avain, "data": data}),
            timeout=10,
        )
        if r.status_code >= 400:
            st.session_state["_sb_virhe"] = f"HTTP {r.status_code}: {r.text[:200]}"
            st.error(f"Supabase-tallennusvirhe ({avain}): {r.status_code} — {r.text[:200]}")
            return False
        return True
    except Exception as e:
        st.session_state["_sb_virhe"] = str(e)
        st.error(f"Supabase-tallennusvirhe ({avain}): {e}")
        return False


# ── Toimintaloki ───────────────────────────────────────────────────────────────

def lisaa_loki(rivi: dict) -> bool:
    """Lisää yhden lokirivin loki-tauluun. aika täytetään palvelimella (default now())."""
    base, headers = _conf()
    if not base:
        return False
    try:
        r = requests.post(f"{base}/loki", headers=headers,
                          data=json.dumps(rivi), timeout=10)
        return r.status_code < 400
    except Exception:
        return False  # loki ei saa koskaan kaataa sovellusta


def hae_loki(rajoitus: int = 500) -> list:
    base, headers = _conf()
    if not base:
        return []
    try:
        r = requests.get(f"{base}/loki", headers=headers,
                         params={"select": "*", "order": "aika.desc", "limit": str(rajoitus)},
                         timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


# ── Tiedostot (Supabase Storage) ───────────────────────────────────────────────
#
# Bucket "tyomaakuvat" luodaan kerran Supabasen hallintapaneelissa:
#   Storage → New bucket → nimi: tyomaakuvat → Private (EI public).
# Secret-avain ohittaa Storage-RLS:n kuten muutkin taulut — ei policyjä tarvita.

BUCKET = "tyomaakuvat"


def _storage_conf():
    try:
        url = st.secrets["supabase"]["url"].rstrip("/")
        key = st.secrets["supabase"]["key"]
    except Exception:
        return None, None
    return f"{url}/storage/v1", {"apikey": key, "Authorization": f"Bearer {key}"}


def tallenna_tiedosto(polku: str, sisalto: bytes,
                      mime: str = "application/octet-stream") -> bool:
    base, headers = _storage_conf()
    if not base:
        return False
    try:
        h = dict(headers)
        h["Content-Type"] = mime
        h["x-upsert"] = "true"
        r = requests.post(f"{base}/object/{BUCKET}/{polku}", headers=h,
                          data=sisalto, timeout=30)
        if r.status_code >= 400:
            st.error(f"Storage-tallennusvirhe ({polku}): {r.status_code} — {r.text[:200]}")
            return False
        return True
    except Exception as e:
        st.error(f"Storage-tallennusvirhe ({polku}): {e}")
        return False


def lataa_tiedosto(polku: str):
    """Palauttaa tiedoston sisällön (bytes) tai None."""
    base, headers = _storage_conf()
    if not base:
        return None
    try:
        r = requests.get(f"{base}/object/{BUCKET}/{polku}", headers=headers, timeout=30)
        if r.status_code >= 400:
            return None
        return r.content
    except Exception:
        return None


def listaa_tiedostot(etuliite: str) -> list:
    """Listaa tiedostopolut annetun 'kansion' alla (rekursiivisesti)."""
    base, headers = _storage_conf()
    if not base:
        return []

    def _listaa(prefix: str, syvyys: int = 0) -> list:
        if syvyys > 4:
            return []
        try:
            r = requests.post(
                f"{base}/object/list/{BUCKET}", headers=headers,
                json={"prefix": prefix, "limit": 1000,
                      "sortBy": {"column": "name", "order": "asc"}},
                timeout=30,
            )
            if r.status_code >= 400:
                return []
            polut = []
            for kohde in r.json():
                nimi = kohde.get("name", "")
                koko_polku = f"{prefix}/{nimi}" if prefix else nimi
                if kohde.get("id"):          # tiedosto
                    polut.append(koko_polku)
                else:                        # alikansio
                    polut.extend(_listaa(koko_polku, syvyys + 1))
            return polut
        except Exception:
            return []

    return _listaa(etuliite.strip("/"))


def poista_tiedosto(polku: str) -> bool:
    base, headers = _storage_conf()
    if not base:
        return False
    try:
        r = requests.delete(f"{base}/object/{BUCKET}/{polku}", headers=headers, timeout=30)
        return r.status_code < 400
    except Exception:
        return False


# ── Projektilista ──────────────────────────────────────────────────────────────

def hae_projektit() -> list:
    base, headers = _conf()
    if not base:
        return []
    try:
        r = requests.get(
            f"{base}/projekti_data",
            headers=headers,
            params={"select": "projekti"},
            timeout=10,
        )
        r.raise_for_status()
        return sorted(set(row["projekti"] for row in r.json()))
    except Exception:
        return []
