-- Aja tämä Supabase SQL Editorissa
-- Estää suoran pääsyn tietokantaan ilman API-avainta

-- Ota Row Level Security käyttöön
ALTER TABLE projekti_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE globaali_data ENABLE ROW LEVEL SECURITY;

-- Salli pääsy vain anon-avaimella (sovelluksen käyttämä avain)
CREATE POLICY "anon_kaikki_projekti_data" ON projekti_data
  FOR ALL TO anon USING (true) WITH CHECK (true);

CREATE POLICY "anon_kaikki_globaali_data" ON globaali_data
  FOR ALL TO anon USING (true) WITH CHECK (true);

-- Huom: tämä sallii kaikki pyynnöt joilla on oikea API-avain.
-- Tiukempi vaihtoehto: rajoita projekteittain tai käyttäjittäin
-- jos lisäät käyttäjähallinnan myöhemmin.
