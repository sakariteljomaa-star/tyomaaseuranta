# Kirjautumisohje — Työmaaseuranta

Kaikissa sovelluksissa on **sama käyttäjätunnus ja salasana**. Tunnuksen saat pääkäyttäjältä
(Sakari Teljomaa). Rooli ratkaisee, mitä näet.

| Sovellus | Osoite | Kenelle |
|---|---|---|
| 👷 Tuntikirja | https://uap-tuntikirjaus.streamlit.app | työnjohto, työntekijät |
| 💰 Kustannusseuranta | https://uap-kustannus.streamlit.app | työnjohto, kirjanpito (ei työntekijät) |
| ☣️ Asbestikohteet | https://uap-asbesti.streamlit.app | työnjohto, työntekijät |
| 🔧 Kalustoseuranta | https://kalusto-uap.streamlit.app | työnjohto; työmaalla QR-koodi ilman kirjautumista |

---

## 1. Näin kirjaudut

1. Avaa sovelluksen osoite puhelimen tai tietokoneen selaimessa.
   Jos sivu näyttää "Zzz… This app has gone to sleep", paina **Yes, get this app back up** ja odota noin minuutti.
2. Kirjoita **käyttäjätunnus** (pienet ja isot kirjaimet ovat sama asia) ja **salasana**.
3. Paina **Kirjaudu**.
4. Lopuksi **Kirjaudu ulos** sivupalkista, varsinkin yhteiskäytössä olevalla laitteella.

💡 Puhelimessa: lisää sovellus kotinäytölle (Safari: Jaa → Lisää Koti-valikkoon,
Chrome: ⋮ → Lisää aloitusnäyttöön), niin se aukeaa kuin sovellus.

### Jos kirjautuminen ei onnistu

| Ilmoitus | Syy ja ratkaisu |
|---|---|
| *Väärä käyttäjätunnus tai salasana.* | Tarkista kirjoitusasu. Sama ilmoitus tulee myös, jos tunnus on poistettu käytöstä. |
| *Liian monta epäonnistunutta yritystä…* | 5 väärää yritystä → tunnus lukittuu **15 minuutiksi**. Odota tai pyydä pääkäyttäjää avaamaan lukitus. |
| *Istunto päättyi: käyttäjätunnus on poistettu käytöstä.* | Ota yhteys työnjohtoon. |
| Unohtunut salasana | Pääkäyttäjä asettaa uuden. Vanhaa ei voi palauttaa. |

### Turvallisuus
- Älä kerro salasanaasi kenellekään, älä myöskään työkaverille tai WhatsAppissa.
- Salasanassa vähintään **8 merkkiä**. Pidempi on parempi, esim. kolme sanaa ja numero.
- Älä tallenna salasanaa yhteiskäyttöisen laitteen selaimeen.

---

## 2. Työntekijälle / Для работника (fi + ru)

**Tuntikirja** — kirjaa tuntisi joka päivä tai viikon lopussa:
1. Avaa tuntikirjan osoite → kirjaudu omalla tunnuksella.
2. Valitse sivupalkista kieli (🇫🇮 Suomi / 🇷🇺 Русский) ja viikko.
3. **⚡ Pikasyöttö** → kirjoita tunnit päivittäin → **💾 Tallenna kaikki**.
4. Kun työnjohtaja on hyväksynyt viikon, tunteja ei voi enää muuttaa. Virheistä kerro työnjohtajalle.

**Табель (Tuntikirja)** — отмечайте часы каждый день или в конце недели:
1. Откройте адрес табеля → войдите со своим логином и паролем.
2. В боковой панели выберите язык (🇷🇺 Русский) и неделю.
3. **⚡ Быстрый ввод** → введите часы по дням → **💾 Сохранить всё**.
4. После утверждения недели прорабом часы изменить нельзя. Об ошибках сообщите прорабу.

**Вход / Kirjautuminen:** 5 неверных попыток → логин блокируется на 15 минут.
Пароль никому не сообщайте. Забыли пароль — обратитесь к прорабу.

**Kalusto / Оборудование:** skannaa laitteen QR-koodi puhelimen kameralla — kirjautumista ei tarvita. /
отсканируйте QR-код на аппарате камерой телефона — вход не нужен.

---

## 3. Pääkäyttäjälle

### Uuden käyttäjän luonti
Mikä tahansa sovellus → **👤 Käyttäjät** → *➕ Lisää käyttäjä*:
- **Käyttäjätunnus:** etunimi tai etunimi.sukunimi pienillä, ei ääkkösiä (esim. `ivan.petrov`)
- **Rooli:**
  - *Pääkäyttäjä* — kaikki + käyttäjähallinta
  - *Työnjohtaja* — kaikki sovellukset, hyväksyy tunnit, näkee viranomais- ja terveystiedot
  - *Katselija* — näkee raportit, ei voi muuttaa mitään (esim. kirjanpitäjä, tilaaja)
  - *Työntekijä* — omat tunnit tuntikirjaan, omat asbestikohteet; voit rajata projektit
- **Salasana:** väh. 8 merkkiä. Anna se henkilölle **kasvokkain tai puhelimessa**, ei samassa
  viestissä tunnuksen kanssa.

### Kun joku lopettaa
**👤 Käyttäjät** → *✏️ Muokkaa* → poista ruksi kohdasta **Aktiivinen** → Tallenna.
Pääsy katkeaa noin 30 sekunnissa myös avoimesta istunnosta. Passivointi on parempi kuin
poisto: tunnus säilyy lokissa ja tuntikirjauksissa.

### Lukitun tunnuksen avaus
**👤 Käyttäjät** → keltainen *🔒 Lukitut tunnukset* -ilmoitus → valitse → **Avaa lukitus**.

### Varapääkäyttäjä
Pidä aina **vähintään kaksi aktiivista pääkäyttäjää**. Jos ainoa admin unohtaa salasanansa tai
tunnus lukittuu, kukaan ei pääse hallintaan. Järjestelmä estää viimeisen adminin poiston,
passivoinnin ja alentamisen.

1. **👤 Käyttäjät** → *➕ Lisää käyttäjä*
2. Tunnus esim. `sakari.vara` (oma varatunnus) tai luotettavan henkilön tunnus
3. Rooli **Pääkäyttäjä**, vahva salasana (väh. 12 merkkiä)
4. **Luo käyttäjä** → kirjaudu ulos → testaa kirjautuminen uudella tunnuksella
5. Tallenna salasana **salasananhallintaan** (esim. iCloud-avainnippu, 1Password, Bitwarden).
   Paperilla vain lukitussa paikassa.

### Jos kukaan ei pääse sisään (hätätilanne)
Kaikki adminit lukittu tai salasanat hukassa: odota lukituksen päättyminen (15 min).
Jos salasanat ovat oikeasti hukassa, käyttäjärekisteri on Supabasessa
(`globaali_data` → avain `kayttajat`). Ota yhteys ylläpitäjään. Älä poista rekisteriä,
koska tyhjä rekisteri avaa alkuasennuksen kenelle tahansa.
