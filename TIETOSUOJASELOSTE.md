# Tietosuojaseloste — Työmaaseurantajärjestelmä

*Informaatio rekisteröidyille, EU:n yleinen tietosuoja-asetus (GDPR) 13 ja 14 artikla.*

**Päivitetty:** 15.10.2026 · Korvaa version 1.6.2026

---

## 1. Rekisterinpitäjä

**Uudenmaan Asbestipurku Oy** (Y-tunnus 2817254-1)
Yhteyshenkilö tietosuoja-asioissa: **Sakari Teljomaa**, sakari.teljomaa@gmail.com

## 2. Rekisterin nimi ja kattavuus

**Työmaaseurantajärjestelmä**, joka koostuu neljästä sovelluksesta:

| Sovellus | Käyttötarkoitus |
|---|---|
| Tuntikirja | Aliurakoitsijoiden ja työntekijöiden työtunnit, hyväksyntä, Verohallinnon työntekijäilmoitus |
| Kustannusseuranta | Työmaan kustannukset ja laskutus, Verohallinnon urakkailmoitus |
| Kalustoseuranta | Koneiden ja laitteiden luovutukset ja palautukset |
| Asbestikohteet | Asbestipurkukohteiden dokumentointi, työntekijöiden pätevyyksien seuranta |

## 3. Keiden tietoja käsitellään (rekisteröidyt)

- Omat työntekijät
- **Aliurakoitsijoiden ja vuokrayritysten työntekijät**, jotka työskentelevät työmaillamme
- Järjestelmän käyttäjät (työnjohto, kirjanpito)
- Tilaajien ja yhteistyökumppaneiden yhteyshenkilöt

## 4. Käsittelyn tarkoitukset, tiedot ja oikeusperusteet

| Tietoryhmä | Tarkoitus | Oikeusperuste |
|---|---|---|
| Nimi, veronumero, syntymäaika, työnantaja ja sen Y-tunnus, työsuhteen laji, kansalaisuus, lähettävä yritys, työmaalla olopäivät | Päätoteuttajan lakisääteinen työntekijäilmoitus Verohallinnolle ja työmaan henkilöluettelo | **Lakisääteinen velvoite** (6.1 c) — verotusmenettelylaki (rakentamisen tiedonantovelvollisuus), työturvallisuuslaki (veronumero ja henkilöluettelo yhteisellä rakennustyömaalla) |
| Aliurakoitsijayrityksen nimi, Y-tunnus, yhteyshenkilö, maksetut summat | Lakisääteinen urakkailmoitus Verohallinnolle | **Lakisääteinen velvoite** (6.1 c) — verotusmenettelylaki |
| Työtunnit päivittäin, työtehtävä, työnjohtajan kommentit, hyväksyntätila | Aliurakkasopimusten toteutuksen seuranta ja laskutusperusteiden todentaminen | **Sopimus** (6.1 b) ja **oikeutettu etu** (6.1 f) |
| Osoite, puhelinnumero | Yhteydenpito ja Verohallinnon ilmoitus (vapaaehtoiset kentät) | **Oikeutettu etu** (6.1 f) / lakisääteinen velvoite |
| Terveystarkastuksen suorituspäivä ja voimassaolo, hengityksensuojaimen tiiviystestauksen päivä, asbestityön koulutustodistuksen päivä | Asbestityön edellytysten (työkyky, pätevyys) varmistaminen | **Lakisääteinen velvoite** (6.1 c) ja **9.2 b** (työoikeudelliset velvoitteet) — asbestityöstä annettu valtioneuvoston asetus, työterveyshuoltolaki, laki yksityisyyden suojasta työelämässä 5 § |
| Kaluston luovuttajan/palauttajan nimi | Kaluston sijainnin ja vastuun seuranta | **Oikeutettu etu** (6.1 f) |
| Käyttäjätunnus, nimi, rooli, salasanan tiiviste, toimintaloki | Pääsynhallinta ja tietoturva | **Oikeutettu etu** (6.1 f) ja tietoturvavelvoite (32 art.) |

**Terveystiedot:** järjestelmään ei tallenneta diagnooseja eikä terveystarkastuksen sisältöä —
vain tieto tarkastuksen suorittamisesta ja voimassaolosta. Näitä tietoja käsittelevät vain
nimetyt henkilöt, jotka tekevät niiden perusteella työhön osallistumista koskevia päätöksiä.

## 5. Mistä tiedot saadaan

- Rekisteröidyltä itseltään
- **Aliurakoitsijalta / työnantajalta**, joka toimittaa työntekijöidensä tiedot päätoteuttajalle
  lakisääteistä ilmoitusta varten (GDPR 14 art.)
- Kirjanpitojärjestelmästä (Netvisor) — laskutus- ja ostotiedot

