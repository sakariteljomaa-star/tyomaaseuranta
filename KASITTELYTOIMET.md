# Seloste käsittelytoimista — GDPR 30 artikla

**Rekisterinpitäjä:** Uudenmaan Asbestipurku Oy (Y-tunnus 2817254-1)
**Yhteyshenkilö:** Sakari Teljomaa, sakari.teljomaa@gmail.com
**Tietosuojavastaava:** ei nimitetty (ei lakisääteistä velvollisuutta, ks. GDPR_ARVIOINTI.md)
**Laadittu:** 15.10.2026 · **Seuraava tarkistus:** viimeistään 10/2027 tai muutosten yhteydessä

> Seloste on rekisterinpitäjän sisäinen asiakirja, joka on pyydettäessä esitettävä
> Tietosuojavaltuutetulle. Rekisteröidyille suunnattu informaatio: `TIETOSUOJASELOSTE.md`.

---

## Yhteiset tiedot kaikille käsittelytoimille

### Järjestelmä
Työmaaseurantajärjestelmä: Tuntikirja (`ali_app.py`), Kustannusseuranta (`app.py`),
Kalustoseuranta (`kalusto_app.py`), Asbestikohteet (`asbesti_app.py`).

### Henkilötietojen käsittelijät (GDPR 28 art.)

| Käsittelijä | Palvelu | Käsittelyn sijainti | Käsittelysopimus |
|---|---|---|---|
| Supabase Inc. | Tietokanta, tiedostotallennus | EU (Frankfurt) | ⏳ Varmistettava (T1) |
| Snowflake Inc. (Streamlit Community Cloud) | Sovellusten ajoympäristö | Yhdysvallat | ⏳ Varmistettava (T1) |
| Google LLC (Gmail) | Raporttien sähköpostilähetys, Labroc-tulosten nouto | EU / Yhdysvallat | ⏳ Varmistettava (T1) |
| Visma Netvisor Oy | Kirjanpito (tietolähde) | EU | Erillinen asiakassopimus |

### Siirrot EU/ETA-alueen ulkopuolelle (GDPR 44–49 art.)
Sovellusten ajoympäristö (Snowflake/Streamlit) ja osin Google sijaitsevat Yhdysvalloissa.
Tiedot tallennetaan EU:hun, mutta niitä käsitellään käytön aikana US-palvelimilla.
**Peruste:** EU–US Data Privacy Framework (jos palveluntarjoaja sertifioitu) tai
vakiosopimuslausekkeet (SCC). **Tila:** varmistettavana, toimenpide T1.

### Tekniset ja organisatoriset suojatoimet (GDPR 32 art.)
- Liikenne salattu (HTTPS/TLS); tallennus palveluntarjoajan salaamana
- Henkilökohtaiset käyttäjätunnukset; salasanat PBKDF2-HMAC-SHA256-tiivisteinä (100 000 kierrosta, suola)
- Roolipohjainen pääsynhallinta: admin, työnjohtaja, katselija, työntekijä
- Työntekijä näkee vain omat kohteensa ja tuntinsa; viranomaistiedot vain työnjohdolle
- Terveystarkastustiedot vain työnjohdolle (admin + työnjohtaja), ei katselijalle
- Tietokannan rivitason suojaus (RLS) päällä; palvelinpuolen avain vain sovellusten salaisuuksissa
- Toimintaloki: kirjautumiset, käyttäjämuutokset, hyväksynnät, Netvisor-haut
- Salaisuudet eivät ole lähdekoodissa (Streamlit Secrets; `.gitignore`)

---

## Käsittelytoimet

### KT1 — Verohallinnon työntekijäilmoitus ja työmaan henkilöluettelo

| | |
|---|---|
| **Tarkoitus** | Päätoteuttajan lakisääteinen kuukausittainen ilmoitus yhteisellä rakennustyömaalla työskennelleistä; työmaan henkilöluettelo |
| **Oikeusperuste** | 6.1 c lakisääteinen velvoite — verotusmenettelylaki (rakentamisen tiedonantovelvollisuus), työturvallisuuslaki (veronumero, henkilöluettelo) |
| **Rekisteröidyt** | Omat työntekijät; aliurakoitsijoiden ja vuokrayritysten työntekijät |
| **Tietoryhmät** | Nimi, veronumero, syntymäaika, työnantaja ja sen Y-tunnus, työsuhteen laji, kansalaisuus, lähettävä yritys, osoite, puhelin, työmaalla olopäivät |
| **Tietolähde** | Rekisteröity itse; työnantaja (aliurakoitsija) |
| **Vastaanottajat** | Verohallinto |
| **Säilytysaika** | 6 vuotta sen vuoden päättymisestä, jota tiedot koskevat |
| **Sovellus / tallennus** | Tuntikirja → Viranomaisilmoitukset; Supabase `globaali_data` (aliurakoitsijat), `projekti_data` (ali_tunnit) |
| **Erityiset riskit** | Ladatut Excel/CSV-ilmoitukset sisältävät veronumerot → poistetaan laitteelta lähetyksen jälkeen (T8) |

