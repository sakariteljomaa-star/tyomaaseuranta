# GDPR-arviointi — Työmaaseurantajärjestelmä

**Laadittu:** 15.10.2026 · **Rekisterinpitäjä:** Uudenmaan Asbestipurku Oy (2817254-1)

> Tämä on käytännön tietosuoja-arviointi, ei juridinen lausunto. Kohdat merkinnällä
> *[tarkistettava]* kannattaa varmistaa juristilta, tilitoimistolta tai viranomaisohjeista.

---

## 1. Johtopäätös

1. **Järjestelmä on henkilötietorekisteri** ja yritys on **rekisterinpitäjä**.
2. Keskeiset tiedot (veronumero, työmaalla olo) perustuvat **lakisääteiseen velvoitteeseen** —
   vahvin mahdollinen peruste. Kerääminen on pakollista, ei vapaaehtoista.
3. Järjestelmä käsittelee **vähäisessä määrin terveyteen liittyviä tietoja** (terveystarkastuksen
   päivä ja voimassaolo asbestityöntekijöille) → erityinen henkilötietoryhmä (9 art.),
   lisävaatimukset työelämän tietosuojalaista.
4. **Tietosuojavastaavaa (DPO) ei vaadita** — pieni yritys, ei laajamittaista erityisdatan käsittelyä.
5. **Vaikutustenarviointia (DPIA) ei todennäköisesti vaadita** — pieni mittakaava, ei
   järjestelmällistä valvontaa. *[tarkistettava, jos terveystietojen määrä kasvaa]*
6. **Suurimmat puutteet:** US-hostaus (siirto EU:n ulkopuolelle), puuttuva käsittelytoimien
   seloste, terveystietojen pääsynhallinta, automaattisen poiston puuttuminen.

---

## 2. Henkilötietojen inventaario

| Tieto | Sovellus | Tallennus | Peruste | Herkkyys |
|---|---|---|---|---|
| Nimi, veronumero, syntymäaika, työnantaja + Y-tunnus, työsuhde, kansalaisuus | Tuntikirja | Supabase `globaali_data` (aliurakoitsijat) | Lakisääteinen | 🟠 Korkea |
| Työmaalla olopäivät, työtunnit, kommentit, hyväksyntä | Tuntikirja | Supabase `projekti_data` | Sopimus / lakisääteinen | 🟡 Keskitaso |
| Osoite, puhelin | Tuntikirja | Supabase | Oikeutettu etu | 🟡 Keskitaso |
| Aliurakoitsijan Y-tunnus, yhteyshenkilö, maksut | Kustannusseuranta | Supabase `globaali_data` | Lakisääteinen | 🟢 Matala (yritystieto) |
| Terveystarkastus-, tiiviystesti- ja koulutuspäivät | Asbestikohteet | Supabase `globaali_data` (asbesti_patevyydet) | 9.2 b + lakisääteinen | 🔴 Erityinen |
| Kuvat työmaalta (voi sisältää henkilöitä) | Asbestikohteet | Supabase Storage | Oikeutettu etu | 🟡 Keskitaso |
| Kaluston luovuttajan nimi | Kalusto | Supabase | Oikeutettu etu | 🟢 Matala |
| Käyttäjätunnus, nimi, rooli, salasanatiiviste | Kaikki | Supabase | Oikeutettu etu | 🟡 Keskitaso |
| Toimintaloki | Kaikki | Supabase `loki` | Oikeutettu etu | 🟢 Matala |
| **Ladatut Excel/CSV-ilmoitukset** (sis. veronumerot) | Tuntikirja, Kustannus | **Käyttäjän laite** | — | 🟠 Korkea |

---

## 3. Rekisterinpitäjän velvoitteet — tilanne

| Velvoite | GDPR | Tila | Huomio |
|---|---|---|---|
| Oikeusperuste jokaiselle käsittelylle | 6, 9 art. | ✅ | Dokumentoitu tietosuojaselosteessa |
| Informointi rekisteröidyille | 13, 14 art. | ⚠️ | Seloste päivitetty — **jakelu työntekijöille puuttuu** (T4) |
| Käsittelytoimien seloste | 30 art. | ❌ | **Puuttuu** (T2) |
| Tietoturva | 32 art. | ✅ | PBKDF2, RLS, roolit, loki, HTTPS |
| Käsittelysopimukset (DPA) | 28 art. | ⚠️ | Supabase/Streamlit/Google DPA:t **varmistamatta** (T1) |
| Siirrot EU:n ulkopuolelle | 44–49 art. | ⚠️ | Streamlit USA — **peruste varmistamatta** (T1) |
| Säilytysajan rajaus | 5.1 e | ⚠️ | Määritelty — **automaattinen poisto puuttuu** (T6) |
| Rekisteröidyn oikeudet | 15–22 art. | ⚠️ | Manuaalisesti hoidettavissa — ei henkilökohtaista vientiä (T7) |
| Terveystietojen käsittely | 9 art. + TyöTSL 5 § | ⚠️ | **Katselija-rooli näkee** (T3) |
| Tietoturvaloukkausten ilmoittaminen | 33, 34 art. | ⚠️ | Toimintamalli puuttuu (T5) |
| Sisäänrakennettu tietosuoja | 25 art. | ✅ | Työntekijä ei näe muiden tietoja; viranomaistiedot vain TJ:lle |

---

## 4. Riskit

