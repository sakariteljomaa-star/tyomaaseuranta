# CLAUDE.md — Työmaaseuranta

Tämä tiedosto ohjaa Claude Codea tämän projektin kehityksessä. Lue tämä aina ensin.
Kaikki luokittelu- ja laskentasäännöt ovat tässä — älä keksi niitä uudelleen, vaan
sovella näitä. Jos sääntö muuttuu, päivitä se TÄHÄN tiedostoon (ja `classifier.py`:hyn).

---

## 1. Mikä tämä on

**Kolme erillistä Streamlit-sovellusta** samassa repositoriossa, jaettu yhteinen
tallennus ja käyttäjähallinta:

| Sovellus | Tiedosto | Tarkoitus | Käyttäjät |
|----------|----------|-----------|-----------|
| 💰 **Kustannusseuranta** | `app.py` | Netvisor-viennit → kustannusseuranta-Excel | työnjohto, kirjanpito |
| 👷 **Tuntikirja** | `ali_app.py` | Aliurakoitsijoiden tuntien kirjaus + hyväksyntä | työnjohto, työntekijät |
| 🔧 **Kalustoseuranta** | `kalusto_app.py` | QR-pohjainen laitekirjanpito | kaikki työmaalla |

Yritys: Uudenmaan Asbestipurku Oy / Uudenmaan Vahinkopalvelu Oy (Y-tunnus 2817254-1).
Toiminta: asbestipurku, vahinkosaneeraus, rakentamisen aliurakointi.
Tmi ST Konsultti (Y-tunnus 3376518-1) = työnjohtopalvelut, oma toiminimi.

## 2. Käynnistys

```
# Paikallisesti (ei vaadi Supabasea — käyttää data/-kansion JSON-tiedostoja)
python3 -m streamlit run app.py          --server.port 8501   # Kustannusseuranta
python3 -m streamlit run ali_app.py      --server.port 8502   # Tuntikirja
python3 -m streamlit run kalusto_app.py  --server.port 8503   # Kalustoseuranta
```

Riippuvuudet: `pip install -r requirements.txt`

**Julkaisu:** Streamlit Community Cloud, kolme erillistä appia samasta GitHub-repositoriosta
(`sakariteljomaa-star/tyomaaseuranta`), eri Main file path kullekin. Ks. kohta 11.

## 3. Arkkitehtuuri

| Tiedosto             | Tehtävä                                                       |
|----------------------|--------------------------------------------------------------|
| `app.py`             | Kustannusseuranta-UI (10 välilehteä + Käyttäjät adminille)    |
| `ali_app.py`         | Tuntikirja-UI (roolien mukaiset välilehdet, 2 kieltä)        |
| `kalusto_app.py`     | Kalustoseuranta-UI + julkinen QR-skannausnäkymä              |
| `auth.py`            | Käyttäjähallinta, roolit, PBKDF2-salasanat (YHTEINEN)        |
| `parser.py`          | Netvisor ostolaskut (laskentakohderaportti) → DataFrame      |
| `parser_myynti.py`   | Netvisor myyntireskontra → DataFrame (sarakehaku nimellä)    |
| `parser_tunnit.py`   | Netvisor tuntikirjanpito → DataFrame                         |
| `parser_kalusto.py`  | Kalustonhallinta-XLSX → laiterekisteri                       |
| `classifier.py`      | Ostolaskujen automaattinen luokittelu (SÄÄNNÖT, ks. kohta 4) |
| `excel_export.py`    | Kustannusseuranta-Excelin generointi                         |
| `raportti_ali.py`    | Aliurakoitsija-viikkoraportti (Excel, tulostettava PDF:ksi)  |
| `tarrapohja.py`      | QR-konetarrat A4-arkille (reportlab, 3 kokoa)                |
| `translations.py`    | Käännökset fi/ru (`tr()`-funktio — EI `t()`, ks. kohta 10)   |
| `kansiotuonti.py`    | Lukee Netvisor-XLSX:t kansiosta (vain paikallisesti)         |
| `storage.py`         | Tallennuksen julkinen rajapinta (pilvi/paikallinen valinta)  |
| `storage_supabase.py`| Supabase-tallennus suorilla REST-kutsuilla (requests)        |
| `data/`              | Paikalliset JSON-tallennukset (gitignored)                   |

