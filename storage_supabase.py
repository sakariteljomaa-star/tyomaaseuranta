"""
Supabase-pohjainen tallennus — käytetään kun sovellus pyörii Streamlit Cloudissa.
Paikallisesti käytetään storage.py:n JSON-tallennusta.

Supabase-taulut (aja SQL Supabasen SQL Editorissa):

    create table projekti_data (
      id          bigserial primary key,
      projekti    text not null,
      avain       text not null,
      data        jsonb not null default '[]',
      paivitetty  timestamptz default now(),
      unique (projekti, avain)
    );

    create table globaali_data (
      avain       text primary key,
      data        jsonb not null default '[]',
      paivitetty  timestamptz default now()
    );
"""

import streamlit as st
import json


def _client():
    """Luo Supabase-yhteyden Streamlit Secretsistä."""
    from supabase import create_client
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


def on_pilvessa() -> bool:
    """Tarkistaa onko Supabase-tunnukset konfigurattu."""
    try:
        return "supabase" in st.secrets and bool(st.secrets["supabase"].get("url"))
    except Exception:
        return False


# ── Projektikohtainen data ─────────────────────────────────────────────────────

def lataa_projekti(projekti: str, avain: str) -> list:
    try:
        sb = _client()
        tulos = (sb.table("projekti_data")
                   .select("data")
                   .eq("projekti", projekti)
                   .eq("avain", avain)
                   .execute())
        if tulos.data:
            d = tulos.data[0]["data"]
            return d if isinstance(d, list) else json.loads(d)
    except Exception as e:
        st.error(f"Supabase-lukuvirhe ({avain}): {e}")
    return []


def tallenna_projekti(projekti: str, avain: str, data: list):
    try:
        sb = _client()
        (sb.table("projekti_data")
           .upsert({"projekti": projekti, "avain": avain, "data": data},
                   on_conflict="projekti,avain")
           .execute())
    except Exception as e:
        st.error(f"Supabase-tallennusvirhe ({avain}): {e}")


# ── Globaali data (ei projektikohtainen) ──────────────────────────────────────

def lataa_globaali(avain: str) -> list:
    try:
        sb = _client()
        tulos = (sb.table("globaali_data")
                   .select("data")
                   .eq("avain", avain)
                   .execute())
        if tulos.data:
            d = tulos.data[0]["data"]
            return d if isinstance(d, list) else json.loads(d)
    except Exception as e:
        st.error(f"Supabase-lukuvirhe ({avain}): {e}")
    return []


def tallenna_globaali(avain: str, data: list):
    try:
        sb = _client()
        (sb.table("globaali_data")
           .upsert({"avain": avain, "data": data})
           .execute())
    except Exception as e:
        st.error(f"Supabase-tallennusvirhe ({avain}): {e}")


# ── Projektilista ──────────────────────────────────────────────────────────────

def hae_projektit() -> list[str]:
    try:
        sb = _client()
        tulos = (sb.table("projekti_data")
                   .select("projekti")
                   .execute())
        return sorted(set(r["projekti"] for r in tulos.data))
    except Exception:
        return []
