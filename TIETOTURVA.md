# Tietoturva — Työmaaseuranta

Uudenmaan Asbestipurku Oy. Päivitetty 2026-06.

Tämä dokumentti kuvaa järjestelmän tietoturvaratkaisut, avainten hallinnan ja
toimintaohjeet ongelmatilanteissa. Lue tämä ennen kuin jaat tunnuksia tai avaimia.

---

## 1. Kokonaiskuva

Kolme sovellusta (kustannusseuranta, tuntikirja, kalustoseuranta) pyörivät
**Streamlit Community Cloudissa**. Data tallennetaan **Supabaseen** (PostgreSQL, EU).
Lähdekoodi on GitHubissa. Salaisuudet (avaimet, salasanat) **eivät** ole koodissa.

```
Selain ──► Streamlit Cloud (sovelluskoodi + Secrets) ──► Supabase (data, EU)
                                   │
                                   └──► Netvisor API (vain kustannusseuranta)
```

---

## 2. Salaisuuksien sijainti

| Salaisuus | Sijainti | Näkyykö selaimeen? | GitHubissa? |
|-----------|----------|:---:|:---:|
| Supabase secret-avain | Streamlit Secrets | Ei | Ei |
| Netvisor API-avaimet | Streamlit Secrets | Ei | Ei |
| Käyttäjien salasanat | Supabase (PBKDF2-hash) | Ei | Ei |

**Streamlit Secrets** on palvelinpuolen salattu asetustila. Sitä ei lähetetä
selaimelle eikä se päädy lähdekoodiin. `.gitignore` estää `secrets.toml`:n
ja `data/`-kansion joutumisen GitHubiin.

**Kultainen sääntö:** avaimia ei koskaan liitetä chattiin, sähköpostiin,
GitHubiin, koodiin eikä kuvakaappauksiin. Vain Streamlitin Secrets-kenttään.

---

## 3. Käyttäjien salasanat

- Tallennetaan **PBKDF2-HMAC-SHA256**, 100 000 kierrosta, satunnainen suola per käyttäjä.
- Selkokielistä salasanaa ei tallenneta minnekään — vain hash.
- Salasanaa ei voi "palauttaa" sellaisenaan; pääkäyttäjä asettaa uuden.
- **Pääkäyttäjän (admin) salasana on kriittisin** — ota se talteen turvalliseen paikkaan.

---

## 4. Supabase

- **Käytä secret-avainta** (`sb_secret_...` / legacy `service_role`), ei publishable-avainta.
  Secret-avain toimii vain palvelinpuolella (Streamlit Secrets), ei selaimelle.
- Avain antaa täyden pääsyn tietokantaan → pidä se vain Secretsissä.
- Data sijaitsee EU:ssa (Frankfurt). Supabase salaa datan levossa ja siirrossa (TLS).
- **Jos secret-avain vuotaa:** Supabase → Project Settings → API → luo uusi avain
  (rotaatio) ja päivitä se kaikkien kolmen sovelluksen Secretseihin.

> RLS (Row Level Security) on pois päältä, koska pääsyä rajaa secret-avain
> (palvelinpuolella) + sovelluksen oma käyttäjäkirjautuminen. Tämä on riittävä
> taso pienelle sisäiselle työkalulle.

---

## 5. Netvisor API (kustannusseuranta)

### Avaintyypit
- **Partner ID + Partner Key** — saadaan Netvisorilta (tukipyyntö).
- **Customer ID + Customer Key** — yrityksen oma API-avain Netvisorin asetuksista.

### TÄRKEIN suojaus: lue-vain-oikeudet
Anna Netvisor-integraatiolle **VAIN lukuoikeudet** ostoihin, myyntiin ja
tuntikirjanpitoon. **Älä** anna kirjoitus-, maksu- tai muokkausoikeuksia.
Näin vaikka avain vuotaisi, sillä voi vain lukea — ei muuttaa tai maksaa mitään.

### Muuta
- Avaimet vain Streamlit Secretsissä, eivät koodissa.
- Tunnistus: MAC-hash (SHA256) jokaisessa pyynnössä, ei avaimia URL:ssa.
- Raakavastauksen tutkija näkyy **vain admin-roolille**.
- **Jos avain vuotaa:** mitätöi se Netvisorissa ja luo uusi.

---

## 6. Roolit ja pääsynhallinta

| Rooli | Kustannukset (ml. palkat) | Tunnit | Kalusto |
|-------|:---:|:---:|:---:|
| admin | ✅ + käyttäjähallinta | ✅ | ✅ |
| tyonjohtaja | ✅ | hyväksyy | hallinta |
| katselija | luku | luku | luku |
| tyontekija | 🚫 estetty | omat tunnit | QR |

- **Työntekijä ei pääse kustannusseurantaan** — palkka- ja laskutustiedot eivät vuoda työmaalle.
- Hyväksytyt tunnit lukittuvat; vain TJ/admin voi avata.
- QR-kalustoskannaus on tarkoituksella julkinen (ei arkaluonteista dataa).

---

## 6b. Toimintaloki

Järjestelmä kirjaa turvallisuuskriittiset tapahtumat `loki`-tauluun:
kirjautumiset, käyttäjämuutokset, tuntien hyväksynnät ja Netvisor-haut
(käyttäjä + aikaleima + kohde). Admin näkee lokin 👤 Käyttäjät → 📜 Toimintaloki.
Loki auttaa väärinkäytösten selvittämisessä ja vastuun osoittamisessa.

## 7. Henkilötiedot (GDPR)

- Järjestelmä sisältää henkilötietoja (nimet, työtunnit). Ks. `TIETOSUOJASELOSTE.md`.
- Käsittelyperuste: sopimuksen täytäntöönpano (aliurakkasuhteet, työtunnit).
- Säilytysaika: tiedot poistetaan 6 kk projektin päättymisen jälkeen.
- Data EU:ssa, ei luovuteta kolmansille (tilaajalle vain tuntiraportit, ei yksilöityjä tietoja).

---

## 8. Toimintaohje: avain vuotanut tai epäilys väärinkäytöstä

1. **Supabase-avain:** luo uusi avain Supabasessa → päivitä kaikkien 3 sovelluksen Secrets → vanha lakkaa toimimasta.
2. **Netvisor-avain:** mitätöi Netvisorissa → luo uusi → päivitä kustannusseurannan Secrets.
3. **Käyttäjätunnus:** admin poistaa/passivoi käyttäjän 👤 Käyttäjät -välilehdeltä tai vaihtaa salasanan.
4. **Streamlit-tili:** vaihda Streamlit Cloud -tilin salasana (sieltä pääsee Secretsiin).

---

## 9. Säännöllinen ylläpito

- [ ] Tarkista käyttäjälista neljännesvuosittain — poista lähteneet työntekijät.
- [ ] Varmista että pääkäyttäjiä on vähintään kaksi (ettei pääsy lukkiudu).
- [ ] Pidä admin-salasana ja avaimet turvallisessa salasananhallinnassa.
- [ ] Älä jaa sovellusten URL-osoitteita julkisesti tarpeettomasti.

---

## 10. Tiivistelmä — tee nämä

1. ✅ Käytä Supabasen **secret-avainta**, älä publishable-avainta.
2. ✅ Pyydä Netvisorista **lue-vain** -integraatio.
3. ✅ Avaimet **vain** Streamlit Secretsiin — ei koskaan koodiin/GitHubiin/chattiin.
4. ✅ Ota **admin-salasana talteen** ja luo toinen admin varalle.
5. ✅ Tunnukset henkilökohtaisia — jokaiselle oma, ei jaettuja.