Suunnitteluperiaate: luokittelulogiikka erillään (`classifier.py`), tallennuslogiikka
erillään (`storage.py`), käyttäjähallinta erillään (`auth.py`).

## 4. Luokittelusäännöt (ydin)

Luokittelu tehdään ensisijaisesti **toimittajan nimen + ALV-tunnuksen** perusteella.

### ALV-käsittely
- **KOOS 25,5 %** = kotimaan ostot: materiaalit, jätemaksut, konevuokra, suojaimet.
  Vähennetään ALV-tilityksessä.
- **RAOS / ALV 0 %** = rakentamispalvelun käänteinen ALV: aliurakoitsijat.
  Ostopalvelu, **ei sivukulukerrointa**.

### Kululajien tunnistus (classifier.py)
- **Kuljetusrinki / Labroc = AINA jäte** (jätemaksut), riippumatta muusta.
- **RK Rakentajan Konevuokraamo = Kalusto** (konevuokra).
- **RAOS-ALV = Aliurakoitsijat.** Myös ALV 0 % + selite alkaa "Työ" tai "aloitus pvm".
- **Sanerakennus Oy** = aina ALV 0 % (käänteinen ALV).
- **Materiaalit / konevuokra / suojaimet** = KOOS 25,5 %.
- **Palkkakirjanpito** = ALV 0 %.

### Laskentakohde erottaa urakan ja lisätyön
- Urakka: laskentakohde "Valteri-koulu Mirlux"
- Lisätyö: laskentakohde sisältää "LISÄTYÖT"
- Yleinen sääntö: laskentakohde-kentän teksti ratkaisee, urakka vs. lisätyö.

## 5. Laskentaparametrit

- Oman työntekijän tuntihinta: **38 €/h** (säädettävissä)
- Aliurakoitsijan tuntihinta: vaihtelee, asetetaan ammattinimikkeen mukaan
- Ammattinimikkeet (oletukset): RAM 45 €, RM 40 €, Purkutyöntekijä 38 €,
  Siistijä 35 €, Apumies 33 € — muokattavissa Tuntikirjan Projektit-välilehdellä
- Maksuehto: **21 pv netto** (eräpäivä = laskutuspvm + 21 pv)
- Palkkakerroin (brutto × kerroin): oletus **1,5** (toteuttava porras 1,6–1,7,
  toimihenkilöt 1,3–1,4)
- Aliurakoitsijalaskut: ALV 0 %, **ei** sivukulukerrointa.

## 6. Kustannusseuranta-Excelin rakenne

Välilehdet generoidaan `excel_export.py`:ssä: Ostot · Jätemaksut · Aliurakoitsijat ·
Yhteenveto (ALV-kohtelu kululajeittain). UI:ssa lisäksi Myynti, Tuntiseuranta,
Palkkakustannukset.

## 7. Netvisor-tietolähteet ja vienti

1. **Myyntireskontra** → myyntilaskut. Vienti: Myynti → Myyntireskontra → Excel.
2. **Laskentakohderaportti** → ostolaskut (materiaalit, jäte, konevuokra, aliurakka,
   palkat). Vienti: Raportit → Laskentakohderaportti → rajaa laskentakohteella → Excel.
3. **Tuntikirjanpito** → omien työntekijöiden tunnit. Vienti: Palkka → Tuntikirjanpito.

Parserit tunnistavat sarakkeet **nimien** perusteella (parser_myynti) → kestävät
Netvisor-vientiversioiden eroja. CSV-ongelmat: korjaa Windowsin muotoasetus suomalaiseksi.

## 8. Käyttäjähallinta ja roolit (auth.py)

Yhteinen käyttäjärekisteri kaikille kolmelle sovellukselle (Supabase `globaali_data`,
avain `kayttajat`). Salasanat PBKDF2-HMAC-SHA256, 100k kierrosta, satunnainen suola.

| Rooli | Kustannus | Tuntikirja | Kalusto |
|-------|-----------|------------|---------|
| `admin` | ✅ + käyttäjähallinta | ✅ + käyttäjähallinta | ✅ + käyttäjähallinta |
| `tyonjohtaja` | ✅ | ✅ hyväksyy tunnit, projektit | ✅ hallinta |
| `katselija` | ✅ (luku) | 👁️ luku | 👁️ luku |
| `tyontekija` | 🚫 estetty (palkkatiedot) | ✅ omat tunnit, sallitut projektit | 📱 QR |

