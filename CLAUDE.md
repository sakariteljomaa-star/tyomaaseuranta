# CLAUDE.md — Työmaaseuranta

Tämä tiedosto ohjaa Claude Codea tämän projektin kehityksessä. Lue tämä aina ensin.
Kaikki luokittelu- ja laskentasäännöt ovat tässä — älä keksi niitä uudelleen, vaan
sovella näitä. Jos sääntö muuttuu, päivitä se TÄHÄN tiedostoon (ja `classifier.py`:hyn).

---

## 1. Mikä tämä on

Streamlit-pohjainen työkalu työmaiden kustannusseurantaan. Lukee Netvisorista ladatut
viennit (ostolaskut, myyntireskontra, tunnit), luokittelee ne automaattisesti ja tuottaa
valmiin kustannusseuranta-Excelin sekä aliurakoitsija-viikkoraportin.

Yritys: Uudenmaan Asbestipurku Oy / Uudenmaan Vahinkopalvelu Oy (Y-tunnus 2817254-1).
Toiminta: asbestipurku, vahinkosaneeraus, rakentamisen aliurakointi.
Tmi ST Konsultti (Y-tunnus 3376518-1) = työnjohtopalvelut, oma toiminimi.

## 2. Käynnistys

```
python3 -m streamlit run app.py
```
→ avautuu osoitteeseen http://localhost:8501

Riippuvuudet: `pip install -r requirements.txt`

## 3. Arkkitehtuuri

| Tiedosto            | Tehtävä                                                  |
|---------------------|----------------------------------------------------------|
| `app.py`            | Käyttöliittymä, välilehdet                                |
| `parser.py`         | Netvisor ostolaskut → DataFrame                           |
| `parser_myynti.py`  | Netvisor myyntireskontra → DataFrame                      |
| `parser_tunnit.py`  | Netvisor tuntikirjanpito → DataFrame                      |
| `classifier.py`     | Automaattinen luokittelu (SÄÄNNÖT, ks. kohta 4)           |
| `excel_export.py`   | Kustannusseuranta-Excelin generointi (Valteri-malli)      |
| `raportti_ali.py`   | Aliurakoitsija-viikkoraportti (Excel/PDF)                 |
| `storage.py`        | JSON-tallennus projektikohtaisesti                        |
| `data/`             | Projektikohtaiset tallennukset, esim. `valteri-koulu_tenholantie_15.json` |

Suunnitteluperiaate: luokittelulogiikka pidetään erillään muusta (`classifier.py`),
jotta sääntömuutokset osuvat yhteen tiedostoon.

## 4. Luokittelusäännöt (ydin)

Luokittelu tehdään ensisijaisesti **toimittajan nimen + ALV-tunnuksen** perusteella.

### ALV-käsittely
- **KOOS 25,5 %** = kotimaan ostot: materiaalit, jätemaksut, konevuokra, suojaimet.
  Vähennetään ALV-tilityksessä. Sisältää sivukulukertoimen tarvittaessa.
- **RAOS / ALV 0 %** = rakentamispalvelun käänteinen ALV: aliurakoitsijat.
  Ostopalvelu, **ei sivukulukerrointa**.

### Kululajien tunnistus
- **Kuljetusrinki = AINA jäte** (jätemaksut), riippumatta muusta.
- **Aliurakoitsijat** = RAOS tai ALV 0 % -rivit. Esim. A-voima Uusimaa Oy.
  Aliurakka = muuttuva kiinteä kulu (ostopalvelu, ei kerrointa). Tuntihinta 35 €/h.
- **Sanerakennus Oy** = aina ALV 0 % (käänteinen arvonlisäverovelvollisuus).
- **Materiaalit / konevuokra / suojaimet** = KOOS 25,5 %.
- **Palkkakirjanpito** = ALV 0 %.

### Laskentakohde erottaa urakan ja lisätyön
- Urakka: laskentakohde "Valteri-koulu Mirlux"
- Lisätyö: laskentakohde "Valteri koulu Mirlux LISÄTYÖT"
- Yleinen sääntö: laskentakohde-kentän teksti ratkaisee, urakka vs. lisätyö.

## 5. Laskentaparametrit

- Oman työntekijän tuntihinta: **38 €/h**
- Aliurakoitsijan tuntihinta: **35 €/h**
- Maksuehto: **21 pv netto** (eräpäivä = laskutuspvm + 21 pv)
- Palkkakerroin (brutto × kerroin):
  - oletus **1,5**
  - toteuttava porras **1,6–1,7**
  - toimihenkilöt **1,3–1,4**
  - (vaihtelee henkilöittäin TyEL-%:n, vakuutusten ja muiden sivukulujen mukaan)
