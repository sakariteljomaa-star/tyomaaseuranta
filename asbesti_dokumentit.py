"""
Asbestityön dokumenttien PDF-generointi.

Kolme dokumenttia, rakenteet tiedostosta CATEVA_DOKUMENTTIPOHJAT.md:
  1. Asbestipurkutyön turvallisuussuunnitelma (osiot Perustiedot + 1–7)
  2. Ennakkoilmoituksen esitäyttö AVIn asiointia varten
  3. Asbestipurkutyön aloitus- ja lopetusraportti (+ liite-PDF:ien yhdistys)

Ylä- ja alatunniste kuten yrityksen nykyisissä dokumenteissa.
"""

import io
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak,
)

YRITYS = {
    "nimi":    "Uudenmaan Asbestipurku Oy",
    "osoite":  "Rattitie 24",
    "posti":   "00770 Helsinki",
    "ytunnus": "Y-tunnus: 2817254-1",
    "www":     "www.uudenmaanasbestipurku.fi",
    "puhelin": "Puhelin: 044 300 9672",
}

# UAP-merkki (brand/LOGO-OHJE.md): merkki + nimi oikealla puolella
_LOGO = Path(__file__).parent / "brand" / "png" / "uap-merkki-vari-512.png"

# ── Tyylit ─────────────────────────────────────────────────────────────────────

S_KOHDE   = ParagraphStyle("kohde",   fontName="Helvetica-Bold", fontSize=14, leading=17, spaceAfter=1)
S_PVM     = ParagraphStyle("pvm",     fontName="Helvetica",      fontSize=10, leading=12,
                           spaceAfter=4, textColor=colors.HexColor("#444444"))
S_OSIO    = ParagraphStyle("osio",    fontName="Helvetica-Bold", fontSize=11.5, leading=14,
                           spaceBefore=9, spaceAfter=4)
S_LABEL   = ParagraphStyle("label",   fontName="Helvetica-Bold", fontSize=9,  leading=11, spaceAfter=1)
S_ARVO    = ParagraphStyle("arvo",    fontName="Helvetica",      fontSize=10, leading=12, spaceAfter=4)
S_TEKSTI  = ParagraphStyle("teksti",  fontName="Helvetica",      fontSize=9,  leading=11.5, spaceAfter=5)
S_KUVATXT = ParagraphStyle("kuvatxt", fontName="Helvetica",      fontSize=8.5, leading=10, spaceBefore=2)
S_PIENI   = ParagraphStyle("pieni",   fontName="Helvetica",      fontSize=8,  leading=10,
                           textColor=colors.HexColor("#555555"))


# ── Sivupohja: ylä-/alatunniste ja sivunumerointi "1(N)" ──────────────────────

