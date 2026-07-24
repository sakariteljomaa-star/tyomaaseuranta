# Netvisor API -tunnusten pyyntö

Valmis viesti Netvisorin asiakastukeen. Kopioi sähköpostiin tai käytä
puhelinmuistilistana. Täydennä hakasulkeissa olevat kohdat.

---

## Sähköpostiversio

**Vastaanottaja:** Netvisorin asiakastuki (asiakaspalvelu@netvisor.fi tai tuen kautta)
**Aihe:** API-rajapinnan käyttöönotto — Uudenmaan Asbestipurku Oy (2817254-1)

---

Hei,

Haluaisimme ottaa käyttöön Netvisorin API-rajapinnan omaa integraatiota varten.

**Yritys**
- Uudenmaan Asbestipurku Oy
- Y-tunnus: 2817254-1
- Yhteyshenkilö: Sakari Teljomaa
- Sähköposti: [sähköpostisi]
- Puhelin: [puhelinnumerosi]

**Käyttötarkoitus**
Olemme rakentaneet oman työmaakohtaisen kustannusseurantasovelluksen. Se hakee
tällä hetkellä tiedot käsin viedyistä Excel-tiedostoista, ja haluaisimme
automatisoida haun rajapinnan kautta.

**Mitä tietoja haemme (vain luku)**
1. **Ostolaskut** laskentakohteineen (vastaa Laskentakohderaporttia) — kulujen
   kohdistus työmaittain, ALV-tunnukset (KOOS/RAOS)
2. **Myyntilaskut** — laskutus ja avoimet saatavat
3. **Tuntikirjanpito** — työtunnit (vain tuntimäärät, ei palkkatietoja)

**Mitä tarvitsemme teiltä**
- **Partner ID** ja **Partner Key**
- Ohjeet **Customer ID:n** ja **Customer Key:n** luomiseen omissa yritysasetuksissamme
- **Sender-tunniste** (integraation nimi), jos se pitää rekisteröidä

**Oikeudet**
Pyydämme integraatiolle **vain lukuoikeudet** yllä mainittuihin tietoihin.
Emme tarvitse kirjoitus-, maksu- tai muokkausoikeuksia.

**Kysymykset**
1. Onko API-rajapinnan käyttöönotossa kertaluonteista tai kuukausittaista kustannusta?
2. Mitkä ovat tarkat vaiheet, jotta saamme rajapinnan käyttöön?
3. Onko rajapinnan käytössä kutsumäärärajoituksia?
4. Mistä löydän API-dokumentaation (endpointit ja kenttäkuvaukset)?

Kiitos jo etukäteen!

Ystävällisin terveisin,
Sakari Teljomaa
Uudenmaan Asbestipurku Oy
[puhelin] · [sähköposti]

---

## Puhelinmuistilista

Jos soitat, käy nämä läpi:

**Kerro ensin**
- Yritys: Uudenmaan Asbestipurku Oy, Y-tunnus 2817254-1
- "Haluamme ottaa API-rajapinnan käyttöön omaa integraatiota varten"

**Pyydä nämä 5 asiaa**
1. ☐ Partner ID
2. ☐ Partner Key
3. ☐ Ohje Customer ID:n ja Customer Key:n luomiseen (yritysasetukset)
4. ☐ Sender-tunniste (integraation nimi) — pitääkö rekisteröidä?
5. ☐ Linkki API-dokumentaatioon

**Korosta**
- ☐ **Vain lukuoikeudet** (ostot, myynti, tuntikirjanpito) — ei kirjoitus/maksu

**Kysy**
- ☐ Maksaako rajapinnan käyttöönotto?
- ☐ Mitkä vaiheet tarvitaan aktivointiin?
- ☐ Onko kutsumäärärajoituksia?

**Kirjaa ylös**
- Partner ID: ______________________
- Partner Key: ______________________ (älä lähetä sähköpostilla, pyydä turvallisesti)
- Sender: ______________________
- Customer ID: ______________________
- Customer Key: ______________________

---

## Kun saat tunnukset

Lisää ne kustannusseurannan **Streamlit Secretsiin** (⋮ → Settings → Secrets):

```toml
[netvisor]
sender          = "Integraation nimi"
partner_id      = "..."
partner_key     = "..."
customer_id     = "..."
customer_key    = "..."
organisation_id = "2817254-1"
```

Sitten sovelluksessa: sivupalkki → **🔄 Hae Netvisorista** → **🔌 Testaa yhteys**.

⚠️ **Älä laita avaimia koodiin, GitHubiin tai chattiin** — vain Streamlit Secretsiin.
Ks. `TIETOTURVA.md`.
