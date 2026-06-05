# Järjestelmäkartta — Työmaaseuranta

Uudenmaan Asbestipurku Oy. Yleiskuva: kolme sovellusta, yhteinen tallennus ja käyttäjähallinta.

---

## 1. Yleiskuva

```
                         ┌───────────────────────────────┐
                         │   KÄYTTÄJÄT (selain/puhelin)   │
                         └───────────────┬───────────────┘
                                         │ kirjautuminen (rooli)
         ┌───────────────────────────────┼───────────────────────────────┐
         │                                │                                │
 ┌───────▼────────┐              ┌────────▼────────┐              ┌────────▼────────┐
 │ 💰 KUSTANNUS-  │              │ 👷 TUNTIKIRJA   │              │ 🔧 KALUSTO-     │
 │   SEURANTA     │              │  (ali_app.py)   │              │   SEURANTA      │
 │   (app.py)     │              │                 │              │ (kalusto_app.py)│
 └───────┬────────┘              └────────┬────────┘              └────────┬────────┘
         │                                │                                │
         └───────────────────────────────┼────────────────────────────────┘
                                          │  yhteinen rajapinta
                            ┌─────────────▼─────────────┐
                            │  auth.py  ·  storage.py   │
                            │  loki.py                  │
                            └─────────────┬─────────────┘
                                          │
                            ┌─────────────▼─────────────┐
                            │   SUPABASE (PostgreSQL, EU)│
                            │   projekti_data · globaali_│
                            │   data · loki              │
                            └───────────────────────────┘
```

---

## 2. Kolme sovellusta

### 💰 Kustannusseuranta — `app.py`
**Kenelle:** työnjohto, kirjanpito (EI työntekijät — palkkatiedot)
**Mitä:** Netvisor-kulujen ja myynnin seuranta, kustannusseuranta-Excel

```
Välilehdet:
 📊 Yhteenveto        — kokonaiskuva, ALV-kohtelu
 💰 Myynti            — myyntilaskut (reskontra TAI laskentakohderaportti)
 ⏱️ Tuntiseuranta     — omien työntekijöiden tunnit (Netvisor)
 📋 Ali-tuntikirja    — aliurakoitsijatunnit (tuntikirjasta)
 💼 Palkkakustannukset— brutto × kerroin
 🛒 Ostot             — materiaalit (KOOS)
 🗑️ Jätemaksut        — Kuljetusrinki/Labroc (KOOS)
 👷 Aliurakoitsijat   — ostopalvelut (RAOS)
 🔧 Kalusto           — konevuokra
 📋 Kaikki rivit      — yhdistetty + suodatus
 👤 Käyttäjät (admin) — käyttäjähallinta + loki

Datalähteet: Netvisor-XLSX-lataus välilehdittäin TAI 🔄 Netvisor API
```

### 👷 Tuntikirja — `ali_app.py`
**Kenelle:** työnjohto + aliurakoitsijat/työntekijät
**Mitä:** aliurakoitsijoiden tuntien kirjaus, hyväksyntä, viikkoraportti
**Kielet:** 🇫🇮 suomi / 🇷🇺 venäjä

```
Välilehdet (roolin mukaan):
 ⚡ Pikasyöttö        — kaikki tekijät kerralla (puhelinystävällinen)
 👤 Yksittäinen       — yksi tekijä, pikanapit
 📊 Viikkoyhteenveto  — yhteenveto + HYVÄKSYNTÄ (vain TJ) + raportti
 👥 Tekijälista (TJ)  — aliurakoitsijat + ammattinimikkeet
 📁 Projektit (TJ)    — luo projekti + koodi + kustannuspaikat
 📈 Historia (TJ)     — valmiit projektit, tarjouslaskennan apu
 👤 Käyttäjät (admin) — käyttäjähallinta + loki

Hyväksyntä: 🔵 Odottaa → ✅ Hyväksytty (lukitsee) / ⚠️ Selvitys
```

### 🔧 Kalustoseuranta — `kalusto_app.py`
**Kenelle:** hallinta (kirjautuneet) + työmaa (QR, ei kirjautumista)
**Mitä:** QR-pohjainen laitekirjanpito