def _numero_canvas_tehdas(otsikkorivit, alaotsikko):
    """Canvas-luokka joka piirtää ylä-/alatunnisteen ja sivunumeron 1(N)."""

    class _NumeroCanvas(rl_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._tallennetut = []

        def showPage(self):
            self._tallennetut.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            yhteensa = len(self._tallennetut)
            for tila in self._tallennetut:
                self.__dict__.update(tila)
                self._piirra_kehys(yhteensa)
                rl_canvas.Canvas.showPage(self)
            rl_canvas.Canvas.save(self)

        def _piirra_kehys(self, yhteensa):
            self.saveState()
            pw, ph = A4
            # Logo vasempaan yläkulmaan: merkki 14 mm + nimi (väli ¼ merkistä)
            if _LOGO.exists():
                try:
                    koko = 14 * mm
                    x0, y0 = 18 * mm, ph - 16 * mm - koko
                    self.drawImage(str(_LOGO), x0, y0, width=koko, height=koko, mask="auto")
                    xn = x0 + koko + koko / 4
                    self.setFillColor(colors.HexColor("#14232A"))
                    self.setFont("Helvetica-Bold", 10)
                    self.drawString(xn, y0 + koko * 0.55, "Uudenmaan")
                    self.drawString(xn, y0 + koko * 0.55 - 11, "Asbestipurku")
                    leveys = self.stringWidth("Asbestipurku ", "Helvetica-Bold", 10)
                    self.setFillColor(colors.HexColor("#7A888B"))
                    self.setFont("Helvetica", 10)
                    self.drawString(xn + leveys, y0 + koko * 0.55 - 11, "Oy")
                    self.setFillColor(colors.black)
                except Exception:
                    pass
            # Otsikko oikealle + sivunumero
            self.setFont("Helvetica", 9)
            self.drawRightString(pw - 16 * mm, ph - 17 * mm,
                                 f"{self._pageNumber}({yhteensa})")
            y = ph - 17 * mm
            self.setFont("Helvetica-Bold", 10.5)
            for rivi in otsikkorivit:
                self.drawRightString(pw - 28 * mm, y, rivi)
                y -= 4.6 * mm
            if alaotsikko:
                self.setFont("Helvetica", 9)
                self.drawRightString(pw - 28 * mm, y, alaotsikko)
            # Vaakaviiva otsikon alle
            self.setStrokeColor(colors.HexColor("#333333"))
            self.setLineWidth(0.8)
            self.line(18 * mm, ph - 34 * mm, pw - 16 * mm, ph - 34 * mm)
            # Alatunniste
            self.setLineWidth(0.5)
            self.line(18 * mm, 20 * mm, pw - 16 * mm, 20 * mm)
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#444444"))
            self.drawString(18 * mm, 15.5 * mm, YRITYS["nimi"])
            self.drawString(18 * mm, 11.5 * mm, YRITYS["www"])
            self.drawCentredString(pw / 2, 15.5 * mm, YRITYS["osoite"])
            self.drawCentredString(pw / 2, 11.5 * mm, YRITYS["posti"])
            self.drawRightString(pw - 16 * mm, 15.5 * mm, YRITYS["ytunnus"])
            self.drawRightString(pw - 16 * mm, 11.5 * mm, YRITYS["puhelin"])
            self.restoreState()

    return _NumeroCanvas


def _dokumentti(otsikkorivit, alaotsikko, sisalto) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=16 * mm,
        topMargin=40 * mm, bottomMargin=26 * mm,
        title=" ".join(otsikkorivit),
    )
    doc.build(sisalto, canvasmaker=_numero_canvas_tehdas(otsikkorivit, alaotsikko))
    return buf.getvalue()


# ── Sisältöapurit ──────────────────────────────────────────────────────────────

def _kentat(parit, sarakkeita=2):
    """Label+arvo -parit taulukkona (kuten mallidokumenttien kenttäruudukot)."""
    parit = [p for p in parit if p]
    rivit, leveys = [], (A4[0] - 34 * mm) / sarakkeita
    for i in range(0, len(parit), sarakkeita):
        ryhma = parit[i:i + sarakkeita]
        rivit.append([Paragraph(lb, S_LABEL) for lb, _ in ryhma]
                     + [""] * (sarakkeita - len(ryhma)))
        rivit.append([Paragraph(str(ar) if ar else "—", S_ARVO) for _, ar in ryhma]
                     + [""] * (sarakkeita - len(ryhma)))
    t = Table(rivit, colWidths=[leveys] * sarakkeita)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return t


def _rivit(teksti, tyyli=S_TEKSTI):
    return [Paragraph(kpl.strip(), tyyli) for kpl in teksti.strip().split("\n\n") if kpl.strip()]


# ── Turvallisuussuunnitelman vakiotekstit (yrityksen oma pohja) ────────────────