### KT2 — Verohallinnon urakkailmoitus

| | |
|---|---|
| **Tarkoitus** | Tilaajan lakisääteinen kuukausittainen ilmoitus aliurakoitsijoille maksetuista summista |
| **Oikeusperuste** | 6.1 c lakisääteinen velvoite — verotusmenettelylaki |
| **Rekisteröidyt** | Aliurakoitsijoiden yhteyshenkilöt (pääosin yritystietoa; toiminimiyrittäjien osalta henkilötietoa) |
| **Tietoryhmät** | Yrityksen nimi, Y-tunnus, yhteyshenkilö, maksetut summat |
| **Tietolähde** | Kirjanpito (Netvisor), rekisterinpitäjän syöttämä Y-tunnus |
| **Vastaanottajat** | Verohallinto |
| **Säilytysaika** | 6 vuotta sen vuoden päättymisestä, jota tiedot koskevat |
| **Sovellus / tallennus** | Kustannusseuranta → Viranomaisilmoitukset; Supabase `globaali_data` (aliurakoitsijarekisteri) |

### KT3 — Aliurakoitsijoiden ja työntekijöiden tuntiseuranta

| | |
|---|---|
| **Tarkoitus** | Aliurakkasopimusten toteutuksen seuranta, tuntien hyväksyntä, laskutusperusteiden todentaminen |
| **Oikeusperuste** | 6.1 b sopimus; 6.1 f oikeutettu etu (työmaan johtaminen) |
| **Rekisteröidyt** | Aliurakoitsijoiden työntekijät, omat työntekijät |
| **Tietoryhmät** | Nimi, yritys, ammattinimike, päivittäiset työtunnit, kustannuspaikka, päiväkohtaiset huomiot, työnjohtajan kommentit, hyväksyntätila, tuntihinta |
| **Vastaanottajat** | Tilaaja (viikkoraportti, sopimuksen mukaan) |
| **Säilytysaika** | Laskutuksen perusteena olevat: 6 vuotta tilikauden päättymisestä (kirjanpitolaki); muut: 6 kk projektin päättymisestä |
| **Sovellus / tallennus** | Tuntikirja; Supabase `projekti_data` |

### KT4 — Kustannusseuranta ja laskutus

| | |
|---|---|
| **Tarkoitus** | Työmaakohtainen kustannus- ja laskutusseuranta |
| **Oikeusperuste** | 6.1 f oikeutettu etu; kirjanpitolaki |
| **Rekisteröidyt** | Toimittajien ja asiakkaiden yhteyshenkilöt; omat työntekijät (tunnit ja palkkakustannukset) |
| **Tietoryhmät** | Laskujen selitteet (voivat sisältää nimiä), omien työntekijöiden tunnit, bruttopalkat kustannuksena |
| **Tietolähde** | Netvisor (XLSX-vienti tai API) |
| **Vastaanottajat** | Ei luovutuksia |
| **Säilytysaika** | 6 vuotta tilikauden päättymisestä |
| **Sovellus / tallennus** | Kustannusseuranta; Supabase `projekti_data`. Pääsy estetty työntekijä-roolilta (palkkatiedot) |

### KT5 — Asbestityön pätevyys- ja terveystarkastusseuranta ⚠️ erityinen henkilötietoryhmä