- **Ensikäynnistys:** kun rekisteri tyhjä, sovellus pyytää luomaan pääkäyttäjän (admin).
- **Hyväksyntä lukitsee:** kun TJ hyväksyy viikon tunnit, työntekijä ei voi enää muokata
  (`_on_lukittu`). Vain TJ/admin voi palauttaa tilan.
- **QR-skannaus on julkinen** (kalusto) — työmies ei tarvitse kirjautumista.

## 9. Tallennus (storage.py + storage_supabase.py)

- **Paikallisesti:** JSON-tiedostot `data/`-kansiossa. Toimii ilman Supabasea.
- **Pilvessä:** Supabase REST-rajapinta (PostgREST) suorilla `requests`-kutsuilla.
  Valinta automaattinen: `on_pilvessa()` tarkistaa onko `st.secrets["supabase"]` asetettu.

Supabase-taulut:
```sql
projekti_data (projekti text, avain text, data jsonb, unique(projekti,avain))
globaali_data (avain text primary key, data jsonb)
```
Projektikohtainen data → `projekti_data` (ali_tunnit, tuntiseuranta, palkat, yhteenveto).
Globaali data → `globaali_data` (kayttajat, projektirekisteri, ammattinimikkeet,
kalusto_laitteet, kalusto_tapahtumat).

**TÄRKEÄ — Supabase-avain:** käytä **secret-avainta** (`sb_secret_...` tai legacy
`service_role`), EI publishable-avainta. Secret-avain ohittaa RLS:n ja toimii
palvelinpuolella (Streamlit secrets, ei selaimelle). Publishable-avain + RLS estää
kirjoitukset (virhe 42501). Avain VAIN Streamlit Secretsiin, ei koskaan GitHubiin.

## 10. Sudenkuopat

- **`tr()` ei `t()`:** käännösfunktio on `tr()`. Aiemmin nimellä `t()` mutta se
  törmäsi `for t in ...` -silmukkamuuttujiin ja varjostui → NameError. Älä nimeä uudelleen.
- **F-string + kenoviiva:** Python <3.12 ei salli kenoviivaa f-stringin lausekkeessa.
  Laske arvo muuttujaan ensin (esim. `_css = _tila_css(...)` ja `f"...{_css}..."`).
- **Supabase RLS:** on PÄÄLLÄ kaikissa tauluissa (ei policy-sääntöjä). Secret-avain
  ohittaa RLS:n → toimii. Publishable/anon-avain estyy → virhe 42501. Käytä AINA
  secret-avainta kaikissa kolmessa sovelluksessa.
- **`runtime.txt` ei toimi Streamlit Cloudissa** (Heroku-konventio). Python-versio
  valitaan appin Advanced settings -kohdassa.
- **Älä pinniä `supabase`-kirjastoa:** se aiheutti loputtomia httpx/gotrue/pydantic-
  ristiriitoja. Siksi käytämme suoria REST-kutsuja (`requests`).
- **QR-koodien app_url:** kalustoseurannan secrets `[kalusto] app_url` pitää olla
  oikea julkaistu osoite ENNEN tarrojen tulostusta, muuten QR osoittaa localhostiin.

## 11. Julkaisu Streamlit Cloudiin

1. **[share.streamlit.io](https://share.streamlit.io)** → Create app
2. Repository: `sakariteljomaa-star/tyomaaseuranta`, Branch: `main`
3. Main file path: `app.py` / `ali_app.py` / `kalusto_app.py` (yksi app kustakin)
4. Advanced settings → Secrets:
```toml
[supabase]
url = "https://sxpnzyaafuhbsuolpfuc.supabase.co"
key = "sb_secret_...secret-avain..."

[kalusto]                                    # vain kalusto_app.py
app_url = "https://<kaluston-osoite>.streamlit.app"
```
5. Deploy. Sama secret-avain kaikkiin kolmeen.

## 12. Konventiot

- Projektitiedoston nimi (paikallinen): `kohde_osoite.json` pienillä, alaviivat,
  ei ä/ö (esim. `valteri-koulu_tenholantie_15.json`).
- Kieli: suomi + venäjä (käyttöliittymä). Raportit suomeksi.
- Jokainen Netvisor-tuonti on itsenäinen: kukin osio lataa oman aineistonsa.
- Tietosuoja: ks. `TIETOSUOJASELOSTE.md`. Säilytysaika 6 kk projektin päätyttyä.