VAKIO_TOIMIMINEN = """
Työnantajan on selvitettävä työstä aiheutuvat vaarat ja tarvittaessa arvioitava jäännösvaaran merkitys työntekijöiden turvallisuudelle ja terveydelle. Selvitys ja arviointi on tehtävä työturvallisuuslain 10 §:n edellyttämällä tavalla.

Työnantajan on huolehdittava siitä, että työntekijän työstä johtuva altistuminen asbestille on mahdollisimman vähäistä. Työnantajan on huolehdittava, että altistumisvaara ja todennäköinen altistumisvaara kohdistuu mahdollisimman pieneen määrään työntekijöitä. Altistumisvaara voi muodostua ja kohdistua myös muuta työtä suorittaviin työntekijöihin suojausten pettämisen, laiterikkojen tai muun syyn vuoksi.

Työnantajan on suunniteltava ja toteutettava toimenpiteet, joilla asbestin vapautuminen työssä estetään ja rajoitetaan mahdollisimman vähäiseksi. Asbestin vapautumisen estämiseksi ja vähentämiseksi on käytettävä työ-/purkumenetelmiä, joissa asbestia sisältävän materiaalin / rakenteen rikkoutuminen on mahdollisimman vähäistä. Vapautuvan asbestin leviämisen estämiseksi on käytettävä kohdepoistoa, kastelua, purkupusseja tai muita pölynhallintaan soveltuvia keinoja ja välineitä.

Purkutyössä esille tulleiden, ennalta havaitsemattomien asbestimateriaalien löytyessä työ on keskeytettävä ja altistumisvaara selvitettävä. Asbestilöydöksestä on ilmoitettava rakennuttajalle ja asbestikartoitusta on täydennettävä. Materiaalia, jonka asbestipitoisuudesta ei tehdyistä selvityksistä huolimatta voida luotettavasti varmistua, on pidettävä ja käsiteltävä asbestia sisältävänä ja sen purku on tehtävä osastointimenetelmällä.

Päätoteuttajan on yhteisellä rakennustyömaalla omalta osaltaan huolehdittava työympäristön turvallisuudesta, huomioiden myös haitta-aineita sisältävien rakenteiden purku ja niiden aiheuttama vaara. Tilanteissa, joissa on perusteltu syy epäillä, että asbestipölyä on vapautunut hengitysilmaan työssä, jossa ei ole tunnistettu asbestia ennen työn aloittamista, päätoteuttajan on keskeytettävä työ vaikutusalueella. Työn keskeyttämisvelvollisuus on päätoteuttajan lisäksi myös yksittäisellä työnantajalla.
"""

VAKIO_TYOVALINEET = """
Ilmankäsittelylaitteille ei suoriteta työmaalla huoltoa, vaan se tehdään yrityksen laitehuoltotilassa. Ainoa huoltotoimenpide, joka voidaan suorittaa, on karkeasuodattimen vaihto, mikäli se on mahdollista tehdä turvallisesti. Laitteisiin vaihdetaan suodattimet valmistajien ohjeiden mukaisesti laitehuoltotilassa. Ilmankäsittelylaitteet tulpataan ja teipataan umpeen, jotta asbesti ei leviä koneista siirtämisen aikana.
"""

VAKIO_JATE = """
Jätteet pakataan purkusäkkeihin tai mahdollisesti muovitetaan, jos irrotettu kokonaisena. Mikäli jätteitä on tilanpuutteen vuoksi poistettava osastoinnin sisältä, imuroidaan säkit puhtaiksi ja varovasti sulkutunnelia tai pakkausta rikkomatta jätteet poistetaan sulkutunnelin kautta. Jätteet merkitään aina varoitusteipein, että sisältävät asbestia. Jätteet kuljetetaan välittömästi autossa kaatopaikalle. Mikäli jätteitä joudutaan syystä tai toisesta säilömään työmaalla, on sen tapahduttava sellaisessa tilassa, joka saadaan lukittua tai peitettyä, ja merkittävä varoituskyltein/teipillä.
"""

VAKIO_PUHTAUS = """
Purkutyön jälkeen tilaajalle luovutetaan tila lopetusraportin kanssa, jossa vastuuhenkilöiden allekirjoitukset.
"""

VAKIO_HATA = """
Tapaturman tapahtuessa, jos mahdollista, poistutaan suojauksien sisältä oikeaoppisesti. Jos tapaturma on vakava ja aiheuttaa hengenvaaraa, saa suojaukset poistaa avunannon ajaksi. Mikäli tapaturman johdosta tarvitaan hoitoa, on soitettava hätänumeroon (112). Teknisten vikojen tapahtuessa työ keskeytetään välittömästi ja vian syytä ruvetaan selvittämään ja korjaamaan.
"""

VAKIO_TIEDOKSIANTO = """
Turvallisuussuunnitelma on annettava tiedoksi asbestipurkutyöhön osallistuville työntekijöille. Turvallisuussuunnitelma on annettava tiedoksi yhteisellä rakennustyömaalla työmaan päätoteuttajalle. Päätoteuttajan on esitettävä suunnitelma rakennuttajalle. Asbestipurkutyöhön ryhtyvän työnantajan on yhteisellä työpaikalla huolehdittava suunnitelman tiedoksiannosta työn vaikutuspiirissä oleville toiminnanharjoittajille ja heidän työntekijöilleen.
"""


