# Cateva-dokumenttipohjat

Rakenteet purettu käyttäjän toimittamista mallidokumenteista 4.8.2026. Tätä tiedostoa
käytetään asbesti_app.py:n dokumenttigeneroinnin määrittelynä — kenttänimet ja
osiojärjestys pidetään täsmälleen näiden mukaisina.

Malliketju on yksi todellinen case (Koroistentie 8 C 19, Helsinki / As Oy Tilkanrinne):
Catevan asbestikartoitus → purkutyön dokumentointi → kuivaus → puhdastilamittaus.

---

## 1. Asbestipurkutyön aloitus- ja lopetusraportti (OMA pohja — päädokumentti Catevalle)

Malli: `asbestipurkutyon_aloitus-_ja_lopetusraportti_raaseporintie37_220726-3.pdf`

**Ylätunniste:** yrityksen logo + "ASBESTIPURKUTYÖN ALOITUS- JA LOPETUSRAPORTTI" +
alaotsikko (kohderyhmä) + sivunumero muodossa `1(6)`.
**Alatunniste:** Uudenmaan Asbestipurku Oy · Rattitie 24, 00770 Helsinki ·
Y-tunnus 2817254-1 · www.uudenmaanasbestipurku.fi · Puhelin 044 300 9672.

**Sivu 1 — perustiedot:**
| Osio | Kentät |
|------|--------|
| Otsikko | Kohteen nimi/osoite + päivämäärä. Cateva-kohteissa lisäksi **Catevan työnumero/yksilöintiviite** |
| Osallistujat | nimi + yritys, useita rivejä |
| Aikataulu | Työmaan alkamispäivä, Työmaan lopettamispäivä |
| Vastuuhenkilöt ja yhteystiedot | Asbestiurakoitsija + vastuuhenkilö, Päätoteuttaja + vastuuhenkilö |
| Huomiot asbestipurkutyön aloituksesta ja lähtötilanteesta | vapaa teksti: aloitus/lopetus, lähtötilanteen kuvaus, viite "(Ks. kuvat 1–N)" |

**Kuvaliitesivut:** 4 kuvaa per sivu (2×2), jokaisessa numeroitu kuvateksti
"Kuva N — teksti". Kuvajärjestys: aloituskuvat (lähtötilanne, suojaukset/osastointi,
alipaineistus, paine-eromittarin lukema, kalusto) → työnaikaiset → lopetuskuvat.

**Liitteet raportin perään (PDF:t yhdistetään samaan tiedostoon):**
1. Ilma-analyysivastaus laboratoriolta (puhdastilamittaus)
2. Kuljetusrinki Oy:n todistus asbestipitoisen jätteen loppusijoituksesta

---

## 2. Asbestipurkutyön turvallisuussuunnitelma (OMA pohja, 4 sivua)

Malli: `asbestipurkutyon_turvallisuussuunnitelma_yle_lahetyskeskus_a-osa_1_krs_030626-2.pdf`

Sama ylä-/alatunniste kuin raportissa. Suurin osa tekstistä on **vakiotekstiä**
(lakiviittaukset, toimintaohjeet) — vain alla merkityt kentät muuttuvat kohteittain.

| Osio | Muuttuvat kentät |
|------|------------------|
| Otsikko | kohteen nimi + pvm |
| Osallistujat | nimi, yritys, rooli |
| Perustiedot | Tarkenne (kuvaus löydöksestä), Osastointi (osastoidaan / ei osastoida) |
| 1. Altistuksen arviointi | Purettava asbestipitoinen materiaali, Asbestin sijainti, Purkutyömenetelmä, Menetelmän kuvaus, Altistumisalueen rajaaminen. Loppu vakiotekstiä. |
| 2. Henkilösuojainten valinta | kohdekohtainen suojainteksti |
| 3. Työvälineiden käsittely | vakioteksti |
| 4. Asbestijätteen käsittely | vakioteksti + **Jätteiden lopullinen sijoituspaikka** |
| 5. Purkutyöalueen puhtauden varmistaminen | Ilmamittauksen suorittaja kohteessa, Näytteen analysointipaikka |
| 6. Hätätilanteessa toimiminen | vakioteksti |
| 7. Suunnitelman seuranta | Työn suorittajan vastuuhenkilö, Tilaajan vastuuhenkilö, Tarvittavat päivitykset (henkilö) |
| Allekirjoitussivu | allekirjoittaja + titteli |

---

## 3. Asbestipurkutyön ennakkoilmoitus (AVI) — kenttälista

Malli: ennakkoilmoitus 834726 (turvallisuussuunnitelma-PDF:n liitteenä).
Jätetään AVIn sähköiseen asiointiin käsin — järjestelmä tuottaa **esitäytön**,
josta tiedot kopioidaan. Määräaika: 7 vrk ennen työn aloitusta (VNa 798/2015).

