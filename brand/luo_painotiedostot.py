"""
UAP-merkin painotiedostot ja työvaatteiden painatusohje.

    python3 brand/luo_painotiedostot.py

Tuottaa kansioon brand/painatus/:
  - vektori-PDF:t merkin versioista (väri, petroli, musta, valkoinen, negatiivi)
  - brodeerausversio (paksumpi kehys, vahvemmat kirjaimet ja pylväät) SVG + PDF
  - tarrapohja (merkki + leikkuuviiva spot-värillä "CutContour")
  - UAP_tyovaatteet_painatusohje.pdf — sijoitukset, koot ja tiedostot toimittajalle

Lähde on brand/svg/uap-merkki-vari.svg (polut M/L/Q/Z, viewBox 120×120). Vain merkki —
EI yrityksen nimeä eikä sanaa "asbesti" vaatteisiin (Sakari 21.10.2026).
"""

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import CMYKColorSep
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

BRAND = Path(__file__).parent
ULOS = BRAND / "painatus"

PETROLI, KLINIKKA, KLINIKKA_V = "#14232A", "#1F7A73", "#3E9A92"
LUONNONVALKO, HUURRE, TERAS = "#F2F4F4", "#DDEAE8", "#B7C2C4"
HV_KELTAINEN, HV_ORANSSI = "#E4EE2B", "#FF6B1A"      # huomiovärit (näyttöarvio)
HEIJASTIN = "#B9BEC1"

# ── Merkin geometria lähde-SVG:stä ─────────────────────────────────────────────

