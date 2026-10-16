"""
Käännökset: suomi (fi) ja venäjä (ru)
"""

KAANNOKSET = {
    # ── Sovelluksen otsikko ───────────────────────────────────────────────────
    "app_title":        {"fi": "Työmaan tuntikirja",                 "ru": "Табель учёта рабочего времени на объекте"},
    "app_caption":      {"fi": "Uudenmaan Asbestipurku Oy",          "ru": "Uudenmaan Asbestipurku Oy"},

    # ── Sivupalkki ────────────────────────────────────────────────────────────
    "projekti":         {"fi": "Projektin nimi",                     "ru": "Название объекта"},
    "projekti_ph":      {"fi": "esim. Valteri-koulu, Tenholantie 15","ru": "напр. Valteri-koulu, Tenholantie 15"},
    "viikko":           {"fi": "Viikko",                             "ru": "Неделя"},
    "vuosi":            {"fi": "Vuosi",                              "ru": "Год"},
    "oletus_kat":       {"fi": "Oletuskategoria",                    "ru": "Категория по умолчанию"},
    "paasovellus":      {"fi": "Pääsovellus",                        "ru": "Главное приложение"},

    # ── Välilehdet ────────────────────────────────────────────────────────────
    "tab_pikasyotto":   {"fi": "⚡ Pikasyöttö",                      "ru": "⚡ Быстрый ввод"},
    "tab_yksittainen":  {"fi": "👤 Yksittäinen",                     "ru": "👤 Отдельная запись"},
    "tab_vkoyht":       {"fi": "📊 Viikkoyhteenveto",                "ru": "📊 Сводка за неделю"},
    "tab_tekijat":      {"fi": "👥 Tekijälista",                     "ru": "👥 Список работников"},

    # ── Kategoriat ────────────────────────────────────────────────────────────
    "urakka":           {"fi": "Urakka",                             "ru": "Контракт"},
    "lisatyo":          {"fi": "Lisätyö",                            "ru": "Доп. работы"},
    "vesivahinko":      {"fi": "Vesivahinko",                        "ru": "Водный ущерб"},

    # ── Laskutustavat ─────────────────────────────────────────────────────────
    "vain_tunnit":      {"fi": "Vain tunnit",                        "ru": "Только часы"},
    "tuntihinta":       {"fi": "Tuntihinta (€/h)",                   "ru": "Почасовая оплата (€/ч)"},
    "kiintea_hinta":    {"fi": "Kiinteä hinta (€)",                  "ru": "Фиксированная цена (€)"},
    "laskutustapa":     {"fi": "Laskutustapa",                       "ru": "Тип оплаты"},

    # ── Päivät ────────────────────────────────────────────────────────────────
    "paivat_lyhyt":     {"fi": ["Ma","Ti","Ke","To","Pe","La","Su"], "ru": ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]},

    # ── Kentät ────────────────────────────────────────────────────────────────
    "nimi":             {"fi": "Nimi",                               "ru": "Имя"},
    "nimi_ph":          {"fi": "Nimi",                               "ru": "Имя работника"},
    "yritys":           {"fi": "Yritys",                             "ru": "Компания"},
    "kategoria":        {"fi": "Kategoria",                          "ru": "Категория"},
    "tunnit_pv":        {"fi": "Tunnit (h) päivittäin",              "ru": "Часы (ч) по дням"},
    "yht_tunnit":       {"fi": "Yhteensä",                           "ru": "Итого"},
    "huomio":           {"fi": "Huomio",                             "ru": "Примечание"},
    "huomio_ph":        {"fi": "mitä tehty",                         "ru": "что сделано"},
    "yleinen_huomio":   {"fi": "Yleinen huomio viikolle (vapaaehtoinen)", "ru": "Общее примечание за неделю (необязательно)"},
    "summa":            {"fi": "Summa",                              "ru": "Сумма"},

    # ── Napit ────────────────────────────────────────────────────────────────
    "tallenna":         {"fi": "💾 Tallenna",                        "ru": "💾 Сохранить"},
    "tallenna_kaikki":  {"fi": "💾 Tallenna kaikki",                 "ru": "💾 Сохранить всё"},
    "tallenna_vko":     {"fi": "Tallenna viikko",                    "ru": "Сохранить неделю"},
    "lisaa":            {"fi": "Lisää listalle",                     "ru": "Добавить в список"},
    "lisaa_kirjaus":    {"fi": "➕ Lisää tuntikirjaus",               "ru": "➕ Добавить запись"},
    "lisaa_tekija":     {"fi": "➕ Lisää aliurakoitsija",             "ru": "➕ Добавить работника"},
    "poista":           {"fi": "Poista",                             "ru": "Удалить"},
    "poista_listalta":  {"fi": "Poista listalta",                    "ru": "Убрать из списка"},
    "luo_raportti":     {"fi": "Luo raportti",                       "ru": "Создать отчёт"},
    "lataa_excel":      {"fi": "⬇️ Lataa Excel",                     "ru": "⬇️ Скачать Excel"},
    "tuo_viikkona":     {"fi": "Tuo viikkona",                       "ru": "Импортировать за неделю"},

    # ── Pikasyöttönapit ───────────────────────────────────────────────────────
    "lisaa_tunnit":     {"fi": "Lisää tunnit kerralla:",             "ru": "Добавить часы сразу:"},

    # ── Hyväksyntä ────────────────────────────────────────────────────────────
    "hyvaksynta":       {"fi": "🔏 Hyväksyntä",                      "ru": "🔏 Согласование"},
    "hyvaksy":          {"fi": "✅ Hyväksy",                         "ru": "✅ Подтвердить"},
    "selvitys_nappi":   {"fi": "⚠️ Selvitys",                        "ru": "⚠️ Уточнение"},
    "palauta":          {"fi": "🔄 Palauta",                         "ru": "🔄 Сбросить"},
    "selvityksen_syy":  {"fi": "Selvityksen syy",                    "ru": "Причина уточнения"},
    "selvityksen_ph":   {"fi": "Mikä vaatii selvitystä?",            "ru": "Что требует уточнения?"},

    # ── Tilat ─────────────────────────────────────────────────────────────────
    "tila_odottaa":     {"fi": "Odottaa hyväksyntää",                "ru": "Ожидает согласования"},
    "tila_hyvaksytty":  {"fi": "Hyväksytty",                         "ru": "Подтверждено"},
    "tila_selvitys":    {"fi": "Selvitys vaaditaan",                 "ru": "Требует уточнения"},

    # ── Työnjohtajan kommentti ────────────────────────────────────────────────
    "tj_kommentti":     {"fi": "💬 Työnjohtajan kommentti",          "ru": "💬 Комментарий прораба"},
    "tj_kommentti_ph":  {"fi": "esim. Tarkista tiistain tunnit…",    "ru": "напр. Проверьте часы за вторник…"},
    "tj_kommentti_tall":{"fi": "💾 Tallenna",                        "ru": "💾 Сохранить"},
    "tj_kommentti_del": {"fi": "🗑️ Poista kommentti",               "ru": "🗑️ Удалить комментарий"},
    "tj_huomio_label":  {"fi": "💬 Työnjohtajan huomio:",            "ru": "💬 Комментарий прораба:"},

    # ── Päiväkohtaiset huomiot ────────────────────────────────────────────────
    "pv_huomiot":       {"fi": "📝 Päiväkohtaiset huomiot",          "ru": "📝 Примечания по дням"},

    # ── Viikkoyhteenveto ──────────────────────────────────────────────────────
    "tekijoita":        {"fi": "Tekijöitä",                          "ru": "Работников"},
    "tunteja_yht":      {"fi": "Tunteja yht.",                       "ru": "Часов итого"},
    "summa_yht":        {"fi": "Summa yht.",                         "ru": "Сумма итого"},
    "raportti_ohje":    {"fi": "📄 Lataa viikkoraportti — tulosta PDF:nä selaimessa",
                         "ru": "📄 Скачать недельный отчёт — распечатать как PDF в браузере"},

    # ── Tekijälista ───────────────────────────────────────────────────────────
    "tekijat_ohje":     {"fi": "Lisää tekijät kerran — sen jälkeen ne näkyvät pikasyötössä automaattisesti.",
                         "ru": "Добавьте работников один раз — они появятся в быстром вводе автоматически."},
    "jo_listalla":      {"fi": "on jo listalla.",                    "ru": "уже в списке."},

    # ── Infot / viestit ───────────────────────────────────────────────────────
    "ei_tekijoita":     {"fi": "Lisää aliurakoitsijat **Tekijälista**-välilehdeltä.",
                         "ru": "Добавьте работников на вкладке **Список работников**."},
    "ei_kirjauksia":    {"fi": "Ei kirjauksia tälle viikolle.",      "ru": "Нет записей за эту неделю."},
    "aseta_projekti":   {"fi": "Aseta projektin nimi sivupalkissa.", "ru": "Укажите название объекта на боковой панели."},
    "tallennettu":      {"fi": "✅ Tallennettu",                     "ru": "✅ Сохранено"},
    "kommentti_tall":   {"fi": "Kommentti tallennettu.",             "ru": "Комментарий сохранён."},
    "syota_nimi":       {"fi": "Syötä nimi.",                        "ru": "Введите имя."},

    # ── Tunnit-sarakkeet taulukossa ───────────────────────────────────────────
    "taulukko_nimi":    {"fi": "Nimi",                               "ru": "Имя"},
    "taulukko_yritys":  {"fi": "Yritys",                             "ru": "Компания"},
    "taulukko_yht":     {"fi": "Yht (h)",                            "ru": "Итого (ч)"},
    "taulukko_kat":     {"fi": "Kategoria",                          "ru": "Категория"},
    "taulukko_hinta":   {"fi": "Hinta",                              "ru": "Цена"},
    "taulukko_summa":   {"fi": "Summa (€)",                          "ru": "Сумма (€)"},
    "taulukko_tila":    {"fi": "Tila",                               "ru": "Статус"},
    "taulukko_huomio":  {"fi": "Huomio",                             "ru": "Примечание"},

    # ── Hyväksyntäyhteenveto ──────────────────────────────────────────────────
    "hyv_yht":          {"fi": "hyväksytty",                         "ru": "подтверждено"},
    "sel_yht":          {"fi": "selvitystä",                         "ru": "уточнений"},
    "odo_yht":          {"fi": "odottaa",                            "ru": "ожидает"},

    # ── Poisto-expander ───────────────────────────────────────────────────────
    "poista_kirjaus":   {"fi": "🗑️ Poista kirjaus",                  "ru": "🗑️ Удалить запись"},
    "poista_tekija":    {"fi": "🗑️ Poista listalta",                 "ru": "🗑️ Убрать из списка"},
    "kirjaus":          {"fi": "Kirjaus",                            "ru": "Запись"},
    "tekija":           {"fi": "Tekijä",                             "ru": "Работник"},

    # ── Asbestityön dokumentointi (asbesti_app) ───────────────────────────────
    "asb_title":        {"fi": "Asbestityön dokumentointi",          "ru": "Документация асбестовых работ"},
    "asb_valitse_kohde":{"fi": "Valitse työkohde",                   "ru": "Выберите объект"},
    "asb_ei_kohteita":  {"fi": "Sinulle ei ole vielä osoitettu työkohteita. Pyydä työnjohtajaa lisäämään sinut kohteelle.",
                         "ru": "Вам ещё не назначены объекты. Попросите прораба добавить вас на объект."},
    "asb_aloitus":      {"fi": "📸 Aloitusdokumentointi",            "ru": "📸 Документация начала работ"},
    "asb_lopetus":      {"fi": "🏁 Lopetusdokumentointi",            "ru": "🏁 Документация окончания работ"},
    "asb_lahtotilanne": {"fi": "Lähtötilanne ennen purkua",          "ru": "Исходное состояние до демонтажа"},
    "asb_suojaukset":   {"fi": "Suojaukset ja osastointi",           "ru": "Защита и изоляция"},
    "asb_alipaineistus":{"fi": "Alipaineistaja paikallaan",          "ru": "Установка отрицательного давления"},
    "asb_mittari":      {"fi": "Paine-eromittarin lukema",           "ru": "Показание манометра"},
    "asb_kalusto":      {"fi": "Käytössä oleva kalusto",             "ru": "Используемое оборудование"},
    "asb_lopetuskuvat": {"fi": "Lopetuskuvat puretusta tilasta",     "ru": "Фото после демонтажа"},
    "asb_ota_kuva":     {"fi": "📷 Ota kuva tai valitse tiedosto",   "ru": "📷 Сделайте фото или выберите файл"},
    "asb_kuvateksti":   {"fi": "Kuvateksti (vapaaehtoinen)",         "ru": "Подпись к фото (необязательно)"},
    "asb_tallenna_kuvat":{"fi": "💾 Tallenna kuvat",                 "ru": "💾 Сохранить фото"},
    "asb_kuvia":        {"fi": "kuvaa tallennettu",                  "ru": "фото сохранено"},
    "asb_puuttuu":      {"fi": "puuttuu",                            "ru": "отсутствует"},
    "asb_valmis":       {"fi": "valmis",                             "ru": "готово"},
    "asb_havainnot":    {"fi": "Havainnot työn aikana",              "ru": "Наблюдения во время работ"},
    "asb_havainnot_ph": {"fi": "esim. löytyi lisää asbestipitoista materiaalia, poikkeamat…",
                         "ru": "напр. обнаружен дополнительный асбестосодержащий материал, отклонения…"},
    "asb_tallenna_hav": {"fi": "💾 Tallenna havainnot",              "ru": "💾 Сохранить наблюдения"},
    "asb_aloitus_ok":   {"fi": "✅ Kaikki aloituskohdat dokumentoitu — työ merkitty käynnistyneeksi.",
                         "ru": "✅ Все пункты начала задокументированы — работа отмечена как начатая."},
    "asb_purku_valmis": {"fi": "🏁 Kuittaa purku valmiiksi",         "ru": "🏁 Подтвердить окончание демонтажа"},
    "asb_purku_kuitattu":{"fi": "Purku kuitattu valmiiksi",          "ru": "Демонтаж подтверждён"},
    "asb_tallennettu":  {"fi": "✅ Tallennettu",                     "ru": "✅ Сохранено"},
    "asb_tila":         {"fi": "Tila",                               "ru": "Статус"},
    "asb_tyonumero":    {"fi": "Työnumero",                          "ru": "Номер работы"},
}


def tr(avain: str, kieli: str = "fi"):
    """Palauttaa käännöksen annetulle avaimelle ja kielelle."""
    if avain not in KAANNOKSET:
        return avain
    return KAANNOKSET[avain].get(kieli, KAANNOKSET[avain].get("fi", avain))


def paivat(kieli: str = "fi") -> list:
    """Palauttaa päivien lyhenteet oikealla kielellä."""
    return KAANNOKSET["paivat_lyhyt"][kieli]


def kategoriat(kieli: str = "fi") -> list:
    return [tr("urakka", kieli), tr("lisatyo", kieli), tr("vesivahinko", kieli)]


def laskutustavat(kieli: str = "fi") -> list:
    return [tr("vain_tunnit", kieli), tr("tuntihinta", kieli), tr("kiintea_hinta", kieli)]
