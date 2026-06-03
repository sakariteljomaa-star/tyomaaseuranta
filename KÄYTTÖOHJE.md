# Käyttöohje — Työmaaseuranta

Uudenmaan Asbestipurku Oy:n työmaaseurantajärjestelmä koostuu **kolmesta sovelluksesta**.
Kaikki toimivat selaimessa, myös puhelimella. Sama käyttäjätunnus toimii kaikissa.

---

## Sovellukset ja osoitteet

| Sovellus | Mihin | Osoite |
|----------|-------|--------|
| 💰 **Kustannusseuranta** | Netvisor-kulujen seuranta, Excel-raportit | _(täydennä julkaistu osoite)_ |
| 👷 **Tuntikirja** | Aliurakoitsijoiden tunnit ja hyväksyntä | _(täydennä)_ |
| 🔧 **Kalustoseuranta** | Koneiden seuranta QR-koodilla | _(täydennä)_ |

> 💡 Lisää osoite puhelimen kotinäytölle: Safari/Chrome → Jaa → "Lisää kotivalikkoon".
> Sovellus avautuu kuin tavallinen appi.

---

## Roolit — kuka näkee mitä

| Rooli | Kustannukset | Tunnit | Kalusto |
|-------|:---:|:---:|:---:|
| **Pääkäyttäjä** | kaikki | kaikki | kaikki |
| **Työnjohtaja** | ✅ | hyväksyy tunnit | hallinta |
| **Kirjanpitäjä** | katselu | katselu | katselu |
| **Työntekijä** | ei pääsyä | omat tunnit | QR-skannaus |

Pääkäyttäjä lisää käyttäjät **👤 Käyttäjät** -välilehdeltä (näkyy vain pääkäyttäjälle).

---

## 👷 Tuntikirja — työnkulku

**Aliurakoitsija / työntekijä:**
1. Kirjaudu omalla tunnuksella
2. Valitse viikko sivupalkista
3. **⚡ Pikasyöttö** — täytä tunnit päivittäin (puhelimella numeronäppäimistö aukeaa)
4. Lisää halutessasi päiväkohtaiset huomiot
5. **💾 Tallenna kaikki**

**Työnjohtaja:**
1. **📊 Viikkoyhteenveto** → näe kaikki kirjaukset
2. Hyväksy tunnit (✅), pyydä selvitystä (⚠️) tai palauta (🔄)
3. Kirjoita tarvittaessa kommentti työntekijälle
4. **Hyväksytyt tunnit lukittuvat** — työntekijä ei voi enää muokata
5. Lataa viikkoraportti Excel/PDF:nä

**Kieli:** vaihda 🇫🇮 / 🇷🇺 sivupalkin yläreunasta.

---

## 🔧 Kalustoseuranta — työnkulku

**Käyttöönotto (pääkäyttäjä):**
1. **📥 Tuo Excel** → lataa Kalustonhallinta-tiedosto (tunnistaa AP-, IH- jne. automaattisesti)
2. **📱 QR-koodit** → valitse koko → **Luo tarra-PDF** → tulosta → kiinnitä koneisiin
   - Pieni = käsikoneet · Keskikoko = imurit · Iso = alipaineistajat
   - Käytä säänkestävää tarramateriaalia

**Työmaalla (kuka tahansa, ei kirjautumista):**
1. Skannaa koneen QR-koodi puhelimella
2. Laitekortti avautuu → **Ota käyttöön** (kirjaa työmaa) tai **Palauta varastolle**
3. Vikatilanteessa **🔴 Ilmoita viasta**

**Seuranta (työnjohtaja):**
- **📊 Tilannekuva** → missä kukin laite on, montako varastossa/työmaalla, viat

---

## 🔄 Netvisor-automaattihaku (kustannusseuranta)

Sen sijaan että viet XLSX-tiedostoja käsin, kustannusseuranta voi hakea laskut
**suoraan Netvisorista** napilla. Vaatii kertaluonteisen asennuksen.

**Asennus (kerran):**
1. Netvisorissa: **Yritysasetukset → Rajapinta / Integraatiot** → luo integraatiotunnukset
2. Saat: Sender, Customer ID + Customer key, Partner ID + Partner key
3. Lisää ne kustannusseurannan Streamlit Secretsiin:
```toml
[netvisor]
sender          = "Integraation nimi"
partner_id      = "..."
partner_key     = "..."
customer_id     = "..."
customer_key    = "..."
organisation_id = "2817254-1"
```

**Käyttö:**
1. Sivupalkki → **🔄 Hae Netvisorista**
2. **🔌 Testaa yhteys** (varmista että tunnukset toimivat)
3. Valitse aikaväli → **⬇️ Hae laskut**
4. Ostot, jätemaksut, aliurakoitsijat, kalusto ja myynti täyttyvät automaattisesti

> ⚠️ Kenttien kohdistus (ALV-tunnus, laskentakohde) voi vaatia pientä hienosäätöä
> ensimmäisen oikean haun jälkeen — kerro jos jokin sarake näyttää väärältä.

---

## 💰 Kustannusseuranta — työnkulku

1. Kirjaudu (työnjohtaja/kirjanpitäjä/pääkäyttäjä — ei työntekijä)
2. Jokaisella välilehdellä oma **📥 Tuo Netvisorista** -lataus:
   - Myynti → Myyntireskontra-XLSX
   - Ostot/Jätemaksut/Aliurakoitsijat/Kalusto → Laskentakohderaportti-XLSX
   - Tuntiseuranta → Tuntikirjanpito-XLSX
3. Sovellus luokittelee automaattisesti (KOOS/RAOS, Urakka/Lisätyö)
4. **📊 Yhteenveto** → kokonaiskuva + ALV-kohtelu
5. **Lataa kustannusseuranta Excelinä**

---

## Tärkeää muistaa

- 🔑 **Pääkäyttäjän salasana talteen** — sen palautus vaatii teknistä työtä.
- 🔒 Kaikki data tallentuu pilveen (Supabase, EU) ja säilyy automaattisesti.
- 👤 Sama tunnus kaikkiin kolmeen sovellukseen.
- 📱 Toimii puhelimella, tabletilla ja tietokoneella.
- 🗑️ Tietosuoja: tiedot poistetaan 6 kk projektin päättymisen jälkeen (ks. TIETOSUOJASELOSTE.md).

---

## Vianetsintä

| Ongelma | Ratkaisu |
|---------|----------|
| "Invalid API key" / tallennusvirhe | Tarkista että Streamlit Secretsissä on **secret**-avain (`sb_secret_...`) |
| QR-koodi vie localhostiin | Päivitä kalustoseurannan secrets `[kalusto] app_url` oikeaksi |
| Työntekijä ei näe projektia | Pääkäyttäjä: lisää projekti työntekijän "sallitut projektit" -listaan |
| En pääse kustannusseurantaan | Työntekijä-roolilla ei ole pääsyä (sisältää palkkatiedot) |
| Unohdin salasanan | Pääkäyttäjä voi nollata sen 👤 Käyttäjät -välilehdeltä |