# ── 1. Turvallisuussuunnitelma ────────────────────────────────────────────────

def luo_turvallisuussuunnitelma(tiedot: dict) -> bytes:
    """
    tiedot-avaimet: kohde_nimi, tyonumero, pvm, osallistujat [(nimi, rooli)],
    tarkenne, osastointi, materiaali, sijainti, menetelma, menetelma_kuvaus,
    rajaaminen, suojaimet, jatteen_sijoituspaikka, ilmamittaus_suorittaja,
    analysointipaikka, vastuu_suorittaja, vastuu_tilaaja, paivitykset,
    allekirjoittaja, allekirjoittaja_titteli
    """
    e = []
    otsake = tiedot.get("kohde_nimi", "")
    if tiedot.get("tyonumero"):
        otsake += f"  ·  Työnumero {tiedot['tyonumero']}"
    e.append(Paragraph(otsake, S_KOHDE))
    e.append(Paragraph(tiedot.get("pvm", ""), S_PVM))

    e.append(Paragraph("Osallistujat", S_OSIO))
    e.append(_kentat([(nimi, rooli) for nimi, rooli in tiedot.get("osallistujat", [])] or
                     [("—", "")]))

    e.append(Paragraph("Perustiedot", S_OSIO))
    e.append(_kentat([("Tarkenne", tiedot.get("tarkenne", "")),
                      ("Osastointi", tiedot.get("osastointi", ""))]))

    e.append(Paragraph("1. Altistuksen arviointi sekä altistumisalueen rajaaminen ja siellä toimiminen", S_OSIO))
    e.append(_kentat([("Purettava asbestipitoinen materiaali", tiedot.get("materiaali", "")),
                      ("Asbestin sijainti", tiedot.get("sijainti", "")),
                      ("Purkutyömenetelmä", tiedot.get("menetelma", "")),
                      ("Purkutyömenetelmän kuvaus", tiedot.get("menetelma_kuvaus", ""))]))
    e.append(_kentat([("Altistumisalueen rajaaminen", tiedot.get("rajaaminen", ""))], 1))
    e.append(Paragraph("Toimiminen altistumisalueella", S_LABEL))
    e.extend(_rivit(VAKIO_TOIMIMINEN))

    e.append(Paragraph("2. Henkilösuojainten valinta", S_OSIO))
    e.extend(_rivit(tiedot.get("suojaimet", "") or "—"))

    e.append(Paragraph("3. Työvälineiden käsittely", S_OSIO))
    e.extend(_rivit(VAKIO_TYOVALINEET))

    e.append(Paragraph("4. Asbestijätteen käsittely", S_OSIO))
    e.extend(_rivit(VAKIO_JATE))
    e.append(_kentat([("Jätteiden lopullinen sijoituspaikka",
                       tiedot.get("jatteen_sijoituspaikka", ""))], 1))

    e.append(Paragraph("5. Purkutyöalueen puhtauden varmistaminen", S_OSIO))
    e.append(_kentat([("Ilmamittauksen suorittaja kohteessa", tiedot.get("ilmamittaus_suorittaja", "")),
                      ("Näytteen analysointipaikka", tiedot.get("analysointipaikka", ""))]))
    e.extend(_rivit(VAKIO_PUHTAUS))

    e.append(Paragraph("6. Hätätilanteessa toimiminen", S_OSIO))
    e.extend(_rivit(VAKIO_HATA))

    e.append(Paragraph("7. Suunnitelman seuranta ja ajan tasalla pitäminen", S_OSIO))
    e.append(_kentat([("Työn suorittajan vastuuhenkilö", tiedot.get("vastuu_suorittaja", "")),
                      ("Tilaajan vastuuhenkilö", tiedot.get("vastuu_tilaaja", "")),
                      ("Tarvittavat päivitykset", tiedot.get("paivitykset", ""))]))
    e.extend(_rivit(VAKIO_TIEDOKSIANTO))

    # Allekirjoitussivu
    e.append(PageBreak())
    e.append(Spacer(1, 30 * mm))
    e.append(Table([[""]], colWidths=[70 * mm], style=TableStyle(
        [("LINEBELOW", (0, 0), (0, 0), 0.8, colors.black)])))
    allek = tiedot.get("allekirjoittaja", "")
    titteli = tiedot.get("allekirjoittaja_titteli", "")
    e.append(Paragraph(f"{allek}, {YRITYS['nimi']},<br/>{titteli}", S_ARVO))

    return _dokumentti(["ASBESTIPURKUTYÖN", "TURVALLISUUSSUUNNITELMA"],
                       tiedot.get("kohde_nimi", ""), e)


