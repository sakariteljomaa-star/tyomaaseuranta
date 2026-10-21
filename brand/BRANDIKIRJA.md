# UAP-brändikirja

Uudenmaan Asbestipurku Oy · perustettu 2017 · Y-tunnus 2817254-1
**Slogan:** "Hallittua purkua, mitattavaa puhtautta."
**Alarivi:** "Dokumentoitu asbestipurku". Älä käytä sanaa "sertifioitu".

Brändisuunta on **1a "Puhdas", kliininen tarkkuus (vaalea)**. Asbestipurku esitetään laboratorion
täsmällisyydellä: mitattavaa puhtautta, ei purkuvoimaa. Tumma suunta 1b ("Auktoriteetti") ei ole
käytössä.

---

## 1. Tunnus: UAP-merkki 4c

<img src="svg/uap-merkki-vari.svg" alt="UAP-merkki" width="96"> &nbsp;
<img src="svg/uap-merkki-sovelluskuvake.svg" alt="UAP-sovelluskuvake" width="96">

UAP-kirjaimet kehyksessä ja niiden alla neljä nousevaa pylvästä (kasvu, mitattavuus).
Korvaa aiemman UAP-laatikon ja vanhan keltaisen sanalogon.

| Tiedosto | Käyttö |
|---|---|
| `svg/uap-merkki-vari.svg` | **Pääversio** vaalealla pohjalla |
| `svg/uap-merkki-negatiivi.svg` | Tummalla pohjalla (syväpetroli tai kuva) |
| `svg/uap-merkki-musta.svg` | Yksivärinen painatus, leimat |
| `svg/uap-merkki-valkoinen.svg` | Valkoinen yksivärinen tummalle tai kuvalle |
| `svg/uap-merkki-sovelluskuvake.svg` | Favicon, sovelluskuvake, somen profiilikuva |
| `png/…-512/-1024/-2048.png` | Samat rasterina, läpinäkyvä tausta |

**Nimen kanssa:** nimi merkin oikealle puolelle, väli ¼ merkin leveydestä. Teksti on
"Uudenmaan / Asbestipurku Oy" Hanken Groteskilla painolla 700, rivinkorkeus 1,05. "Oy" painolla
500 värillä `#7A888B`. Nimen korkeus on noin 60 % merkin korkeudesta.

**Suoja-alue** on ¼ merkin leveydestä. **Minimikoko** on 24 px digitaalisesti tai 8 mm painettuna.
Sitä pienemmissä käytetään sovelluskuvaketta.

**Älä** muuta pylväiden järjestystä tai korkeuksia, käytä paletin ulkopuolisia värejä tai
liukuvärejä, täytä kehystä (paitsi sovelluskuvakkeessa), venytä, kallista tai lisää varjoja.

Tarkka geometria: [LOGO-OHJE.md](LOGO-OHJE.md).

## 2. Väripaletti

| Nimi | Hex | Käyttö |
|---|---|---|
| Syväpetroli | `#14232A` | Teksti, merkin kehys |
| Klinikka | `#1F7A73` | Aksentti, painikkeet, merkin pylväät |
| Vaalea klinikka | `#3E9A92` | Pylväät tummalla pohjalla |
| Teräs | `#B7C2C4` | Toissijainen (ei tekstiväriksi vaalealla) |
| Huurre | `#DDEAE8` | Pinnat, kortit, sivupalkki |
| Luonnonvalko | `#F2F4F4` | Perusta, taustat |

```css
--uap-petroli: #14232A;  --uap-klinikka: #1F7A73;  --uap-klinikka-vaalea: #3E9A92;
--uap-teras: #B7C2C4;    --uap-huurre: #DDEAE8;    --uap-luonnonvalko: #F2F4F4;
```

## 3. Typografia

- **Hanken Grotesk:** otsikot (800), väliotsikot (600) ja leipäteksti (400).
- **IBM Plex Mono:** koodit, mitat ja pienet versaalimerkinnät laajalla välistyksellä, esim.
  `DOKUMENTOITU ASBESTIPURKU · UUSIMAA`, `<0,01 f/cm³`.

Molemmat ovat SIL Open Font License -fontteja. Sovelluksissa ne tarjoillaan omista tiedostoista
(`static/fonts/`), ei Google Fontsista.

## 4. Käyttö järjestelmässä

| Missä | Miten |
|---|---|
| Streamlit-sovellukset | Teema `.streamlit/config.toml` (värit + fontit), logo-otsikko ja favicon `brandi.py` |
| PDF-asiakirjat | Merkki ja nimi yläkulmassa (`asbesti_dokumentit.py`) |
| Esitykset ja muu visuaalinen | Tämän kirjan paletti, fontit ja merkki |

Jos merkki tai värit muuttuvat, vaihda tiedostot tähän kansioon samoilla nimillä. Sovellukset ja PDF:t
käyttävät niitä suoraan.