_svg = (BRAND / "svg" / "uap-merkki-vari.svg").read_text()
KIRJAIN_POLKU = re.search(r'<path d="([^"]+)"', _svg).group(1)
PYLVAAT = [tuple(float(v) for v in m) for m in
           re.findall(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" fill', _svg)]


def _komennot(d: str):
    for kirjain, luvut in re.findall(r"([MLQZ])([^MLQZ]*)", d):
        yield kirjain, [float(v) for v in luvut.replace(",", " ").split()]


def _kirjaimet(c, ox, oy, s, dy=0.0):
    """Kirjainpolku reportlab-polkuna. SVG y alaspäin → PDF y ylöspäin."""
    p = c.beginPath()
    X = lambda x: ox + x * s
    Y = lambda y: oy + (120 - (y + dy)) * s
    cx = cy = 0.0
    for k, v in _komennot(KIRJAIN_POLKU):
        if k == "M":
            cx, cy = v; p.moveTo(X(cx), Y(cy))
        elif k == "L":
            cx, cy = v; p.lineTo(X(cx), Y(cy))
        elif k == "Q":                                   # kvadraattinen → kuutio
            qx, qy, ex, ey = v
            c1 = (cx + 2 / 3 * (qx - cx), cy + 2 / 3 * (qy - cy))
            c2 = (ex + 2 / 3 * (qx - ex), ey + 2 / 3 * (qy - ey))
            p.curveTo(X(c1[0]), Y(c1[1]), X(c2[0]), Y(c2[1]), X(ex), Y(ey))
            cx, cy = ex, ey
        elif k == "Z":
            p.close()
    return p


def merkki(c, x, y, koko, kehys=PETROLI, kirjain=PETROLI, pylvas=KLINIKKA, brodeeraus=False):
    """Piirtää UAP-merkin vektorina: vasen alakulma (x, y), leveys = koko pistettä."""
    s = koko / 120.0
    c.saveState()
    # Kehys
    vahvuus = 5.0 if brodeeraus else 2.5
    sisa = vahvuus / 2
    c.setStrokeColor(colors.HexColor(kehys)); c.setLineWidth(vahvuus * s)
    c.roundRect(x + sisa * s, y + sisa * s, (120 - vahvuus) * s, (120 - vahvuus) * s,
                (15 - vahvuus) * s + sisa * s, stroke=1, fill=0)
    # Brodeerausversio: pylväät ×1,45 (suhteet säilyvät), ryhmä keskitetään uudelleen
    if brodeeraus:
        kerroin, lev, vali = 1.45, 9.0, 4.5
        korkeudet = [h * kerroin for (_, _, _, h) in PYLVAAT]
        x0 = 60 - (4 * lev + 3 * vali) / 2
        kirjain_ala = 62.75
        ylin = kirjain_ala + 10                        # peruslinja → korkeimman yläreuna 10
        pohja = ylin + max(korkeudet)
        dy = -((34.91 + pohja) / 2 - 60)               # ryhmän pystykeskitys
        pylvaat = [(x0 + i * (lev + vali), pohja - h, lev, h) for i, h in enumerate(korkeudet)]
    else:
        dy = 0.0
        pylvaat = PYLVAAT
    # Kirjaimet (brodeerauksessa lisävahvuus ääriviivalla)
    c.setFillColor(colors.HexColor(kirjain)); c.setStrokeColor(colors.HexColor(kirjain))
    p = _kirjaimet(c, x, y, s, dy)
    if brodeeraus:
        c.setLineWidth(1.1 * s); c.setLineJoin(1)
        c.drawPath(p, stroke=1, fill=1, fillMode=0)
    else:
        c.drawPath(p, stroke=0, fill=1, fillMode=0)
    # Pylväät
    c.setFillColor(colors.HexColor(pylvas))
    for (px, py, pw, ph) in pylvaat:
        py_ = py + dy
        c.rect(x + px * s, y + (120 - py_ - ph) * s, pw * s, ph * s, stroke=0, fill=1)
    c.restoreState()


# ── Yksittäiset painotiedostot ─────────────────────────────────────────────────

VERSIOT = {
    # nimi: (kehys, kirjaimet, pylväät, tausta-esikatselu, kuvaus)
    "vari":       (PETROLI, PETROLI, KLINIKKA, None,     "Pääversio vaalealle pohjalle"),
    "petroli":    (PETROLI, PETROLI, PETROLI,  None,     "Yksivärinen petroli: huomiovaatteet, yksiväripainatus"),
    "musta":      ("#000000", "#000000", "#000000", None, "Yksivärinen musta"),
    "valkoinen":  ("#FFFFFF", "#FFFFFF", "#FFFFFF", PETROLI, "Yksivärinen valkoinen: mustat ja tummat vaatteet"),
    "negatiivi":  (LUONNONVALKO, LUONNONVALKO, KLINIKKA_V, PETROLI, "Kaksivärinen tummalle pohjalle"),
}


def _yksi(nimi, koko_mm, brodeeraus=False, **varit):
    koko = koko_mm * mm
    c = canvas.Canvas(str(ULOS / nimi), pagesize=(koko, koko))
    c.setTitle(nimi.replace(".pdf", "")); c.setAuthor("UAP"); c.setCreator("brand/luo_painotiedostot.py")
    merkki(c, 0, 0, koko, brodeeraus=brodeeraus, **varit)
    c.showPage(); c.save()


def _brodeeraus_svg(nimi, kehys, kirjain, pylvas):
    """Brodeerausversio SVG:nä (samat mitat kuin PDF:ssä)."""
    kerroin, lev, vali = 1.45, 9.0, 4.5
    korkeudet = [h * kerroin for (_, _, _, h) in PYLVAAT]
    x0 = 60 - (4 * lev + 3 * vali) / 2
    pohja = 62.75 + 10 + max(korkeudet)
    dy = -((34.91 + pohja) / 2 - 60)
    rects = "".join(f'<rect x="{x0 + i * (lev + vali):.2f}" y="{pohja - h + dy:.2f}" width="{lev}" '
                    f'height="{h:.2f}" fill="{pylvas}"/>' for i, h in enumerate(korkeudet))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">'
           f'<title>UAP-merkki, brodeerausversio</title>'
           f'<rect x="2.5" y="2.5" width="115" height="115" rx="12.5" fill="none" stroke="{kehys}" stroke-width="5"/>'
           f'<g transform="translate(0 {dy:.2f})"><path d="{KIRJAIN_POLKU}" fill="{kirjain}" stroke="{kirjain}" '
           f'stroke-width="1.1" stroke-linejoin="round"/></g>{rects}</svg>')
    (ULOS / nimi).write_text(svg, encoding="utf-8")


def _tarra(nimi, koko_mm, tausta=LUONNONVALKO):
    """Tarra: valkoinen/luonnonvalko pohja, merkki, leikkuuviiva spot-värinä CutContour."""
    reuna = 3 * mm
    koko = koko_mm * mm
    sivu = koko + 2 * reuna
    c = canvas.Canvas(str(ULOS / nimi), pagesize=(sivu + 4 * mm, sivu + 4 * mm))
    c.setTitle(nimi.replace(".pdf", ""))
    o = 2 * mm
    c.setFillColor(colors.HexColor(tausta))
    c.roundRect(o, o, sivu, sivu, 5 * mm, stroke=0, fill=1)
    merkki(c, o + reuna, o + reuna, koko)
    leikkuu = CMYKColorSep(0, 1, 0, 0, spotName="CutContour", density=1)
    c.setStrokeColor(leikkuu); c.setLineWidth(0.25)
    c.roundRect(o, o, sivu, sivu, 5 * mm, stroke=1, fill=0)
    c.showPage(); c.save()


# ── Vaatesiluetit painatusohjeeseen (yksinkertaistetut, vektori) ──────────────

def _polku(c, pisteet, x, y, s):
    p = c.beginPath(); p.moveTo(x + pisteet[0][0] * s, y + pisteet[0][1] * s)
    for px, py in pisteet[1:]:
        p.lineTo(x + px * s, y + py * s)
    p.close(); return p


TPAITA = [(30, 0), (170, 0), (170, 150), (200, 128), (220, 170), (165, 210), (128, 210),
          (122, 200), (100, 194), (78, 200), (72, 210), (35, 210), (-20, 170), (0, 128), (30, 150)]
HUPPARI = [(28, 0), (172, 0), (172, 150), (210, 40), (228, 50), (182, 205), (140, 214),
           (128, 226), (100, 232), (72, 226), (60, 214), (18, 205), (-28, 50), (-10, 40), (28, 150)]
TAKKI = [(22, 0), (178, 0), (178, 150), (214, 30), (232, 40), (186, 210), (140, 220),
         (130, 234), (100, 238), (70, 234), (60, 220), (14, 210), (-32, 40), (-14, 30), (22, 150)]


def _vaate(c, muoto, x, y, s, vari, raidat=None):
    c.saveState()
    c.setFillColor(colors.HexColor(vari)); c.setStrokeColor(colors.HexColor("#5C6469"))
    c.setLineWidth(0.8)
    p = _polku(c, muoto, x, y, s)
    c.drawPath(p, stroke=1, fill=1)
    if raidat:                                       # heijastinraidat vartalon ympäri
        c.clipPath(_polku(c, muoto, x, y, s), stroke=0, fill=0)
        c.setFillColor(colors.HexColor(HEIJASTIN))
        for ry in raidat:
            c.rect(x - 40 * s, y + ry * s, 320 * s, 9 * s, stroke=0, fill=1)
    c.restoreState()


def _mitta(c, x1, y1, x2, y2, teksti):
    c.saveState()
    c.setStrokeColor(colors.HexColor(KLINIKKA)); c.setFillColor(colors.HexColor(KLINIKKA))
    c.setLineWidth(0.6); c.line(x1, y1, x2, y2)
    for (ax, ay) in ((x1, y1), (x2, y2)):
        c.line(ax, ay - 3, ax, ay + 3) if y1 == y2 else c.line(ax - 3, ay, ax + 3, ay)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString((x1 + x2) / 2, max(y1, y2) + 4, teksti)
    c.restoreState()


def _otsikko(c, teksti, ala=""):
    pw, ph = landscape(A4)
    c.setFillColor(colors.HexColor(LUONNONVALKO)); c.rect(0, 0, pw, ph, stroke=0, fill=1)
    merkki(c, 18 * mm, ph - 26 * mm, 13 * mm)
    c.setFillColor(colors.HexColor(PETROLI)); c.setFont("Helvetica-Bold", 20)
    c.drawString(38 * mm, ph - 18 * mm, teksti)
    if ala:
        c.setFillColor(colors.HexColor("#4A5A5F")); c.setFont("Helvetica", 10)
        c.drawString(38 * mm, ph - 24.5 * mm, ala)
    c.setStrokeColor(colors.HexColor("#C9D6D4")); c.setLineWidth(0.6)
    c.line(18 * mm, ph - 30 * mm, pw - 18 * mm, ph - 30 * mm)
    c.setFont("Helvetica", 8); c.setFillColor(colors.HexColor("#4A5A5F"))
    c.drawString(18 * mm, 10 * mm, "UAP · Työvaatteiden painatusohje · Tiedostot: brand/painatus/")
    c.drawRightString(pw - 18 * mm, 10 * mm, f"Sivu {c.getPageNumber()}")


def _tekstit(c, x, y, rivit, koko=10, rivi=14, leveys=None, vari=PETROLI):
    """Rivit: '**Otsikko:** loput' → otsikko lihavoituna. Rivitys annettuun leveyteen."""
    c.setFillColor(colors.HexColor(vari))
    for r in rivit:
        lihava = ""
        if r.startswith("**") and r.count("**") >= 2:
            lihava, r = r[2:].split("**", 1)
        sanat = [(w, True) for w in lihava.split()] + [(w, False) for w in r.split()]
        sisennys = len(r) - len(r.lstrip()) if not lihava else 0
        if not sanat:
            y -= rivi; continue
        xx = x + sisennys * koko * 0.3
        for sana, on_lihava in sanat:
            f = "Helvetica-Bold" if on_lihava else "Helvetica"
            w = c.stringWidth(sana + " ", f, koko)
            if leveys and xx + w - x > leveys and xx > x:
                y -= rivi; xx = x + koko                   # jatkorivi sisennettynä
            c.setFont(f, koko); c.drawString(xx, y, sana); xx += w
        y -= rivi
    return y


def _vaatesivu(c, otsikko, ala, muoto, vari, raidat, etu, taka, merkkivari, tekstit, takavari=None):
    """etu/taka = (logon leveys cm, sijainti-teksti) tai None."""
    _otsikko(c, otsikko, ala)
    pw, ph = landscape(A4)
    s = 1.05
    for i, (puoli, sijoitus) in enumerate((("ETU", etu), ("TAKA", taka))):
        x = 26 * mm + i * 100 * mm; y = 40 * mm
        _vaate(c, muoto, x, y, s, takavari if (i and takavari) else vari, raidat)
        c.setFont("Helvetica-Bold", 9); c.setFillColor(colors.HexColor("#4A5A5F"))
        c.drawCentredString(x + 100 * s, y - 8 * mm, puoli)
        if sijoitus:
            leveys_cm = sijoitus[0]
            koko = leveys_cm / 55 * 140 * s                # vaatteen leveys ≈ 55 cm
            if puoli == "ETU":
                lx, ly = x + 128 * s, y + 150 * s           # käyttäjän vasen rinta (kuvassa oikealla)
            else:
                lx, ly = x + 100 * s - koko / 2, y + 168 * s - koko
            merkki(c, lx, ly - (0 if puoli == "TAKA" else koko / 2), koko, **merkkivari)
            yl = ly - (0 if puoli == "TAKA" else koko / 2)
            _mitta(c, lx, yl + koko + 6, lx + koko, yl + koko + 6, f"{leveys_cm:g} cm")
    _tekstit(c, 222 * mm, ph - 45 * mm, tekstit, 9, 12.5, leveys=58 * mm)
    c.setFont("Helvetica-Oblique", 7.5); c.setFillColor(colors.HexColor("#4A5A5F"))
    c.drawString(26 * mm, 22 * mm, "Kaaviokuva — vaatteen malli ja mittasuhteet suuntaa-antavia, logon koko ja sijainti ohjeelliset.")


def painatusohje():
    pw, ph = landscape(A4)
    c = canvas.Canvas(str(ULOS / "UAP_tyovaatteet_painatusohje.pdf"), pagesize=(pw, ph))
    c.setTitle("UAP – Työvaatteiden painatusohje"); c.setAuthor("UAP")

    # 1. Kansi
    c.setFillColor(colors.HexColor(LUONNONVALKO)); c.rect(0, 0, pw, ph, stroke=0, fill=1)
    c.setFillColor(colors.HexColor(HUURRE)); c.rect(pw - 95 * mm, 0, 95 * mm, ph, stroke=0, fill=1)
    merkki(c, pw - 80 * mm, ph / 2 - 32 * mm, 64 * mm)
    c.setFillColor(colors.HexColor(KLINIKKA)); c.setFont("Courier-Bold", 11)
    c.drawString(24 * mm, ph - 40 * mm, "TYÖVAATTEET · PAINATUS JA BRODEERAUS")
    c.setFillColor(colors.HexColor(PETROLI)); c.setFont("Helvetica-Bold", 38)
    c.drawString(24 * mm, ph - 62 * mm, "Työvaatteiden")
    c.drawString(24 * mm, ph - 78 * mm, "painatusohje")
    _tekstit(c, 24 * mm, ph - 100 * mm, [
        "Merkkiversiot, sijoitukset ja koot toimittajalle tarjousta ja tuotantoa varten.",
        "",
        "**Periaate: vaatteissa vain UAP-merkki — ei yrityksen nimeä eikä muuta tekstiä.**",
        "",
        "Tuotteet:",
        "  • T-paita, EN ISO 20471 huomioväri (työmaa)",
        "  • Musta puuvillainen T-paita (toimisto, ei työmaakäyttöön)",
        "  • Huppari / fleece (väliasu, ei huomioväri)",
        "  • Talvitakki, EN ISO 20471 huomioväri",
        "  • Pipo ja lippis (brodeeraus) · tarramerkit",
    ], 11, 16)
    c.setFont("Helvetica", 9); c.setFillColor(colors.HexColor("#4A5A5F"))
    c.drawString(24 * mm, 14 * mm, "Tilaaja: Uudenmaan Asbestipurku Oy · Y-tunnus 2817254-1 · info@uudenmaanasbestipurku.fi")
    c.showPage()

    # 2. Merkkiversiot
    _otsikko(c, "Merkkiversiot ja tiedostot", "Kaikki tiedostot vektoreina (PDF ja SVG), kirjaimet polkuina — fonttia ei tarvita")
    kortit = [("vari", None), ("petroli", None), ("valkoinen", PETROLI), ("negatiivi", PETROLI),
              ("brodeeraus-vari", None), ("brodeeraus-valkoinen", PETROLI)]
    for i, (nimi, tausta) in enumerate(kortit):
        kx = 22 * mm + (i % 3) * 88 * mm; ky = ph - 100 * mm - (i // 3) * 72 * mm
        c.setFillColor(colors.HexColor(tausta or "#FFFFFF")); c.setStrokeColor(colors.HexColor("#C9D6D4"))
        c.roundRect(kx, ky, 80 * mm, 52 * mm, 3 * mm, stroke=1, fill=1)
        brod = nimi.startswith("brodeeraus")
        perus = nimi.replace("brodeeraus-", "")
        kv = VERSIOT[perus][:3]
        merkki(c, kx + 6 * mm, ky + 8 * mm, 36 * mm, kehys=kv[0], kirjain=kv[1], pylvas=kv[2], brodeeraus=brod)
        tv = "#FFFFFF" if tausta else PETROLI
        kuvaus = VERSIOT[perus][4] if not brod else "Pipot, lippikset ja brodeeratut rintamerkit"
        _tekstit(c, kx + 46 * mm, ky + 40 * mm, [f"**{'Brodeeraus, ' if brod else ''}{perus}**"], 9, 11,
                 leveys=31 * mm, vari=tv)
        _tekstit(c, kx + 46 * mm, ky + 32 * mm, [kuvaus.replace(": ", " – ")], 7.5, 9.5, leveys=31 * mm, vari=tv)
        c.setFillColor(colors.HexColor(tv)); c.setFont("Courier", 5.6)
        tiedosto = f"uap-merkki-{nimi}"
        c.drawString(kx + 46 * mm, ky + 10 * mm, tiedosto[:26])
        c.drawString(kx + 46 * mm, ky + 7 * mm, (tiedosto[26:] + ".pdf / .svg") if len(tiedosto) > 26 else ".pdf / .svg")
    c.showPage()

    # 3–6. Vaatteet
    huomio_ohje = ["**EN ISO 20471 — tärkeää toimittajalle:** Painatus ei saa pienentää fluoresoivan "
                   "pohjamateriaalin tai heijastinmateriaalin pinta-alaa alle vaatteen luokan vähimmäismäärän. "
                   "Ei painatusta heijastinraitojen päälle. Toimittaja vahvistaa, että vaate säilyttää "
                   "sertifioinnin painatuksen jälkeen."]
    _vaatesivu(c, "T-paita · EN ISO 20471 huomioväri", "Työmaa · keltainen tai oranssi",
               TPAITA, HV_KELTAINEN, [70, 40], (8, "rinta"), (20, "selkä"),
               dict(kehys=PETROLI, kirjain=PETROLI, pylvas=PETROLI),
               ["**Merkki:** petroli, yksivärinen", "**Tiedosto:** uap-merkki-petroli.pdf",
                "**Etu:** vasen rinta, leveys 8 cm", "**Selkä:** yläselkä, leveys 20 cm",
                "  (heijastinraitojen yläpuolelle)", "**Menetelmä:** siirtopaino", "",
                "Oranssi pohja: sama petroliversio.", ""] + huomio_ohje)
    c.showPage()
    _vaatesivu(c, "Musta puuvillainen T-paita", "Toimisto · ei työmaakäyttöön",
               TPAITA, "#1B1D1F", None, (8, "rinta"), None,
               dict(kehys=LUONNONVALKO, kirjain=LUONNONVALKO, pylvas=KLINIKKA_V),
               ["**Merkki:** negatiivi (vaalea + klinikka)", "  tai valkoinen yksivärinen",
                "**Tiedosto:** uap-merkki-negatiivi.pdf /", "  uap-merkki-valkoinen.pdf",
                "**Etu:** vasen rinta, leveys 8 cm", "**Selkä:** ei merkkiä (siisti toimistoasu)",
                "**Menetelmä:** siirto- tai silkkipaino", "  tai brodeeraus (brodeerausversio)"])
    c.showPage()
    _vaatesivu(c, "Huppari / fleece", "Väliasu · ei huomioväri · suositus petroli tai musta",
               HUPPARI, "#1E2E35", None, (8, "rinta"), (24, "selkä"),
               dict(kehys=LUONNONVALKO, kirjain=LUONNONVALKO, pylvas=KLINIKKA_V, brodeeraus=True),
               ["**Etu:** brodeeraus, vasen rinta 8 cm", "**Tiedosto:** uap-merkki-brodeeraus-", "  negatiivi.pdf (tai -valkoinen)",
                "**Selkä (valinnainen):** paino 24 cm,", "  uap-merkki-negatiivi.pdf",
                "**Fleece:** vain brodeeraus — paino", "  ei tartu hyvin nukkapintaan",
                "**Vaatteen väri:** petroli (lähellä", "  #14232A), tummanharmaa tai musta"])
    c.showPage()
    _vaatesivu(c, "Talvitakki · EN ISO 20471 huomioväri", "Työmaa · keltainen tai oranssi",
               TAKKI, HV_KELTAINEN, [72, 40], (9, "rinta"), (22, "selkä"),
               dict(kehys=PETROLI, kirjain=PETROLI, pylvas=PETROLI),
               ["**Merkki:** petroli, yksivärinen", "**Etu:** vasen rinta 9 cm, brodeeraus",
                "  (uap-merkki-brodeeraus-petroli.pdf)", "  tai siirtopaino (uap-merkki-petroli.pdf)",
                "**Selkä:** yläselkä 22 cm, siirtopaino,", "  heijastinraitojen yläpuolelle",
                "", "Monissa takeissa on irrotettava", "selkälappu tai valmis painoalue —",
                "käytä sitä, jos on.", ""] + huomio_ohje)
    c.showPage()

    # 7. Pipo, lippis, tarrat
    _otsikko(c, "Pipo, lippis ja tarramerkit", "Brodeerausversio pieniin kokoihin · tarrat leikkuuviivalla")
    # Lippis
    bx, by = 30 * mm, 70 * mm
    c.setFillColor(colors.HexColor("#1E2E35")); c.setStrokeColor(colors.HexColor("#5C6469"))
    c.ellipse(bx + 20 * mm, by - 6 * mm, bx + 110 * mm, by + 6 * mm, stroke=1, fill=1)
    c.wedge(bx, by - 40 * mm, bx + 70 * mm, by + 40 * mm, 0, 180, stroke=1, fill=1)
    merkki(c, bx + 26 * mm, by + 8 * mm, 18 * mm, kehys=LUONNONVALKO, kirjain=LUONNONVALKO,
           pylvas=KLINIKKA_V, brodeeraus=True)
    _mitta(c, bx + 26 * mm, by + 29 * mm, bx + 44 * mm, by + 29 * mm, "5 cm")
    # Pipo
    px, py = 135 * mm, 64 * mm
    c.setFillColor(colors.HexColor("#1B1D1F"))
    c.wedge(px, py - 8 * mm, px + 60 * mm, py + 56 * mm, 0, 180, stroke=1, fill=1)
    c.setFillColor(colors.HexColor("#25282B")); c.rect(px, py, 60 * mm, 24 * mm, stroke=1, fill=1)
    merkki(c, px + 21.5 * mm, py + 3.5 * mm, 17 * mm, kehys=LUONNONVALKO, kirjain=LUONNONVALKO,
           pylvas=KLINIKKA_V, brodeeraus=True)
    _mitta(c, px + 21.5 * mm, py + 27 * mm, px + 38.5 * mm, py + 27 * mm, "4,5 cm")
    # Tarra
    tx, ty = 215 * mm, 72 * mm
    c.setFillColor(colors.HexColor(LUONNONVALKO)); c.roundRect(tx, ty, 46 * mm, 46 * mm, 5 * mm, stroke=0, fill=1)
    merkki(c, tx + 3 * mm, ty + 3 * mm, 40 * mm)
    c.setStrokeColor(colors.HexColor("#E0218A")); c.setDash(2, 2); c.setLineWidth(0.6)
    c.roundRect(tx, ty, 46 * mm, 46 * mm, 5 * mm, stroke=1, fill=0); c.setDash()
    for x0, otsikko, rivit in (
        (30 * mm, "Lippis", ["Brodeeraus etupaneeliin, leveys 5 cm", "uap-merkki-brodeeraus-negatiivi.pdf",
                             "Vaalea lippis: -brodeeraus-vari.pdf"]),
        (135 * mm, "Pipo", ["Brodeeraus käänteeseen, leveys 4,5 cm", "uap-merkki-brodeeraus-negatiivi.pdf",
                            "Huom. neulos: tukikangas brodeeraukseen"]),
        (215 * mm, "Tarramerkki", ["uap-tarra-50mm.pdf / uap-tarra-80mm.pdf", "Leikkuuviiva spot-väri CutContour",
                                   "Pohja luonnonvalko, 3 mm reunus"])):
        _tekstit(c, x0, 52 * mm, [f"**{otsikko}**"] + rivit, 9, 12)
    _tekstit(c, 30 * mm, 24 * mm, ["**Brodeeraus:** pienin suositeltu leveys 3,5 cm. Brodeerausversiossa kehys on kaksinkertainen ja "
                                   "kirjaimet ja pylväät vahvemmat, jotta ne erottuvat langalla."], 9, 12)
    c.showPage()

    # 8. Värit ja säännöt
    _otsikko(c, "Värit ja käyttösäännöt", "Värit vahvistetaan toimittajan lanka- ja värikartasta ennen tuotantoa")
    varit = [("Syväpetroli", PETROLI, "Kehys ja kirjaimet"), ("Klinikka", KLINIKKA, "Pylväät vaalealla"),
             ("Vaalea klinikka", KLINIKKA_V, "Pylväät tummalla"), ("Luonnonvalko", LUONNONVALKO, "Merkki tummalla")]
    for i, (nimi, hx, kaytto) in enumerate(varit):
        vx = 22 * mm + i * 64 * mm; vy = ph - 85 * mm
        c.setFillColor(colors.HexColor(hx)); c.setStrokeColor(colors.HexColor("#C9D6D4"))
        c.roundRect(vx, vy, 56 * mm, 30 * mm, 3 * mm, stroke=1, fill=1)
        r, g, b = (int(hx[k:k + 2], 16) for k in (1, 3, 5))
        _tekstit(c, vx, vy - 6 * mm, [f"**{nimi}**", f"HEX {hx}   RGB {r} {g} {b}", kaytto], 9, 12)
    _tekstit(c, 22 * mm, ph - 125 * mm, [
        "**Säännöt**",
        "• Vaatteissa vain UAP-merkki. Ei yrityksen nimeä, ei sanaa \"asbesti\", ei iskulausetta.",
        "• Suoja-alue merkin ympärillä vähintään ¼ merkin leveydestä — ei muita painatuksia tällä alueella.",
        "• Pienin koko: paino 2,4 cm, brodeeraus 3,5 cm. Ei venytystä, kallistusta, varjoja eikä liukuvärejä.",
        "• Kehystä ei täytetä värillä. Pylväiden järjestys ja korkeussuhteet pysyvät aina samoina.",
        "• Värit: valitse lähin sävy toimittajan lanka- tai painokartasta ja lähetä mallikappale hyväksyttäväksi.",
        "• Huomiovaatteet: painatus ei saa vaarantaa EN ISO 20471 -luokitusta (ks. vaatesivut).",
    ], 10, 15)
    c.showPage()
    c.save()


def main():
    ULOS.mkdir(exist_ok=True)
    for nimi, (kehys, kirjain, pylvas, _, _) in VERSIOT.items():
        _yksi(f"uap-merkki-{nimi}.pdf", 60, kehys=kehys, kirjain=kirjain, pylvas=pylvas)
    for nimi, (kehys, kirjain, pylvas) in {"vari": (PETROLI, PETROLI, KLINIKKA),
                                           "petroli": (PETROLI, PETROLI, PETROLI),
                                           "valkoinen": ("#FFFFFF", "#FFFFFF", "#FFFFFF"),
                                           "negatiivi": (LUONNONVALKO, LUONNONVALKO, KLINIKKA_V)}.items():
        _yksi(f"uap-merkki-brodeeraus-{nimi}.pdf", 60, brodeeraus=True, kehys=kehys, kirjain=kirjain, pylvas=pylvas)
        _brodeeraus_svg(f"uap-merkki-brodeeraus-{nimi}.svg", kehys, kirjain, pylvas)
    _tarra("uap-tarra-50mm.pdf", 44)
    _tarra("uap-tarra-80mm.pdf", 74)
    painatusohje()
    print("Valmis:", sorted(p.name for p in ULOS.iterdir()))


if __name__ == "__main__":
    main()