# ── 2. Ennakkoilmoituksen esitäyttö ───────────────────────────────────────────

def luo_ennakkoilmoitus_esitaytto(tiedot: dict, tyontekijat: list, laitteet: list) -> bytes:
    """
    Esitäyttödokumentti, josta tiedot kopioidaan AVIn sähköiseen asiointiin.
    tyontekijat: pätevyysrekisterin rivejä, laitteet: kalustorekisterin rivejä.
    """
    e = []
    e.append(Paragraph(tiedot.get("kohde_nimi", ""), S_KOHDE))
    e.append(Paragraph(tiedot.get("pvm", ""), S_PVM))
    e.append(Paragraph(
        "Esitäyttö AVIn sähköistä asiointia varten — ilmoitus jätetään viimeistään "
        "7 vrk ennen työn aloitusta (VNa 798/2015).", S_PIENI))

    e.append(Paragraph("Ilmoittaja", S_OSIO))
    e.append(_kentat([("Nimi", tiedot.get("ilmoittaja", "")),
                      ("Puhelin", tiedot.get("ilmoittaja_puhelin", "")),
                      ("Sähköposti", tiedot.get("ilmoittaja_email", ""))]))

    e.append(Paragraph("Asbestipurkutyön suorittaja", S_OSIO))
    e.append(_kentat([("Yrityksen nimi", YRITYS["nimi"]),
                      ("Y-tunnus", "2817254-1"),
                      ("Osoite", f"{YRITYS['osoite']}, {YRITYS['posti']}"),
                      ("Puhelin", "044 300 9672"),
                      ("Sähköposti", "info@uudenmaanasbestipurku.fi")]))

    e.append(Paragraph("Asbestipurkutyön tilaaja", S_OSIO))
    e.append(_kentat([("Yrityksen nimi", tiedot.get("tilaaja_yritys", "")),
                      ("Y-tunnus", tiedot.get("tilaaja_ytunnus", "")),
                      ("Yhteyshenkilö", tiedot.get("tilaaja_yhteyshenkilo", "")),
                      ("Puhelin", tiedot.get("tilaaja_puhelin", "")),
                      ("Sähköposti", tiedot.get("tilaaja_email", ""))]))

    e.append(Paragraph("Asbestipurkutyön kohde", S_OSIO))
    e.append(_kentat([("Työmaan nimi", tiedot.get("kohde_nimi", "")),
                      ("Yksilöidyt alueet", tiedot.get("alueet", "")),
                      ("Osoite", tiedot.get("osoite", "")),
                      ("Sijaintikunta", tiedot.get("kunta", "")),
                      ("Työn alkamispäivä", tiedot.get("aloitus_pvm", "")),
                      ("Työn päättymispäivä", tiedot.get("lopetus_pvm", ""))]))

    e.append(Paragraph("Asbestikartoitus", S_OSIO))
    e.append(_kentat([("Havainnot (sijainti, määrä ja laatu)", tiedot.get("kartoitus_havainnot", "")),
                      ("Kartoituksen suorituspäivä", tiedot.get("kartoitus_pvm", "")),
                      ("Kartoituksen tekijä", tiedot.get("kartoittaja", "")),
                      ("Kartoittajan Y-tunnus / yhteystiedot", tiedot.get("kartoittaja_yhteys", ""))]))

    e.append(Paragraph("Asbestipurkutyömenetelmä", S_OSIO))
    e.append(_kentat([("Menetelmä", tiedot.get("menetelma", "")),
                      ("Menetelmäkuvaus", tiedot.get("menetelma_kuvaus", ""))]))

    e.append(Paragraph("Käytettävät ilmankäsittelylaitteet (kalustorekisteristä)", S_OSIO))
    if laitteet:
        rivit = [[Paragraph("Laite", S_LABEL), Paragraph("Sarjanumero", S_LABEL),
                  Paragraph("Lisätiedot", S_LABEL)]]
        for l in laitteet:
            rivit.append([Paragraph(f"{l.get('nro','')} {l.get('laite','')}", S_TEKSTI),
                          Paragraph(l.get("sarjanumero", "") or "—", S_TEKSTI),
                          Paragraph(l.get("huomiot", "") or "", S_TEKSTI)])
        t = Table(rivit, colWidths=[70 * mm, 45 * mm, 60 * mm])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black),
            ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#BBBBBB")),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        e.append(t)
    else:
        e.append(Paragraph("—", S_ARVO))

    e.append(Paragraph("Purkutyöntekijät (pätevyysrekisteristä)", S_OSIO))
    if tyontekijat:
        for t_ in tyontekijat:
            e.append(Paragraph(t_.get("nimi", ""), S_LABEL))
            e.append(_kentat([
                ("Työnantaja", t_.get("tyonantaja", YRITYS["nimi"])),
                ("Pätevyysrekisterissä", "Kyllä" if t_.get("rekisterissa") else "TARKISTA"),
                ("Terveystarkastus suoritettu", t_.get("terveystarkastus_pvm", "")),
                ("Terveystarkastus voimassa", t_.get("terveystarkastus_voimassa", "")),
                ("Hengityksensuojaimen tiiviystestaus", t_.get("tiiviystestaus_pvm", "")),
                ("Todistus erityisestä opetuksesta", t_.get("koulutus_pvm", "")),
            ]))
    else:
        e.append(Paragraph("—", S_ARVO))

    e.append(Paragraph("Asbestipitoisen jätteen käsittely", S_OSIO))
    e.append(_kentat([("Jätteenkäsittelylaitos", tiedot.get("jatteen_sijoituspaikka", ""))], 1))

    return _dokumentti(["ASBESTIPURKUTYÖN ENNAKKOILMOITUS", "ESITÄYTTÖ AVIn ASIOINTIIN"],
                       tiedot.get("kohde_nimi", ""), e)


