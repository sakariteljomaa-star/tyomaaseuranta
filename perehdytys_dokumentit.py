"""
Perehdytysmateriaali — tietosuojailmoitus työntekijöille (fi + ru) ja työntekijän
tietolomake (kaksikielinen). Tulostettavat PDF:t, esitäytetty työmaan tiedoilla.

GDPR 13/14 art. informointi. Lomakkeen kuittaus on vastaanottokuittaus, EI suostumus:
käsittely perustuu lakisääteiseen velvoitteeseen ja sopimukseen.

Fontti: DejaVu Sans (fonts/, vapaa lisenssi) — tukee kyrillisiä merkkejä.
"""

import io
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

_FONTIT = Path(__file__).parent / "fonts"
try:
    pdfmetrics.registerFont(TTFont("DejaVu", str(_FONTIT / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(_FONTIT / "DejaVuSans-Bold.ttf")))
    F, FB = "DejaVu", "DejaVu-Bold"
except Exception:  # fontti puuttuu → kyrilliset eivät näy, suomi toimii
    F, FB = "Helvetica", "Helvetica-Bold"

TUMMA = colors.HexColor("#1F3864")

S_OTS   = ParagraphStyle("ots", fontName=FB, fontSize=14, leading=17, textColor=TUMMA, spaceAfter=2)
S_ALA   = ParagraphStyle("ala", fontName=F, fontSize=9, leading=11, textColor=colors.grey, spaceAfter=8)
S_H     = ParagraphStyle("h", fontName=FB, fontSize=11, leading=13.5, textColor=TUMMA,
                         spaceBefore=7, spaceAfter=1)
S_T     = ParagraphStyle("t", fontName=F, fontSize=10, leading=13, spaceAfter=2)
S_PIENI = ParagraphStyle("p", fontName=F, fontSize=8, leading=10, textColor=colors.grey)
S_LBL   = ParagraphStyle("lbl", fontName=FB, fontSize=7.5, leading=9)
S_LBL2  = ParagraphStyle("lbl2", fontName=F, fontSize=7, leading=8.5, textColor=colors.grey)

REKISTERINPITAJA = "Uudenmaan Asbestipurku Oy (Y-tunnus 2817254-1)"
YHTEYSHENKILO = "Sakari Teljomaa, sakari.teljomaa@gmail.com"


def _tyomaa_rivi(p: dict) -> str:
    osat = [p.get("nimi", ""), p.get("tyomaa_osoite", "")]
    return ", ".join(o for o in osat if o) or "_______________________________"


# ── Ilmoitustekstit ────────────────────────────────────────────────────────────

def _ilmoitus_fi(p: dict) -> list:
    return [
        ("Kuka käsittelee tietojasi?",
         f"{REKISTERINPITAJA} on työmaan päätoteuttaja ja käsittelee tietojasi rekisterinpitäjänä. "
         f"Yhteyshenkilö: {YHTEYSHENKILO}."),
        ("Mitä tietoja käsitellään?",
         "Nimi, syntymäaika, veronumero, kansalaisuus, työnantaja ja sen Y-tunnus, työsuhteen laji, "
         "yhteystiedot, työmaalla olopäivät ja työtunnit. Asbestityössä lisäksi terveystarkastuksen, "
         "hengityksensuojaimen tiiviystestauksen ja asbestityön koulutuksen päivämäärät. "
         "Terveystarkastuksen tuloksia tai muita terveystietoja emme tallenna."),
        ("Miksi tietoja käsitellään?",
         "• Laki velvoittaa päätoteuttajan ilmoittamaan kaikki työmaalla työskentelevät Verohallinnolle "
         "kuukausittain ja pitämään luetteloa työmaalla olevista. Veronumero on pakollinen "
         "rakennustyömaalla.<br/>"
         "• Työtunteja käytetään työn seurantaan ja laskutukseen.<br/>"
         "• Asbestityön edellytysten (työkyky ja koulutus) varmistaminen on lakisääteistä.<br/>"
         "Käsittely perustuu lakisääteisiin velvoitteisiin ja sopimukseen — ei suostumukseen."),
        ("Mistä tiedot saadaan?",
         "Sinulta itseltäsi tai työnantajaltasi (aliurakoitsija tai vuokrayritys)."),
        ("Kenelle tietoja luovutetaan?",
         "Verohallinnolle (lakisääteinen ilmoitus), työsuojeluviranomaiselle (asbestityön "
         "ennakkoilmoitus) ja tilaajalle työmaan tuntiraporteissa. Tietoja ei luovuteta markkinointiin."),
        ("Kuinka kauan tietoja säilytetään?",
         "Verohallinnolle ilmoitetut tiedot 6 vuotta lain mukaan. Muut tiedot poistetaan, kun niitä ei "
         "enää tarvita."),
        ("Miten tiedot suojataan?",
         "Tiedot ovat salatussa sähköisessä järjestelmässä, johon on pääsy vain nimetyillä henkilöillä. "
         "Tiedot tallennetaan EU:ssa; osa palveluntarjoajista toimii Yhdysvalloissa, ja tietojen siirrot "
         "on suojattu sopimuksin."),
        ("Sinun oikeutesi",
         "Voit pyytää nähtäväksi itseäsi koskevat tiedot ja pyytää korjaamaan virheelliset tiedot. "
         "Lakisääteisiä ilmoitustietoja ei voida poistaa ennen säilytysajan päättymistä. Jos katsot, "
         "että tietojasi käsitellään lainvastaisesti, voit tehdä valituksen Tietosuojavaltuutetulle "
         "(tietosuoja.fi)."),
    ]


def _ilmoitus_ru(p: dict) -> list:
    return [
        ("Кто обрабатывает ваши данные?",
         f"{REKISTERINPITAJA} является генеральным исполнителем (päätoteuttaja) на объекте и "
         f"обрабатывает ваши данные как контролёр персональных данных. "
         f"Контактное лицо: {YHTEYSHENKILO}."),
        ("Какие данные обрабатываются?",
         "Имя, дата рождения, налоговый номер (veronumero), гражданство, работодатель и его "
         "регистрационный номер (Y-tunnus), вид трудовых отношений, контактные данные, дни работы на "
         "объекте и рабочие часы. При работе с асбестом также даты медицинского осмотра, проверки "
         "плотности прилегания респиратора и обучения работе с асбестом. Результаты медосмотра и "
         "другие сведения о здоровье мы не храним."),
        ("Зачем обрабатываются данные?",
         "• Закон обязывает генерального исполнителя ежемесячно сообщать в Налоговую администрацию "
         "Финляндии (Verohallinto) обо всех работающих на объекте и вести список лиц, находящихся на "
         "объекте. Налоговый номер обязателен на строительной площадке.<br/>"
         "• Рабочие часы используются для учёта работы и выставления счетов.<br/>"
         "• Проверка допуска к работе с асбестом (трудоспособность и обучение) требуется по закону.<br/>"
         "Обработка основана на требованиях закона и договоре — а не на согласии."),
        ("Откуда получены данные?",
         "От вас лично или от вашего работодателя (субподрядчика или агентства по найму персонала)."),
        ("Кому передаются данные?",
         "Налоговой администрации (по закону), органу охраны труда (предварительное уведомление о "
         "работе с асбестом) и заказчику в отчётах о рабочих часах. Данные не передаются для маркетинга."),
        ("Как долго хранятся данные?",
         "Данные, переданные в Налоговую администрацию, хранятся 6 лет согласно закону. Остальные "
         "данные удаляются, когда они больше не нужны."),
        ("Как защищены данные?",
         "Данные хранятся в защищённой электронной системе, доступ к которой есть только у "
         "уполномоченных лиц. Данные хранятся в ЕС; часть поставщиков услуг работает в США, передача "
         "данных защищена договорами."),
        ("Ваши права",
         "Вы можете запросить ознакомление со своими данными и исправление неверных данных. Данные, "
         "передаваемые по закону, не могут быть удалены до окончания срока хранения. Если вы считаете, "
         "что ваши данные обрабатываются незаконно, вы можете подать жалобу Уполномоченному по защите "
         "данных Финляндии (tietosuoja.fi)."),
    ]


def _ilmoitus_sivu(otsikko: str, tyomaa_label: str, osiot: list, alaviite: str, p: dict) -> list:
    e = [Paragraph(otsikko, S_OTS),
         Paragraph(f"{tyomaa_label}: {_tyomaa_rivi(p)}", S_ALA)]
    for h, t in osiot:
        e.append(Paragraph(h, S_H))
        e.append(Paragraph(t, S_T))
    e.append(Spacer(1, 6))
    e.append(Paragraph(alaviite, S_PIENI))
    return e


# ── Tietolomake ────────────────────────────────────────────────────────────────

def _kentta(fi: str, ru: str, leveys=None):
    return [Paragraph(fi, S_LBL), Paragraph(ru, S_LBL2)]


def _lomake(p: dict) -> list:
    e = [Paragraph("TYÖNTEKIJÄN TIETOLOMAKE · АНКЕТА РАБОТНИКА", S_OTS),
         Paragraph(f"Työmaa / Объект: {_tyomaa_rivi(p)}   ·   Päätoteuttaja / Генподрядчик: "
                   f"{p.get('paatoteuttaja') or 'Uudenmaan Asbestipurku Oy'}   ·   "
                   f"Työmaa-avain: {p.get('tyomaa_avain') or '__________'}", S_ALA)]

    def rivi(*kentat):
        """Rivi soluja: (fi, ru) → nimiö yläreunaan, tyhjä kirjoitustila alle."""
        return [[Paragraph(f"<b>{fi}</b> · <font color='grey'>{ru}</font>", S_LBL)
                 for fi, ru in kentat]]

    W = 182 * mm
    taulut = [
        (rivi(("Sukunimi ja etunimet", "Фамилия и имя")), [W]),
        (rivi(("Syntymäaika", "Дата рождения"),
              ("Veronumero (12 numeroa)", "Налоговый номер (12 цифр)"),
              ("Kansalaisuus", "Гражданство")), [W*0.27, W*0.43, W*0.30]),
        (rivi(("Työnantaja (yritys)", "Работодатель (компания)"),
              ("Työnantajan Y-tunnus", "Номер компании (Y-tunnus)")), [W*0.62, W*0.38]),
        (rivi(("Lähettävä yritys (ulkomaiset)", "Направляющая компания (иностр.)"),
              ("Ammattinimike", "Должность")), [W*0.62, W*0.38]),
        (rivi(("Puhelin", "Телефон"),
              ("Osoite (vapaaehtoinen)", "Адрес (необязательно)")), [W*0.35, W*0.65]),
    ]
    for data, lev in taulut:
        t = Table(data + [[""] * len(lev)], colWidths=lev, rowHeights=[None, 9 * mm])
        t.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF3FA")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        e.append(t)
        e.append(Spacer(1, 2))

    # Työsuhteen laji
    e.append(Spacer(1, 3))
    e.append(Paragraph("<b>Työsuhteen laji</b> · <font color='grey'>Вид трудовых отношений</font>", S_LBL))
    laji = Table([[Paragraph("☐ Työsuhteinen<br/><font color='grey'>работник по трудовому договору</font>", S_T),
                   Paragraph("☐ Vuokratyöntekijä<br/><font color='grey'>арендованный работник</font>", S_T),
                   Paragraph("☐ Itsenäinen ammatinharjoittaja<br/><font color='grey'>самозанятый</font>", S_T)]],
                 colWidths=[W/3]*3)
    laji.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    e.append(laji)

    # Asbestityö
    e.append(Spacer(1, 3))
    e.append(Paragraph("<b>Asbestityö</b> (vain asbestipurkutyöhön osallistuvat) · "
                       "<font color='grey'>Работа с асбестом (только для участников)</font>", S_LBL))
    asb = Table(rivi(("Terveystarkastus voimassa asti", "Медосмотр действителен до"),
                     ("Tiiviystestaus (pvm)", "Проверка респиратора (дата)"),
                     ("Asbestityön koulutus (pvm)", "Обучение по асбесту (дата)"))
                + [["", "", ""]], colWidths=[W/3]*3, rowHeights=[None, 8 * mm])
    asb.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, colors.black),
                             ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
                             ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FFF4E5"))]))
    e.append(asb)
    e.append(Paragraph("Esitä todistukset työnjohtajalle. Terveystarkastuksen tuloksia ei kirjata. · "
                       "Предъявите документы руководителю работ. Результаты медосмотра не записываются.",
                       S_PIENI))

    # Kuittaus
    e.append(Spacer(1, 6))
    e.append(Paragraph("<b>Kuittaus · Подтверждение</b>", S_H))
    e.append(Paragraph(
        "☐ Olen saanut tietosuojailmoituksen ja tiedän, että tietoni ilmoitetaan lain perusteella "
        "Verohallinnolle. Tämä on vastaanottokuittaus, ei suostumus.<br/>"
        "<font color='grey'>Я получил(а) уведомление о защите данных и знаю, что мои данные передаются "
        "в Налоговую администрацию по закону. Это подтверждение получения, а не согласие.</font>", S_T))
    e.append(Paragraph(
        "☐ Olen saanut työmaaperehdytyksen. · "
        "<font color='grey'>Я прошёл(а) вводный инструктаж на объекте.</font>", S_T))
    e.append(Paragraph(
        "☐ Kuvallisessa tunnisteessani näkyy veronumero. · "
        "<font color='grey'>На моём удостоверении с фото указан налоговый номер.</font>", S_T))

    # 5 saraketta: kenttä, väli, kenttä, väli, kenttä → kullekin oma allekirjoitusviiva
    vali = 6 * mm
    kl = (W - 2 * vali) / 3
    allek = Table([
        [Paragraph("<b>Paikka ja päivämäärä</b> · <font color='grey'>Место и дата</font>", S_LBL), "",
         Paragraph("<b>Allekirjoitus</b> · <font color='grey'>Подпись</font>", S_LBL), "",
         Paragraph("<b>Nimen selvennys</b> · <font color='grey'>Расшифровка</font>", S_LBL)],
        ["", "", "", "", ""]], colWidths=[kl, vali, kl, vali, kl], rowHeights=[None, 12 * mm])
    allek.setStyle(TableStyle([("LINEBELOW", (0, 1), (0, 1), 1.0, colors.black),
                               ("LINEBELOW", (2, 1), (2, 1), 1.0, colors.black),
                               ("LINEBELOW", (4, 1), (4, 1), 1.0, colors.black),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    e.append(Spacer(1, 4))
    e.append(allek)

    # Työnjohto täyttää
    e.append(Spacer(1, 6))
    tj = Table([[Paragraph("<b>Työnjohto täyttää:</b> Perehdyttäjä ____________________ · "
                           "Tiedot syötetty järjestelmään (pvm) __________ · "
                           "Veronumero tarkistettu ☐", S_PIENI)]], colWidths=[W])
    tj.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.4, colors.grey),
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5"))]))
    e.append(tj)
    e.append(Spacer(1, 3))
    e.append(Paragraph("Lomake säilytetään lukitussa paikassa 6 vuotta (Verohallinnon ilmoitusten tausta-aineisto). "
                       "Älä kuvaa tai lähetä lomaketta pikaviestimellä.", S_PIENI))
    return e


# ── Julkiset funktiot ──────────────────────────────────────────────────────────

def _rakenna(elementit: list) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm,
                            title="Perehdytys — tietosuoja", author="Uudenmaan Asbestipurku Oy")
    doc.build(elementit)
    return buf.getvalue()


def luo_tietosuojailmoitus(p: dict) -> bytes:
    """Tietosuojailmoitus työntekijälle: sivu 1 suomi, sivu 2 venäjä."""
    e = _ilmoitus_sivu("Tietosuojailmoitus työmaalla työskenteleville", "Työmaa",
                       _ilmoitus_fi(p),
                       "Koko tietosuojaseloste on saatavilla työnjohtajalta. "
                       "EU:n tietosuoja-asetus (GDPR) 13 ja 14 artikla.", p)
    e.append(PageBreak())
    e += _ilmoitus_sivu("Уведомление о защите персональных данных для работников объекта", "Объект",
                        _ilmoitus_ru(p),
                        "Полное описание обработки данных (tietosuojaseloste) можно получить у "
                        "руководителя работ. Общий регламент ЕС по защите данных (GDPR), статьи 13 и 14.", p)
    return _rakenna(e)


def luo_tietolomakkeet(p: dict, kpl: int = 1) -> bytes:
    """Tyhjät kaksikieliset tietolomakkeet (yksi per sivu)."""
    e = []
    for i in range(max(1, kpl)):
        if i:
            e.append(PageBreak())
        e += _lomake(p)
    return _rakenna(e)


def luo_perehdytyspaketti(p: dict) -> bytes:
    """Yhdessä PDF:ssä: ilmoitus (fi), ilmoitus (ru) ja tietolomake."""
    e = _ilmoitus_sivu("Tietosuojailmoitus työmaalla työskenteleville", "Työmaa",
                       _ilmoitus_fi(p),
                       "Koko tietosuojaseloste on saatavilla työnjohtajalta. "
                       "EU:n tietosuoja-asetus (GDPR) 13 ja 14 artikla.", p)
    e.append(PageBreak())
    e += _ilmoitus_sivu("Уведомление о защите персональных данных для работников объекта", "Объект",
                        _ilmoitus_ru(p),
                        "Полное описание обработки данных (tietosuojaseloste) можно получить у "
                        "руководителя работ. Общий регламент ЕС по защите данных (GDPR), статьи 13 и 14.", p)
    e.append(PageBreak())
    e += _lomake(p)
    return _rakenna(e)