| | |
|---|---|
| **Tarkoitus** | Asbestityön edellytysten varmistaminen: voimassa oleva terveystarkastus, hengityksensuojaimen tiiviystestaus, asbestityön koulutus |
| **Oikeusperuste** | 6.1 c lakisääteinen velvoite ja **9.2 b** (työoikeudelliset velvoitteet) — valtioneuvoston asetus asbestityöstä, työterveyshuoltolaki, laki yksityisyyden suojasta työelämässä 5 § |
| **Rekisteröidyt** | Omat ja aliurakoitsijoiden asbestipurkutyöntekijät |
| **Tietoryhmät** | Nimi, työnantaja, terveystarkastuksen päivä ja voimassaolo, tiiviystestauksen päivä, koulutustodistuksen päivä, rekisterimerkintä. **Ei diagnooseja eikä tarkastuksen sisältöä.** |
| **Tietolähde** | Rekisteröity itse; työnantaja |
| **Vastaanottajat** | Työsuojeluviranomainen (asbestityön ennakkoilmoituksen liitteenä) |
| **Säilytysaika** | Työskentelyn ajan + 1 vuosi viimeisestä työmaasta *[tarkistettava ASA-velvoitteiden osalta, T9]* |
| **Pääsy** | **Vain nimetyt henkilöt:** admin- ja työnjohtajaroolit. Katselija- ja työntekijäroolit eivät näe tietoja (sovellus ei lataa niitä näiden roolien istuntoon). |
| **Nimetyt käsittelijät** | *[täydennä nimet: esim. Sakari Teljomaa, vastaava työnjohtaja]* |
| **Sovellus / tallennus** | Asbestikohteet → Pätevyydet; Supabase `globaali_data` (asbesti_patevyydet) — erillään muista henkilötiedoista |

### KT6 — Asbestikohteiden dokumentointi

| | |
|---|---|
| **Tarkoitus** | Asbestipurkutyön lakisääteinen dokumentointi ja raportointi tilaajalle (Cateva) |
| **Oikeusperuste** | 6.1 c lakisääteinen velvoite (asbestityön dokumentointi); 6.1 b sopimus (tilaajaraportointi) |
| **Rekisteröidyt** | Työntekijät, tilaajan yhteyshenkilöt; kuvissa mahdollisesti näkyvät henkilöt |
| **Tietoryhmät** | Nimi, kuittausmerkinnät aikaleimoineen, työmaakuvat, yhteyshenkilöiden nimi, puhelin ja sähköposti |
| **Vastaanottajat** | Tilaaja (raportti sähköpostitse), työsuojeluviranomainen (ilmoitukset) |
| **Säilytysaika** | Sopimuksen ja asbestityön dokumentointivelvoitteen mukaan *[tarkistettava, T9]* |
| **Sovellus / tallennus** | Asbestikohteet; Supabase `projekti_data`, Supabase Storage `tyomaakuvat` (yksityinen) |

### KT7 — Kaluston luovutusseuranta

| | |
|---|---|
| **Tarkoitus** | Koneiden ja laitteiden sijainnin ja vastuun seuranta |
| **Oikeusperuste** | 6.1 f oikeutettu etu |
| **Rekisteröidyt** | Kaluston luovuttajat ja palauttajat |
| **Tietoryhmät** | Nimi (vapaasti syötetty), työmaa, aikaleima, vikailmoituksen kuvaus |
| **Vastaanottajat** | Ei luovutuksia |
| **Säilytysaika** | 2 vuotta |
| **Sovellus / tallennus** | Kalustoseuranta; Supabase `globaali_data` (kalusto_tapahtumat). QR-skannaus julkinen, ei henkilötietojen näyttöä muille kuin laitteen historiassa |

### KT8 — Käyttäjähallinta ja toimintaloki

| | |
|---|---|
| **Tarkoitus** | Pääsynhallinta, tietoturva, väärinkäytösten selvittäminen |
| **Oikeusperuste** | 6.1 f oikeutettu etu; 32 art. tietoturvavelvoite |
| **Rekisteröidyt** | Järjestelmän käyttäjät |
| **Tietoryhmät** | Käyttäjätunnus, nimi, rooli, salasanan tiiviste, sallitut projektit; lokiin: toiminto, kohde, aikaleima |
| **Vastaanottajat** | Ei luovutuksia |
| **Säilytysaika** | Tunnukset: käyttöoikeuden päättyminen + 6 kk; loki: 2 vuotta |
| **Sovellus / tallennus** | Kaikki sovellukset; Supabase `globaali_data` (kayttajat), `loki` |

---

## Muutoshistoria

| Päivä | Muutos |
|---|---|
| 15.10.2026 | Ensimmäinen versio (KT1–KT8). Terveystarkastustiedot rajattu työnjohdolle (T3). |