# ── 3. Aloitus- ja lopetusraportti ────────────────────────────────────────────

def _sovitettu_kuva(data: bytes, max_w=80 * mm, max_h=58 * mm):
    ir = ImageReader(io.BytesIO(data))
    iw, ih = ir.getSize()
    suhde = min(max_w / iw, max_h / ih)
    return RLImage(io.BytesIO(data), width=iw * suhde, height=ih * suhde)


def luo_aloitus_lopetusraportti(tiedot: dict, kuvat: list, liite_pdfit: list = None) -> bytes:
    """
    tiedot: kohde_nimi, tyonumero, pvm, osallistujat [(nimi, yritys)],
            aloitus_pvm, lopetus_pvm, urakoitsija_vastuu, paatoteuttaja,
            paatoteuttaja_vastuu, huomiot_aloitus, havainnot
    kuvat:  [{"data": bytes, "teksti": str}] järjestyksessä (aloitus → lopetus)
    liite_pdfit: [bytes] — liitetään raportin perään (ilmamittaus, jätetodistus)
    """
    e = []
    otsake = tiedot.get("kohde_nimi", "")
    if tiedot.get("tyonumero"):
        otsake += f"  ·  Työnumero {tiedot['tyonumero']}"
    e.append(Paragraph(otsake, S_KOHDE))
    e.append(Paragraph(tiedot.get("pvm", ""), S_PVM))

    e.append(Paragraph("Osallistujat", S_OSIO))
    e.append(_kentat(list(tiedot.get("osallistujat", [])) or [("—", "")]))

    e.append(Paragraph("Aikataulu", S_OSIO))
    e.append(_kentat([("Työmaan alkamispäivä", tiedot.get("aloitus_pvm", "")),
                      ("Työmaan lopettamispäivä", tiedot.get("lopetus_pvm", ""))]))

    e.append(Paragraph("Vastuuhenkilöt ja yhteystiedot", S_OSIO))
    e.append(_kentat([("Asbestiurakoitsija", YRITYS["nimi"]),
                      ("Asbestiurakoitsijan vastuuhenkilö", tiedot.get("urakoitsija_vastuu", "")),
                      ("Päätoteuttaja", tiedot.get("paatoteuttaja", "")),
                      ("Päätoteuttajan vastuuhenkilö", tiedot.get("paatoteuttaja_vastuu", ""))]))

    e.append(Paragraph("Huomiot asbestipurkutyön aloituksesta ja lähtötilanteesta", S_OSIO))
    e.extend(_rivit(tiedot.get("huomiot_aloitus", "") or "—", S_ARVO))
    if kuvat:
        e.append(Paragraph(f"(Ks. kuvat 1–{len(kuvat)})", S_PIENI))

    if tiedot.get("havainnot"):
        e.append(Paragraph("Havainnot työn aikana", S_OSIO))
        e.extend(_rivit(tiedot["havainnot"], S_ARVO))

    # Kuvaliitteet: 4 kuvaa / sivu (2×2), numeroidut kuvatekstit
    if kuvat:
        e.append(PageBreak())
        e.append(Paragraph("Kuvaliitteet", S_OSIO))
        solu_leveys = (A4[0] - 34 * mm) / 2
        for i in range(0, len(kuvat), 2):
            pari = kuvat[i:i + 2]
            solut = []
            for j, kuva in enumerate(pari):
                nro = i + j + 1
                teksti = kuva.get("teksti", "") or ""
                try:
                    sisus = [_sovitettu_kuva(kuva["data"]),
                             Paragraph(f"<b>Kuva {nro}</b> — {teksti}" if teksti
                                       else f"<b>Kuva {nro}</b>", S_KUVATXT)]
                except Exception:
                    sisus = [Paragraph(f"Kuva {nro} — ei voitu lukea", S_KUVATXT)]
                solut.append(sisus)
            while len(solut) < 2:
                solut.append("")
            t = Table([solut], colWidths=[solu_leveys] * 2)
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            e.append(t)

    runko = _dokumentti(["ASBESTIPURKUTYÖN ALOITUS- JA", "LOPETUSRAPORTTI"],
                        tiedot.get("kohde_nimi", ""), e)

    if liite_pdfit:
        return yhdista_pdfit(runko, liite_pdfit)
    return runko