- **Ilmoittaja:** etunimi, sukunimi, puhelin, sähköposti
- **Suorittaja (vakio):** Uudenmaan Asbestipurku Oy, 2817254-1, Rattitie 24 00770 Helsinki, 044 300 9672, info@uudenmaanasbestipurku.fi
- **Tilaaja:** yritys, Y-tunnus, yhteyshenkilö, osoite, puhelin, sähköposti (Cateva-kohteissa Cateva Oy, 1927433-5)
- **Kohde:** työmaan nimi, yksilöidyt alueet, osoite, postinumero/-toimipaikka, sijaintikunta, työn alkamis- ja päättymispäivä
- **Asbestikartoitus:** havainnot (sijainti, määrä, laatu), kartoituksen suorituspäivä, kartoittajan nimi + Y-tunnus + yhteystiedot → poimitaan Catevan kartoitusraportista
- **Purkumenetelmä:** valinta (osastointi / purkupussi / kokonaisena irrottamalla / upotus / märkäpurku / muu) + kuvaus
- **Ilmankäsittelylaitteet:** nimi/malli, sarjanumero, ilmamäärä/teho, suodatusteho testattu pvm → poimitaan kalustorekisteristä (`kalusto_laitteet`)
- **Purkutyöntekijät (per henkilö):** etunimi, sukunimi, terveydentila sopiva -kuittaus, terveystarkastus pvm + voimassaolo, pätevyysrekisterissä-kuittaus, työnantaja, hengityksensuojaimen tiiviystestaus pvm, todistus erityisestä opetuksesta pvm → poimitaan pätevyysrekisteristä
- **Suojaus- ja puhdistautumislaitteet:** nimi, lisätiedot, suodatustesti pvm
- **Jätteenkäsittely:** jätteenkäsittelylaitos (esim. Kiimassuon jätekeskus Forssa, Kuljetusrinki Oy)
- **Liitteet:** kalustoluettelo

---

## 4. Catevan asbesti- ja haitta-ainekartoitusraportti (LÄHTÖTIETO meille)

Mallit: `6573160_...pdf`, `5898886_...pdf`. **Catevan viitenumero on tiedostonimen
alussa** (esim. 6573160) — käytetään yksilöintiviitteenä ellei muuta anneta.

Poimittavat tiedot:
- Yleistiedot: kohde, osoite, tilaaja, näytteenottaja
- Kohdekuvaus: rakennustyyppi, rakennusvuosi, tutkitut rakenteet
- Näytteet joissa asbestia: numero, sijainti, materiaali, asbestilaatu
- Massaluettelo: tulos (K/E), sijainti, laatu (V/S), kunto (A–D), pölyävyys, toimenpide-ehdotus (0–8)
- Toimenpide-ehdotuskoodit 1–7 = luvanvaraista asbestipurkua

Catevan oma "Purkutyön dokumentointi" -raportti (malli `6005036_...pdf`) on
huonekohtainen kuvat + kuvatekstit -formaatti — meidän raporttimme kuvaliitteet
noudattavat samaa tyyliä, joten ne istuvat Catevan dokumentaatioon suoraan.

---

## 5. Liitteiden hyväksymiskriteerit

- **Puhdastilamittaus (ilma-analyysivastaus):** hyväksytty kun tulos ≤ 0,01
  asbestikuitua/cm³ (VNa 798/2015). Laboratorioita malleissa: Labroc Oy, LAB-ACE Oy.
- **Labrocin raporttityypit erotetaan tiedostonimestä:** `<projektinro> <kohde> ASB_ilma.pdf`
  = ilmanäyte eli puhdastilamittaus (ainoa joka kelpaa aloitus- ja lopetusraportin
  liitteeksi); `<projektinro> <kohde> ASB.pdf` = materiaalinäytteen asbestianalyysi
  (kartoitusvaiheen tieto, EI puhdastilamittaus). Tulokset saapuvat osoitteeseen
  info@uudenmaanasbestipurku.fi lähettäjältä laboratorio.helsinki@labroc.fi, aihe
  "Tutkimustuloksia kohteesta: <kohde>", ja Apps Script kopioi PDF:t Driven
  Labroc-tulokset-kansioon automaattisesti.
- **Jätetodistus:** Kuljetusrinki Oy:n todistus asbestipitoisen jätteen
  loppusijoituksesta.

---

## Huomio laadusta

Mallidokumenteissa on käsin tekemisen jälkiä: liitteen ilmanäytteessä eri osoite kuin
raportin kannessa (Raaseporintie 34 vs. 37) ja lopetusvuodeksi kirjattu 2028 po. 2026.
Generoinnissa kaikki kohdetiedot tulevat aina kohderekisteristä — samaa tietoa ei
koskaan kirjoiteta käsin kahteen paikkaan.
