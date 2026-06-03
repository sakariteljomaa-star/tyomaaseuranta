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