# ── 4. Tarjous ────────────────────────────────────────────────────────────────

def luo_tarjous_pdf(tiedot: dict, rivit: list, valisumma: float,
                    loppusumma: float, minimi_kaytossa: bool,
                    asetukset: dict) -> bytes:
    """
    tiedot: kohde_nimi, tyonumero, osoite, pvm, tilaaja_yritys, saate,
            kartoitus_viite, laatija
    rivit:  [{"nimi","maara","yksikko","a_hinta","summa"}]
    """
    e = []
    otsake = tiedot.get("kohde_nimi") or tiedot.get("osoite", "")
    if tiedot.get("tyonumero"):
        otsake += f"  ·  Työnumero {tiedot['tyonumero']}"
    e.append(Paragraph(otsake, S_KOHDE))
    e.append(Paragraph(tiedot.get("pvm", ""), S_PVM))

    e.append(_kentat([("Tilaaja", tiedot.get("tilaaja_yritys", "")),
                      ("Kohde", tiedot.get("osoite", ""))]))

    if tiedot.get("saate"):
        e.extend(_rivit(tiedot["saate"], S_ARVO))

    e.append(Paragraph("Erittely", S_OSIO))
    taul = [[Paragraph("Työvaihe / kustannus", S_LABEL),
             Paragraph("Määrä", S_LABEL), Paragraph("Yks.", S_LABEL),
             Paragraph("à € (ALV 0 %)", S_LABEL), Paragraph("Yht. €", S_LABEL)]]
    for r in rivit:
        maara = f"{r['maara']:g}"
        taul.append([Paragraph(r["nimi"], S_TEKSTI),
                     Paragraph(maara, S_TEKSTI),
                     Paragraph(r.get("yksikko", ""), S_TEKSTI),
                     Paragraph(f"{r['a_hinta']:.2f}", S_TEKSTI),
                     Paragraph(f"{r['summa']:.2f}", S_TEKSTI)])
    taul.append([Paragraph("<b>Välisumma</b>", S_TEKSTI), "", "", "",
                 Paragraph(f"<b>{valisumma:.2f}</b>", S_TEKSTI)])
    if minimi_kaytossa:
        taul.append([Paragraph("Minimiveloitus", S_TEKSTI), "", "", "",
                     Paragraph(f"{loppusumma:.2f}", S_TEKSTI)])
    taul.append([Paragraph("<b>YHTEENSÄ (ALV 0 %)</b>", S_LABEL), "", "", "",
                 Paragraph(f"<b>{loppusumma:.2f} €</b>", S_LABEL)])
    t = Table(taul, colWidths=[88 * mm, 20 * mm, 15 * mm, 26 * mm, 26 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black),
        ("LINEBELOW", (0, 1), (-1, -4), 0.3, colors.HexColor("#CCCCCC")),
        ("LINEABOVE", (0, -1), (-1, -1), 0.6, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    e.append(t)

    e.append(Paragraph("Ehdot", S_OSIO))
    ehdot = [
        "Hinnat ALV 0 % — rakentamispalvelun käännetty verovelvollisuus (AVL 8 c §).",
        f"Tarjous on voimassa {asetukset.get('voimassaolo_vrk', 30)} vrk tarjouspäivästä.",
        f"Maksuehto {asetukset.get('maksuehto', '14 pv netto')}.",
        "Työ tehdään VNa 798/2015 mukaisesti; ennakkoilmoitus työsuojeluviranomaiselle "
        "sisältyy hintaan. Puhtaus varmistetaan puhdastilamittauksella (raja 0,01 kuitua/cm³) "
        "ja työstä toimitetaan aloitus- ja lopetusraportti kuvineen sekä jätteenkäsittelyasiakirja.",
        "Mikäli purkutyön aikana paljastuu kartoituksessa mainitsemattomia asbestipitoisia "
        "materiaaleja, niiden purku sovitaan ja veloitetaan lisätyönä "
        "(työntekijä 55 €/h, työnjohto 75 €/h, ALV 0 %).",
    ]
    if tiedot.get("kartoitus_viite"):
        ehdot.append(f"Tarjous perustuu kartoitusraporttiin {tiedot['kartoitus_viite']} "
                     "ja toimitettuihin valokuviin purkualuerajauksineen.")
    for rivi in ehdot:
        e.append(Paragraph("•  " + rivi, S_TEKSTI))

    e.append(Spacer(1, 12 * mm))
    e.append(Table([[""]], colWidths=[70 * mm], style=TableStyle(
        [("LINEBELOW", (0, 0), (0, 0), 0.8, colors.black)])))
    e.append(Paragraph(f"{tiedot.get('laatija', '')}, {YRITYS['nimi']}", S_ARVO))

    return _dokumentti(["TARJOUS", "ASBESTIPURKUTYÖ"],
                       tiedot.get("osoite", ""), e)


# ── PDF-yhdistys ja kuvan kääriminen PDF-sivuksi ──────────────────────────────

def kuva_pdfksi(data: bytes) -> bytes:
    """Kääri kuva (jpg/png) yhdeksi A4-PDF-sivuksi."""
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=A4)
    ir = ImageReader(io.BytesIO(data))
    iw, ih = ir.getSize()
    max_w, max_h = A4[0] - 40 * mm, A4[1] - 40 * mm
    suhde = min(max_w / iw, max_h / ih)
    w, h = iw * suhde, ih * suhde
    c.drawImage(ir, (A4[0] - w) / 2, (A4[1] - h) / 2, w, h)
    c.showPage()
    c.save()
    return buf.getvalue()


def yhdista_pdfit(paa: bytes, liitteet: list) -> bytes:
    """Yhdistää pää-PDF:n ja liitteet yhdeksi tiedostoksi. Kuvaliite kääritään sivuksi."""
    from pypdf import PdfReader, PdfWriter
    w = PdfWriter()
    w.append(PdfReader(io.BytesIO(paa)))
    for liite in liitteet:
        if not liite:
            continue
        data = bytes(liite)
        if not data.startswith(b"%PDF"):
            data = kuva_pdfksi(data)
        try:
            w.append(PdfReader(io.BytesIO(data)))
        except Exception:
            continue
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()
