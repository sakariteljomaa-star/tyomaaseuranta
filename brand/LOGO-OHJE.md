# UAP-merkki 4c · Logo-ohje

Uudenmaan Asbestipurku Oy:n tunnus. Korvaa brändiohjeen aiemman UAP-laatikon. Merkissä on UAP-kirjaimet kehyksessä, ja niiden alla on neljä nousevaa pylvästä, jotka kuvaavat kasvua ja mitattavuutta.

## Tiedostot

| Tiedosto | Käyttö |
|---|---|
| `svg/uap-merkki-vari.svg` | Pääversio vaalealla pohjalla |
| `svg/uap-merkki-negatiivi.svg` | Tummalla pohjalla (syväpetroli tai kuva) |
| `svg/uap-merkki-musta.svg` | Yksivärinen painatus, leimat, faksit |
| `svg/uap-merkki-valkoinen.svg` | Valkoinen yksivärinen tummalle tai kuvalle |
| `svg/uap-merkki-sovelluskuvake.svg` | Favicon, sovelluskuvake, somen profiilikuva |
| `png/…-512 / -1024 / -2048.png` | Samat versiot rasterina, läpinäkyvä tausta |

SVG on ensisijainen. Kirjaimet on muunnettu poluiksi, joten fonttia ei tarvita.

## Värit

| Osa | Vaalea pohja | Tumma pohja |
|---|---|---|
| Kehys + UAP | Syväpetroli `#14232A` | Luonnonvalko `#F2F4F4` |
| Pylväät | Klinikka `#1F7A73` | Vaalea klinikka `#3E9A92` |
| Pohja | Luonnonvalko `#F2F4F4` tai valkoinen | Syväpetroli `#14232A` |

## Geometria (viewBox 120 × 120)

- Kehys: 117,5 × 117,5, viiva 2,5, kulmasäde 13,75 (ulkoreuna 15)
- UAP: Hanken Grotesk ExtraBold 800, koko 39, välistys −0,03 em, keskitetty
- Pylväät: 4 kpl, leveys 7, väli 4, korkeudet 4 / 7 / 10 / 13, alareunat samalla linjalla
- Kirjainten peruslinja → pylväiden yläreuna (korkein): 10
- Kirjaimet ja pylväät muodostavat ryhmän, joka on keskitetty kehykseen pystysuunnassa

## Suoja-alue ja minimikoko

- Suoja-alue merkin ympärillä: vähintään 1/4 merkin leveydestä
- Minimikoko: digitaalinen 24 px, painettu 8 mm
- Alle 24 px:n kokoon (favicon 16 px) käytä sovelluskuvaketta

## Käyttö nimen kanssa

Merkkiä voi käyttää yksin. Kun nimi tulee viereen, se sijoitetaan merkin oikealle puolelle:

- "Uudenmaan Asbestipurku Oy", Hanken Grotesk 700, rivin korkeus 1,05, "Oy" painolla 500 ja värillä `#7A888B`
- Merkin ja nimen väli: 1/4 merkin leveydestä
- Nimen kokonaiskorkeus noin 60 % merkin korkeudesta, keskitetty pystysuunnassa

## Älä

- Älä muuta pylväiden järjestystä tai korkeussuhteita
- Älä vaihda värejä paletin ulkopuolisiin tai käytä liukuvärejä
- Älä täytä kehystä värillä (paitsi sovelluskuvakkeessa)
- Älä venytä, kallista tai lisää varjoja
- Älä sijoita merkkiä levottoman kuvan päälle ilman tummaa tai vaaleaa pohjaa

## Koodissa

```html
<img src="/brand/uap-merkki-vari.svg" alt="Uudenmaan Asbestipurku Oy" width="48" height="48">
```

```css
--uap-petroli: #14232A;
--uap-klinikka: #1F7A73;
--uap-klinikka-vaalea: #3E9A92;
--uap-teras: #B7C2C4;
--uap-huurre: #DDEAE8;
--uap-luonnonvalko: #F2F4F4;
```

## Perustiedot

Uudenmaan Asbestipurku Oy · perustettu 2017 · Y-tunnus 2817254-1
Slogan: "Hallittua purkua, mitattavaa puhtautta."
Alarivi: "Dokumentoitu asbestipurku" (älä käytä sanaa "sertifioitu")
