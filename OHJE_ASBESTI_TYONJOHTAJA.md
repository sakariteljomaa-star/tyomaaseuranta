# Asbestikohteet-appi — työnjohtajan ohje

Osoite: **uap-asbesti.streamlit.app** · Kirjaudu samoilla tunnuksilla kuin muihin appeihin.
Kohteen tila näkyy värillisenä merkkinä ja etenee itsestään:
Uusi → Ilmoitukset tehty → Työ käynnissä → Purku valmis → Mittaukset ja jäte ok → Raportti lähetetty.

## 1. Uusi työ → luo kohde

**Kohteet-välilehti → Lisää kohde.**
- **Työnumero** = tilaajan viite tai oma juokseva numero (esim. tilauksesta tai
  kartoitusraportin tiedostonimestä). Pakollinen — kaikki kuvat, dokumentit ja
  sähköpostit kulkevat sen alla.
- **Tilaaja:** valitse aiempi tilaaja listasta (tiedot täyttyvät) tai kirjoita uusi.
  **Sähköposti on tärkeä** — tarjoukset ja raportit lähetetään siihen.
- Osoite, kunta, suunniteltu aloitus ja lopetus, työntekijät (he näkevät kohteen
  puhelimellaan heti), kuvaus = kartoituksen löydökset.

## 2. Ilmoitukset — viimeistään 7 vrk ennen aloitusta

**Ilmoitukset-välilehti**, valitse kohde.
1. Täytä työn tiedot (materiaali, sijainti, menetelmä, jätteen sijoituspaikka…) ja
   valitse työntekijät pätevyysrekisteristä sekä laitteet kalustorekisteristä.
   **Tallenna ilmoitustiedot.**
2. **Luo turvallisuussuunnitelma (PDF)** — lataa ja anna tiedoksi työntekijöille ja
   päätoteuttajalle.
3. **Luo ennakkoilmoituksen esitäyttö (PDF)** — jätä ilmoitus AVIn sähköiseen
   asiointiin esitäytön tiedoilla ja **kuittaa jätetyksi** appissa.

Punainen varoitus tarkoittaa: aloitukseen alle 7 vrk eikä ilmoitusta ole kuitattu.
Älä aloita työtä ennen kuin varoitus on poissa.

## 3. Työmaa dokumentoi (työntekijät puhelimella)

Työntekijä kirjautuu puhelimella, valitsee kohteen (kieli FI/RU) ja kuvaa
tarkistuslistan mukaan:
- **Aloitus (5 pakollista):** lähtötilanne · suojaukset ja osastointi ·
  alipaineistaja · paine-eromittarin lukema · kalusto
- **Lopetus:** kuvat puretusta tilasta + havainnot + **Kuittaa purku valmiiksi**

Punainen kohta = kuva puuttuu. Kun kaikki aloituskohdat on kuvattu, tila siirtyy
automaattisesti "Työ käynnissä" — sinun ei tarvitse tehdä mitään.

## 4. Puhdastilamittaus ja jätetodistus

- **OmaLabroc-tilaukseen kohteen nimeksi AINA kohteen työnumero** — silloin tulos
  kohdistuu automaattisesti oikeaan kohteeseen.
- **Labroc-tulokset-välilehti → Hae uudet tulokset** → tarkista ja tallenna
  kohteelle. 🟢 = hyväksytty (≤ 0,01 kuitua/cm³), 🔴 = hylätty, 🟠 = tarkista käsin.
  Muun laboratorion tuloksen voi ladata käsin Raportti-välilehdellä.
- **Kuljetusringin siirtoasiakirja** ladataan Raportti-välilehdellä.

## 5. Raportti ja lähetys

**Raportti-välilehti**, valitse kohde.
- Appi näyttää puutelistan — raporttia ei voi koota ennen kuin kaikki on koossa.
- **Kokoa aloitus- ja lopetusraportti (PDF)** → **lataa ja tarkista** (kuvat,
  tekstit, liitteet) → ruksi "Olen esikatsellut" → **Lähetä tilaajalle**.
- Jos tarkistustila on päällä (Secrets `[smtp] tarkistusosoite`), viesti menee ensin
  osoitteeseen info@uudenmaanasbestipurku.fi otsikolla *[TARKISTUS → tilaajan osoite]*
  — välitä sieltä tilaajalle. Ilman tarkistustilaa viesti menee suoraan tilaajalle ja
  kopio omaan postilaatikkoon.

## 6. Pidä kunnossa

- **Pätevyydet-välilehti:** työntekijöiden terveystarkastukset, tiiviystestaukset
  ja koulutukset. Appi varoittaa 60 vrk ennen vanhenemista — vanhentunut pätevyys
  näkyy punaisena Kohteet-välilehdellä.
- Kalustorekisteri (Kalustoseuranta-appi) ajan tasalla → laitteet sarjanumeroineen
  siirtyvät ennakkoilmoitukseen napista.