### R1 — Henkilötietojen siirto Yhdysvaltoihin 🔴
Streamlit Community Cloud (Snowflake Inc.) ajaa sovelluksia USA:ssa. Data tallennetaan
EU:hun, mutta veronumerot ja terveystiedot käsitellään US-palvelimen muistissa.
**Lievennys:** jos Snowflake on sertifioitu EU–US Data Privacy Frameworkiin ja sen
käsittelysopimus kattaa Community Cloudin, siirto on sallittu. Muussa tapauksessa
EU-hostaus (esim. Hetzner Saksa, n. 5–10 €/kk).

### R2 — Terveystietojen liian laaja näkyvyys 🟠
Asbesti-appin Pätevyydet-välilehti näkyy myös katselija-roolille. Työelämän
tietosuojalain 5 §: terveydentilatietoja saavat käsitellä vain ne, jotka tekevät
niiden perusteella päätöksiä, ja heidät on nimettävä.

### R3 — Ladatut ilmoitustiedostot käyttäjien laitteilla 🟠
Excel/CSV-ilmoitukset sisältävät veronumerot. Ne jäävät latauskansioon, sähköpostiin
ja mahdollisesti pilvitallennukseen.

### R4 — Ei automaattista poistoa 🟡
Tiedot jäävät järjestelmään säilytysajan jälkeenkin, ellei niitä poisteta käsin.

### R5 — Aliurakoitsijan toimittamat tiedot 🟡
Päätoteuttaja saa aliurakoitsijan työntekijöiden tiedot työnantajalta. Työntekijöitä
on informoitava (14 art.) — käytännössä aliurakkasopimuksessa ja perehdytyksessä.

### R6 — Sähköpostin käyttö raporteissa 🟡
Asbesti-appi lähettää raportteja Gmailin kautta. Raportit eivät sisällä veronumeroita,
mutta voivat sisältää nimiä ja kuvia.

---

## 5. Toimenpidelista

| # | Toimenpide | Prioriteetti | Vastuu | Tila |
|---|---|---|---|---|
| **T1** | **Selvitä Streamlit/Snowflaken DPA ja siirtoperuste** — onko Snowflake DPF-sertifioitu, kattaako DPA Community Cloudin, salliiko Community Cloudin käyttöehto henkilötiedot. Tarkista samalla Supabasen ja Googlen DPA:t. Jos ei kattavaa perustetta → EU-hostaus. | 🔴 Korkea | Sakari | ⏳ Kesken |
| **T2** | Laadi **käsittelytoimien seloste** (30 art.) — voi pohjautua tämän dokumentin kohtaan 2 | 🔴 Korkea | Sakari / Claude | ☐ |
| **T3** | **Rajaa Pätevyydet-välilehti** vain työnjohdolle (admin + työnjohtaja), piilota katselijalta. Nimeä terveystietoja käsittelevät henkilöt. | 🔴 Korkea | Claude (koodi) | ☐ |
| **T4** | **Informoi työntekijät** — lyhyt tietosuojailmoitus perehdytykseen ja aliurakkasopimuksiin (liite: "päätoteuttaja käsittelee työntekijöidenne tietoja lakisääteisiin ilmoituksiin") | 🟠 Keskitaso | Sakari | ☐ |
| **T5** | Laadi **tietoturvaloukkauksen toimintamalli**: kuka tekee mitä, ilmoitus Tietosuojavaltuutetulle 72 h kuluessa | 🟠 Keskitaso | Sakari | ☐ |
| **T6** | **Automaattinen poisto/anonymisointi** säilytysaikojen mukaan (esim. ylläpitotoiminto adminille) | 🟡 Matala | Claude (koodi) | ☐ |
| **T7** | **Henkilön tietojen vienti** tarkastuspyyntöjä varten (admin: "vie kaikki henkilön X tiedot") | 🟡 Matala | Claude (koodi) | ☐ |
| **T8** | Ohjeista: **ladatut ilmoitustiedostot** poistetaan laitteelta lähetyksen jälkeen, ei lähetetä salaamattomana sähköpostina | 🟡 Matala | Sakari | ☐ |
| **T9** | Varmista **säilytysajat**: verodata 6 v (verotusmenettelylaki), ASA-velvoitteet asbestityössä | 🟡 Matala | Sakari / tilitoimisto | ☐ |

---

## 6. Avoimet kysymykset *[tarkistettava]*

1. **Streamlit Community Cloud:** salliiko käyttöehto henkilötietojen käsittelyn, ja kattaako
   Snowflaken DPA ilmaistason? (T1)
2. **Rakentamisen tiedonantovelvollisuus:** tarkka säilytysaika ilmoitetuille tiedoille
   (oletus 6 v, verotusmenettelylaki).
3. **ASA-rekisteri:** asbestityölle altistuvien luettelon säilytysvelvoite (Työterveyslaitos) —
   koskeeko se myös järjestelmän pätevyystietoja vai hoidetaanko ASA-luettelo erikseen?
4. **Aliurakoitsijan rooli:** onko aliurakoitsija itsenäinen rekisterinpitäjä omista
   työntekijöistään (todennäköisesti kyllä) — riittääkö sopimusehto tietojen toimittamisesta.

---

## 7. Seuraava tarkistus

Arviointi päivitetään, kun:
- hostausratkaisu muuttuu (T1)
- järjestelmään lisätään uusia henkilötietoja tai sovelluksia
- viimeistään **10/2027**
