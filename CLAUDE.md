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
| 👷 **Tuntikirja** | `ali_app.py` | Työmaan tuntikirja: omat + aliurakoitsijoiden tunnit, hyväksyntä, viranomaisilmoitukset | työnjohto, työntekijät |
| 🔧 **Kalustoseuranta** | `kalusto_app.py` | QR-pohjainen laitekirjanpito | kaikki työmaalla |
| ☣️ **Asbestikohteet** | `asbesti_app.py` | Asbestipurkukohteiden tarjoukset, dokumentointi ja raportit (tilaaja kohdekohtainen) | työnjohto, työntekijät |

Yritys: Uudenmaan Asbestipurku Oy / Uudenmaan Vahinkopalvelu Oy (Y-tunnus 2817254-1).
Toiminta: asbestipurku, vahinkosaneeraus, rakentamisen aliurakointi.
Tmi ST Konsultti (Y-tunnus 3376518-1) = työnjohtopalvelut, oma toiminimi.

## 2. Käynnistys

```
# Paikallisesti (ei vaadi Supabasea — käyttää data/-kansion JSON-tiedostoja)
python3 -m streamlit run app.py          --server.port 8501   # Kustannusseuranta
python3 -m streamlit run ali_app.py      --server.port 8502   # Tuntikirja
python3 -m streamlit run kalusto_app.py  --server.port 8503   # Kalustoseuranta
python3 -m streamlit run asbesti_app.py  --server.port 8504   # Asbestikohteet
```

Riippuvuudet: `pip install -r requirements.txt`

**Julkaisu:** Streamlit Community Cloud, kolme erillistä appia samasta GitHub-repositoriosta
(`sakariteljomaa-star/tyomaaseuranta`), eri Main file path kullekin. Ks. kohta 11.

## 3. Arkkitehtuuri

| Tiedosto             | Tehtävä                                                       |
|----------------------|--------------------------------------------------------------|
| `app.py`             | Kustannusseuranta-UI (10 välilehteä + Käyttäjät adminille)    |
| `ali_app.py`         | Tuntikirja-UI (roolien mukaiset välilehdet, 2 kieltä) + Viranomaisilmoitukset |
| `verohallinto.py`    | Päätoteuttajan työntekijäilmoitus (Verohallinto): kokoaa kuukauden työmaalla olleet tuntikirjauksista + tekijöiden viranomaistiedot → Excel/CSV |
| `perehdytys_dokumentit.py` | Työntekijän tietosuojailmoitus (fi/ru) + kaksikielinen tietolomake PDF:nä, esitäytetty työmaan tiedoilla (Tuntikirja → Viranomaisilmoitukset) |
| `fonts/`             | DejaVu Sans (vapaa lisenssi) — kyrilliset merkit reportlab-PDF:iin. Älä korvaa Arialilla (ei saa jakaa) |
| `kalusto_app.py`     | Kalustoseuranta-UI + julkinen QR-skannausnäkymä              |
| `asbesti_app.py`     | Asbestikohteet-UI: kohteet + tilaaja, tilakone, dokumentointi |
| `asbesti_dokumentit.py`| Turvallisuussuunnitelma-, ennakkoilmoitus-, raportti- ja tarjous-PDF:t (reportlab + pypdf) |
| `tarjouslaskenta.py` | Asbestitarjoukset: hinnasto, vakiopaketti, kartoitus-PDF:n tulkinta |
| `labroc_nouto.py`    | Labroc-tulosten IMAP-nouto ja PDF-tulkinta                   |
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
- **Asbestitarjousten hinnoittelu** (tarjouslaskenta.py, muokattavissa appin hinnastossa):
  vastaanotto+ennakkoilmoitus 250 € · osastointi ja suojaukset (sis. alipaineistus-
  laitteet) 350 € · purkutyö 55 €/h (min. 4 h) · loppumittaus+dokumentointi 175 € ·
  jäte min. 90 € · pk-kulut 25 € · matkat 1 €/km · **minimiveloitus 1 000 €** ·
  lisätyöt 55/75 €/h · tarjous voimassa 30 vrk, maksuehto 14 pv netto, ALV 0 %
  käänteinen. Purkutyön yksikköhinnat (€/m² ym.) tapauskohtaisesti — lisätään
  hinnastoon kun vakiintuvat.

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
- **Katselija = vain luku:** tallennus/poisto vain `A.voi_hyvaksya(rooli)` (admin + TJ).
  Uusiin tallennus- ja poistotoimintoihin AINA tämä ehto (`app.py`: `voi_muokata`,
  `kalusto_app.py`: `on_tj`). Kaluston hallintanäkymä ei työntekijälle (vain QR).
- **Kirjautumisen suojaus (auth.py):** salasana väh. 8 merkkiä (`MIN_SALASANA`), 5 väärää
  yritystä → 15 min lukitus (globaali `kirjautumisyritykset`), sama virheviesti kaikissa
  tapauksissa, avoin istunto tarkistetaan rekisteristä 30 s välein, viimeistä adminia ei voi
  alentaa/passivoida. `paivita_kayttaja` palauttaa `(ok, viesti)`.
