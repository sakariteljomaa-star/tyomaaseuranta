# Komponentti: Työmaaseuranta

Tämä repositorio on **yksi komponentti** mikroyrityksen kokonaisvaltaisessa
järjestelmässä. Tämä tiedosto kuvaa komponentin roolin, rajapinnat ja
integrointimahdollisuudet muihin osiin.

---

## Yleiskuvaus

**Repo:** `https://github.com/sakariteljomaa-star/tyomaaseuranta` (monorepo, branch `main`)

**Mitä tekee:** Rakennustyömaiden kustannus-, tunti- ja kalustoseuranta.
Kolme Streamlit-sovellusta samassa repossa, jaettu käyttäjähallinta ja tallennus.

**Yritys:** Uudenmaan Asbestipurku Oy / Uudenmaan Vahinkopalvelu Oy (Y-tunnus 2817254-1).
Toiminta: asbestipurku, vahinkosaneeraus, rakentamisen aliurakointi.

---

## Sovellukset (entry pointit)

| Osa | Tiedosto | Tarkoitus | Käyttäjät |
|-----|----------|-----------|-----------|
| 💰 Kustannusseuranta | `app.py` | Netvisor-kulut → luokittelu → Excel | työnjohto, kirjanpito |
| 👷 Tuntikirja | `ali_app.py` | Aliurakoitsijatunnit + hyväksyntä (fi/ru) | työnjohto, työntekijät |
| 🔧 Kalustoseuranta | `kalusto_app.py` | QR-pohjainen laitekirjanpito | kaikki työmaalla |

Kaikki kolme julkaistaan samasta reposta eri **Main file path** -asetuksella
(Streamlit Community Cloud).

---

## Teknologia

- **Python + Streamlit** — UI ja sovelluslogiikka
- **Supabase** (PostgreSQL, EU/Frankfurt) — tallennus REST-rajapinnan kautta (`requests`)
- **Streamlit Community Cloud** — hosting (kolme erillistä appia)
- Ei raskaita riippuvuuksia (ei supabase-py:tä — suorat REST-kutsut versioristiriitojen välttämiseksi)

---

## Ulkoiset riippuvuudet

| Riippuvuus | Käyttö | Pakollinen? |
|------------|--------|-------------|
| Supabase-projekti (secret-avain) | Tallennus | Kyllä (pilvessä) |
| Streamlit Cloud | Hosting | Kyllä (julkaistuna) |
| Netvisor API | Kulujen automaattihaku | Ei (valinnainen) |

Salaisuudet vain Streamlit Secretsissä, ei koskaan koodissa/GitHubissa
(`.gitignore` suojaa `secrets.toml` + `data/`).

---

## Integraatiopinnat kokonaisjärjestelmään

Nämä osat ovat uudelleenkäytettävissä tai yhtenäistettävissä muiden moduulien kanssa:

### 1. Käyttäjähallinta — `auth.py`
- PBKDF2-HMAC-SHA256-salasanat, 4 roolia (admin / tyonjohtaja / tyontekija / katselija)
- Käyttäjät Supabasen `globaali_data.kayttajat`-avaimessa
- **Voidaan laajentaa koko yrityksen keskitetyksi kirjautumiseksi** — sama rekisteri
  palvelisi muitakin moduuleja (CRM, laskutus, jne.).
- Julkinen rajapinta: `kirjaudu_gate()`, `voi_hyvaksya()`, `voi_hallita_kayttajia()`,
  `nakee_kaikki_projektit()`, `nayta_kayttajahallinta()`.

### 2. Tallennus — `storage.py` + `storage_supabase.py`
- Abstraktio: pilvi (Supabase) tai paikallinen (JSON) — valinta automaattinen.
- **Sama Supabase-instanssi voi palvella kaikkia moduuleja** eri tauluilla.
- Julkinen rajapinta: `lataa_globaali()`, `tallenna_globaali()`,
  `lataa_projekti()` / `tallenna_projekti()` (avain-arvo JSONB), `tallennustila()`.

### 3. Toimintaloki — `loki.py`
- Yhteinen `loki`-taulu (kuka, mitä, milloin, mikä sovellus).
- **Sama loki voi kattaa kaikki yritysjärjestelmän moduulit** — vain `sovellus`-kenttä vaihtuu.
- Rajapinta: `kirjaa(kayttaja, sovellus, toiminto, kohde)`, `hae(rajoitus)`.

### 4. Netvisor-integraatio — `netvisor_api.py`
- MAC/SHA256-tunnistus + XML-parsinta (ostot, myynti, tuntikirjanpito).
- **Tunnistuslogiikka uudelleenkäytettävissä** muissa talousmoduuleissa (laskutus, kirjanpito).

### 5. Brändi — `brand/`, `brandi.py`, `.streamlit/config.toml`
- UAP-merkki (SVG/PNG) ja brändikirja `brand/BRANDIKIRJA.md`; teema (värit + omat fontit
  `static/fonts/`) ja `brandi.sivun_asetukset()` / `brandi.ylatunniste()` kaikissa sovelluksissa;
  kopioitavissa muihinkin moduuleihin.

---

## Tallennusrakenne (Supabase)

```sql
projekti_data (projekti text, avain text, data jsonb, unique(projekti,avain))
globaali_data (avain text primary key, data jsonb)
loki          (id bigserial, aika timestamptz, kayttaja, rooli, sovellus, toiminto, kohde)
```

- Projektikohtainen data → `projekti_data` (ali_tunnit, tuntiseuranta, palkat, yhteenveto)
- Globaali data → `globaali_data` (kayttajat, projektirekisteri, ammattinimikkeet, kalusto_*)
- RLS päällä; secret-avain ohittaa. Sama avain kaikkien 3 appin Secretseissä.

---

## Suositukset kokonaisjärjestelmää rakennettaessa

1. **Yksi käyttäjärekisteri** koko yritykselle (`auth.py` + `globaali_data.kayttajat`).
2. **Yksi Supabase** kaikille moduuleille, eri taulut per moduuli.
3. **Yksi toimintaloki** (`loki`-taulu), `sovellus`-kenttä erottaa moduulit.
4. **Netvisor keskitetysti** — `netvisor_api.py` pohjaksi talousintegraatioille.
5. **Yhtenäinen brändi** — jaettu logo/favicon.

---

## Käyttöönotto uudessa ympäristössä

1. `git clone https://github.com/sakariteljomaa-star/tyomaaseuranta.git`
2. Luo Supabase-projekti + taulut (SQL: ks. `CLAUDE.md` kohta 9 ja `loki.py`)
3. Julkaise Streamlit Cloudiin (3 appia, eri Main file path) — ks. `CLAUDE.md` kohta 11
4. Lisää Streamlit Secrets (`[supabase]` secret-avain; valinnainen `[netvisor]`)
5. Ensikäynnistys luo pääkäyttäjän

---

## Muu dokumentaatio repossa

| Tiedosto | Sisältö |
|----------|---------|
| `JARJESTELMAKARTTA.md` | Visuaalinen yleiskuva (kaaviot) |
| `CLAUDE.md` | Tekninen kehitysohje + säännöt |
| `KÄYTTÖOHJE.md` | Loppukäyttäjän opas |
| `TIETOTURVA.md` | Avainten hallinta, roolit, vuototilanteet |
| `TIETOSUOJASELOSTE.md` | GDPR-seloste |