## 6. Tietojen luovutukset

| Vastaanottaja | Mitä | Peruste |
|---|---|---|
| **Verohallinto** | Työntekijä- ja urakkailmoitukset | Lakisääteinen velvoite |
| Tilaaja / rakennuttaja | Työmaan tuntiraportit ja asbestityön raportit | Sopimus |
| Viranomaiset (esim. työsuojeluviranomainen) | Pyydettäessä lain nojalla | Lakisääteinen velvoite |

Tietoja ei myydä eikä luovuteta markkinointiin.

## 7. Henkilötietojen käsittelijät

| Käsittelijä | Tehtävä | Sijainti |
|---|---|---|
| Supabase | Tietokanta ja tiedostojen tallennus | **EU** (Frankfurt, Saksa) |
| Streamlit / Snowflake | Sovellusten ajoympäristö (palvelin) | **Yhdysvallat** |
| Google | Raporttien sähköpostilähetys ja laboratoriotulosten nouto (Gmail) | EU / Yhdysvallat |
| Netvisor (Visma) | Kirjanpito | EU |

## 8. Tietojen siirto EU/ETA-alueen ulkopuolelle

Sovellusten ajoympäristö (Streamlit Community Cloud, Snowflake Inc.) sijaitsee Yhdysvalloissa.
Henkilötiedot tallennetaan EU:hun, mutta niitä käsitellään sovelluksen käytön aikana
Yhdysvalloissa sijaitsevalla palvelimella.

Siirron perusteena on **EU:n ja Yhdysvaltojen tietosuojakehys (Data Privacy Framework)**
tai **EU:n komission vakiosopimuslausekkeet (SCC)** palveluntarjoajan käsittelysopimuksen
mukaisesti. *[TARKISTETTAVANA — ks. GDPR_ARVIOINTI.md, toimenpide T1]*

## 9. Säilytysajat

| Tieto | Säilytysaika | Peruste |
|---|---|---|
| Verohallinnon ilmoitusten tiedot (työntekijä- ja urakkailmoitus) | **6 vuotta** sen vuoden päättymisestä, jota tiedot koskevat | Verotusmenettelylaki |
| Laskutukseen ja kustannuksiin liittyvät tunti- ja ostotiedot | **6 vuotta** tilikauden päättymisestä | Kirjanpitolaki |
| Työtunnit, joita ei tarvita yllä mainittuihin | 6 kk projektin päättymisestä | Tarpeellisuus |
| Pätevyys- ja terveystarkastustiedot | Työskentelyn ajan + **1 vuosi** viimeisestä työmaasta *[tarkistettava suhteessa ASA-säilytysvelvoitteisiin]* | Tarpeellisuus |
| Kaluston luovutustiedot | 2 vuotta | Oikeutettu etu |
| Toimintaloki | 2 vuotta | Tietoturva |
| Käyttäjätunnukset | Käyttöoikeuden päättymiseen + 6 kk | Tietoturva |

Säilytysajan päätyttyä tiedot poistetaan tai anonymisoidaan.

## 10. Tietoturva

- Tiedot salattu siirron aikana (HTTPS/TLS) ja tallennettuina (palveluntarjoajan salaus)
- Pääsy vain henkilökohtaisilla tunnuksilla; roolipohjaiset oikeudet (työntekijä ei näe muiden tietoja)
- Salasanat tallennetaan tiivisteinä (PBKDF2-SHA256, 100 000 kierrosta)
- Tietokannan rivitason suojaus (RLS) ja palvelinpuolen avaimet
- Toimintaloki kirjautumisista ja tärkeistä muutoksista

## 11. Rekisteröidyn oikeudet

Sinulla on oikeus:
- **saada pääsy** omiin tietoihisi (tarkastusoikeus)
- **oikaista** virheelliset tiedot
- **poistattaa** tietosi, ellei niiden säilyttäminen ole lakisääteisesti pakollista
- **rajoittaa** käsittelyä ja **vastustaa** oikeutettuun etuun perustuvaa käsittelyä
- saada tiedot **siirrettävässä muodossa** (sopimukseen perustuva käsittely)

Pyynnöt: kohdan 1 yhteyshenkilölle. Vastaamme kuukauden kuluessa.

**Huom:** lakisääteisiä ilmoitustietoja (kohta 9) ei voida poistaa ennen säilytysajan päättymistä.

## 12. Valitusoikeus

Voit tehdä valituksen valvontaviranomaiselle: **Tietosuojavaltuutetun toimisto**, tietosuoja.fi

## 13. Automaattinen päätöksenteko

Järjestelmässä ei tehdä automaattisia päätöksiä eikä profilointia, jolla olisi oikeusvaikutuksia.