- **Välilehtilohkot:** roolin mukaan piilotettava välilehti on `None` → lohko AINA
  `if tab_x is not None:` -ehtoon (muuten `AttributeError: __enter__`).
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
Projektikohtainen data → `projekti_data` (ali_tunnit, tuntiseuranta, palkat, yhteenveto;
asbesti: `cateva_<työnumero>` → asbesti_dok, asbesti_ilmoitukset).
Globaali data → `globaali_data` (kayttajat, kirjautumisyritykset, projektirekisteri, ammattinimikkeet,
kalusto_laitteet, kalusto_tapahtumat, cateva_kohteet, asbesti_patevyydet,
labroc_kasitellyt).

**Tiedostot (kuvat, PDF:t):** Supabase Storage -bucket `tyomaakuvat` — luo kerran
hallintapaneelissa: Storage → New bucket → nimi `tyomaakuvat` → **Private**.
Secret-avain ohittaa Storage-RLS:n, policyjä ei tarvita. Paikallisesti tiedostot
menevät `data/kuvat/`-kansioon. Polkukäytäntö: `<työnumero>/<vaihe>/<aikaleima>.jpg`.
Asbestidokumenttien kenttärakenteet: ks. `CATEVA_DOKUMENTTIPOHJAT.md` (nimi historiallinen).
**Cateva-yhteistyö on päättynyt.** Tilaaja syötetään kohteelle/tarjoukselle (`TILAAJA_KENTAT`),
sähköpostit menevät tilaajan osoitteeseen. Tallennusavaimet `cateva_kohteet`, `cateva_tarjoukset`,
`cateva_<nro>` ovat historiallisia — ÄLÄ nimeä uudelleen ilman datan siirtoa.

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
- **Lukuvirhe ≠ tyhjä data:** epäonnistunut Supabase-luku palauttaa `[]`. `storage_supabase`
  merkitsee sen ja **estää saman tiedon tallennuksen**, kunnes luku onnistuu (muuten tyhjä
  lista korvaisi tiedot). `auth.kirjaudu_gate` ei tarjoa alkuasennusta lukuvirheen aikana.
  Tarkistus: `storage.lukuvirhe(avain[, projekti])`.
- **Supabase Free pysäyttää projektin** ~7 vrk käyttämättömyyden jälkeen → osoite lakkaa
  resolvoitumasta (`NameResolutionError`). Palautus: Supabase Dashboard → projekti → Restore.
  Streamlit-pingaus ei riitä (curl ei aja Python-koodia eikä tee Supabase-kutsua).
- **Älä pinniä `supabase`-kirjastoa:** se aiheutti loputtomia httpx/gotrue/pydantic-
  ristiriitoja. Siksi käytämme suoria REST-kutsuja (`requests`).
- **QR-koodien app_url:** kalustoseurannan secrets `[kalusto] app_url` pitää olla
  oikea julkaistu osoite ENNEN tarrojen tulostusta, muuten QR osoittaa localhostiin.
- **`width="stretch"`, EI `use_container_width`:** `use_container_width` poistuu
  Streamlitista (vanhentunut, poisto 2025-12-31 jälkeen) ja Cloud asentaa aina uusimman →
  appit kaatuisivat. Käytä `width="stretch"` (= vanha `True`) tai `width="content"`
  (= vanha `False`). Vaatii `streamlit>=1.49.0` (dataframe/data_editor/image).

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

[smtp]                                       # vain asbesti_app.py (raportin lähetys)
host = "smtp.gmail.com"
port = 465
user = "info@uudenmaanasbestipurku.fi"
password = "...(Gmailin sovellussalasana)..."
tarkistusosoite = "info@uudenmaanasbestipurku.fi"  # valinnainen: viestit ensin tänne
                                             # tarkistettaviksi (vanha nimi cateva_vastaanottaja
                                             # toimii samoin). Ilman → suoraan tilaajalle + Bcc user

[labroc_email]                               # vain asbesti_app.py (tulosten nouto)
host = "imap.gmail.com"
user = "...sama postilaatikko johon Labroc-tulokset tulevat..."
password = "...(Gmailin sovellussalasana)..."
```
5. Deploy. Sama secret-avain kaikkiin kolmeen.

## 12. Konventiot

- Projektitiedoston nimi (paikallinen): `kohde_osoite.json` pienillä, alaviivat,
  ei ä/ö (esim. `valteri-koulu_tenholantie_15.json`).
- Kieli: suomi + venäjä (käyttöliittymä). Raportit suomeksi.
- Jokainen Netvisor-tuonti on itsenäinen: kukin osio lataa oman aineistonsa.
- Tietosuoja: ks. `TIETOSUOJASELOSTE.md`, `KASITTELYTOIMET.md` (GDPR 30 art.) ja `GDPR_ARVIOINTI.md`. Säilytysajat tietoryhmittäin
  (verodata 6 v). Järjestelmä on henkilörekisteri. Asbestin pätevyystiedot (terveystarkastus)
  ovat erityisiä henkilötietoja: vain `on_tj`-roolit, katselijalle ei ladata (`asbesti_app.py`).
  Uusia henkilötietokenttiä lisättäessä päivitä myös KASITTELYTOIMET.md.
  Työntekijöiden informointi ja perehdytys: `PEREHDYTYSOHJE_TIETOSUOJA.md`. Jos käsiteltävät
  tiedot muuttuvat, päivitä myös `perehdytys_dokumentit.py`:n ilmoitusteksti (fi + ru).