- Aliurakoitsijalaskut: ALV 0 %, **ei** sivukulukerrointa.

## 6. Kustannusseuranta-Excelin rakenne (9 välilehteä)

Järjestys: **Myynti | Urakkaseuranta | Lisätyöt | Tuntiseuranta | Ostot | Jätemaksut | Aliurakoitsijat | Palkkakustannukset | Yhteenveto**

| Välilehti          | Sisältö                                                            |
|--------------------|--------------------------------------------------------------------|
| Myynti             | Netvisor myyntireskontran kredit-rivit (asiakas Mirlux Oy)         |
| Urakkaseuranta     | Maksuerät, laskutuspvm, eräpäivä (+21 pv), tila                    |
| Lisätyöt           | Lisätyölaskut riveinä                                              |
| Tuntiseuranta      | Viikkokohtaiset tunnit (urakka/lisätyö/vesivahinko) × 38 €/h + jäte € + kalusto € |
| Ostot              | Materiaalit, konevuokra, suojaimet (KOOS 25,5 %)                   |
| Jätemaksut         | Kuljetusrinki + muut (KOOS 25,5 %)                                 |
| Aliurakoitsijat    | Ostopalvelut, ALV 0 % / RAOS, ei kerrointa                         |
| Palkkakustannukset | Brutto × kerroin (ks. kohta 5)                                     |
| Yhteenveto         | Koontisivu + ALV-kohtelu kululajeittain                            |

## 7. Netvisor-tietolähteet ja vienti

Lähteet:
1. **Myyntireskontran otanto** = myyntilaskut (kredit-rivit).
2. **Ostoreskontra tilikohtaisesti**: materiaalit (KOOS), jätemaksut (Kuljetusrinki=jäte, KOOS),
   konevuokra (KOOS), suojaimet (KOOS), aliurakoitsijat (RAOS / ALV 0 %), palkkakirjanpito (ALV 0 %).

Vienti Netvisorista: raporttinäkymässä rajaa **laskentakohteella** ja lataa Exceliin tai CSV:hen
kolmen pisteen valikosta. Tallenna `data/`-kansion sijaan tuontia varten erikseen (esim.
kohteen lähtötietokansioon).

Huom CSV: jos päivämäärät/desimaalit menevät väärin, korjaa Windowsin muotoasetus suomalaiseksi
(Finnish/Finland). Virallista tuloslaskelmaa ja tasetta ei saa Excel-muodossa — niitä ei tarvita.

## 8. Tuntilappuprosessi

- Tuntilaput skannataan PDF/kuva → luetaan Excel-taulukkoon (päivittäinen erittely per tekijä).
- Kategoriat: **Urakka / Lisätyö / Vesivahinko**.
- Jako tehdään tuntilomakkeen **"muut kulut" -sarakkeen** merkinnän mukaan.
- Jos jako puuttuu, käytä **projektin kokonaissuhdelukua**.
- **Ditto-merkintä** = edellisen rivin kuvaus.
- Tee **viikkoyhteenveto ennen erittely-taulukkoa** tarkistusasiakirjana.

## 9. Konventiot

- Projektitiedoston nimi: `kohde_osoite.json` pienillä kirjaimilla, alaviivat erottimina,
  ei ä/ö-kirjaimia (esim. `valteri-koulu_tenholantie_15.json`).
- Tallennus on projektikohtaista ja säilyy selaimen sulkemisen yli (`storage.py` → `data/`).
- Jokainen tuonti on itsenäinen: kukin osio lataa oman aineistonsa erikseen.
- Kieli: suomi (käyttöliittymä, raportit, sarakeotsikot).

## 10. Sudenkuopat

- **OneDrive/SharePoint-jako:** koko `työmaaseuranta`-kansio jaetaan, sekä koodi että `data/`.
  Aseta kansiolle "Säilytä aina tällä laitteella" — muuten Python ei löydä tiedostoja.
- **Yhtäaikainen muokkaus:** älä muokkaa SAMAA projektia kahdelta koneelta yhtä aikaa
  (viimeinen tallennus voittaa). Eri kohteet eri aikoina OK.
- **localhost on konekohtainen:** `streamlit run` näkyy vain sen koneen selaimessa.
  Työkaverin pitää joko ajaa työkalu omalla koneellaan tai käyttää vain valmiita Exceleitä.