```
📱 QR-SKANNAUS (julkinen):
   Skannaa tarra → laitekortti → Ota käyttöön / Palauta / Ilmoita vika

🔧 HALLINTA (kirjautunut):
 📊 Tilannekuva       — missä laitteet, viat
 📱 QR-koodit         — tulosta tarrat (3 kokoa, PDF)
 🔧 Laiterekisteri    — kunto, sijainti
 📥 Tuo Excel         — Kalustonhallinta-XLSX
 📋 Tapahtumahistoria — kaikki siirrot
 👤 Käyttäjät (admin) — käyttäjähallinta + loki
```

---

## 3. Roolit (yhteinen kaikille)

| Rooli | Kustannus | Tuntikirja | Kalusto | Käyttäjät |
|-------|:---:|:---:|:---:|:---:|
| 👑 **admin** | ✅ | ✅ | ✅ | ✅ hallitsee |
| 🔑 **tyonjohtaja** | ✅ | ✅ hyväksyy | ✅ hallinta | — |
| 👁️ **katselija** | luku | luku | luku | — |
| 👷 **tyontekija** | 🚫 | omat tunnit | 📱 QR | — |

Yksi tunnus → kaikki kolme. Salasanat PBKDF2-hashattu.

---

## 4. Datan kulku

```
NETVISOR ──► XLSX-vienti / API ──► app.py (parserit) ──► luokittelu ──► näkymä + Excel
                                      │
                                      ├─ parser.py          (laskentakohderaportti → ostot)
                                      ├─ parser_myynti.py   (myyntireskontra TAI laskentakohde)
                                      ├─ parser_tunnit.py   (tuntikirjanpito)
                                      └─ classifier.py      (KOOS/RAOS, Urakka/Lisätyö, jäte/kalusto)

TYÖMAA ──► ali_app.py (käsinsyöttö) ──► hyväksyntä ──► viikkoraportti (Excel/PDF)

TYÖMAA ──► kalusto_app.py (QR-skannaus) ──► tapahtuma ──► tilannekuva

KAIKKI ──► storage.py ──► Supabase (pilvi) / JSON (paikallinen)
```

---

## 5. Tiedostot

| Tiedosto | Tehtävä |
|----------|---------|
| `app.py` | Kustannusseuranta-UI |
| `ali_app.py` | Tuntikirja-UI |
| `kalusto_app.py` | Kalustoseuranta-UI + QR |
| `auth.py` | Käyttäjät, roolit, salasanat (yhteinen) |
| `storage.py` | Tallennuksen rajapinta (pilvi/paikallinen) |
| `storage_supabase.py` | Supabase REST-kutsut |
| `loki.py` | Toimintaloki |
| `classifier.py` | Luokittelusäännöt |
| `parser.py` · `parser_myynti.py` · `parser_tunnit.py` · `parser_kalusto.py` | Netvisor-/Excel-luku |
| `excel_export.py` | Kustannus-Excel |
| `raportti_ali.py` | Aliurakoitsija-viikkoraportti |
| `tarrapohja.py` | QR-konetarrat (PDF) |
| `netvisor_api.py` | Netvisor API -haku |
| `translations.py` | fi/ru-käännökset |
| `kansiotuonti.py` | Kansiolukija (vain paikallinen) |

**Dokumentit:** `CLAUDE.md` (kehitys) · `KÄYTTÖOHJE.md` · `TIETOTURVA.md` · `TIETOSUOJASELOSTE.md` · `JARJESTELMAKARTTA.md`

---

## 6. Tallennus (Supabase)

| Taulu | Sisältö |
|-------|---------|
| `projekti_data` | Projektikohtainen: ali_tunnit, tuntiseuranta, palkat, yhteenveto |
| `globaali_data` | Yhteinen: käyttäjät, projektirekisteri, ammattinimikkeet, kalusto |
| `loki` | Toimintaloki (kirjautumiset, hyväksynnät, muutokset) |

**Avain:** secret-avain (`sb_secret_…`), RLS päällä. Sama avain kaikkien 3 appsin Streamlit Secretseissä.

---

## 7. Luokittelusäännöt (ydin)

```
ALV-tunnus:  KOOS 25,5% (materiaalit/jäte/kalusto, vähennetään)
             RAOS / ALV 0% (aliurakka, käänteinen, ei sivukulukerrointa)

Toimittaja:  Kuljetusrinki/Labroc → AINA Jätemaksut
             RK Konevuokraamo     → Kalusto
             RAOS / "Työ vkoXX"   → Aliurakoitsijat

Laskentakohde:  sisältää "LISÄTYÖT" → Lisätyö, muuten → Urakka
```

Säännöt: `classifier.py` + CLAUDE.md kohta 4.
