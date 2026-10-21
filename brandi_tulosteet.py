"""
UAP-brändi tulosteisiin (PDF/reportlab ja Excel/openpyxl) — ei Streamlit-riippuvuutta.

Logo ja säännöt: brand/LOGO-OHJE.md · värit: brand/BRANDIKIRJA.md.
Merkki + nimi: nimi oikealle, väli ¼ merkin leveydestä, "Oy" kevyempänä harmaana.
"""

from pathlib import Path

_BRAND = Path(__file__).parent / "brand" / "png"
MERKKI_VARI = _BRAND / "uap-merkki-vari-512.png"            # vaalealle pohjalle
MERKKI_NEGATIIVI = _BRAND / "uap-merkki-negatiivi-512.png"  # tummalle pohjalle

# Paletti (hex ilman #, openpyxl-muoto)
PETROLI = "14232A"
KLINIKKA = "1F7A73"
HUURRE = "DDEAE8"
HUURRE_TUMMA = "C9DEDA"
LUONNONVALKO = "F2F4F4"
OY_HARMAA = "7A888B"


def pdf_logo(c, x: float, y: float, koko: float, nimi: bool = True,
             fontti: str = "Helvetica-Bold", fontti_kevyt: str = "Helvetica"):
    """Piirtää merkin (vasen alakulma x, y; sivu = koko pistettä) ja nimen sen oikealle puolelle."""
    from reportlab.lib import colors
    if not MERKKI_VARI.exists():
        return
    c.saveState()
    c.drawImage(str(MERKKI_VARI), x, y, width=koko, height=koko, mask="auto")
    if nimi:
        fs = koko * 0.6 / 2.1               # kaksi riviä ≈ 60 % merkin korkeudesta
        xn = x + koko * 1.25
        y1 = y + koko / 2 + fs * 0.15
        y2 = y1 - fs * 1.05
        c.setFillColor(colors.HexColor("#" + PETROLI))
        c.setFont(fontti, fs)
        c.drawString(xn, y1, "Uudenmaan")
        c.drawString(xn, y2, "Asbestipurku")
        c.setFillColor(colors.HexColor("#" + OY_HARMAA))
        c.setFont(fontti_kevyt, fs)
        c.drawString(xn + c.stringWidth("Asbestipurku ", fontti, fs), y2, "Oy")
    c.restoreState()


def excel_logo(ws, solu: str, korkeus_px: int = 30, tumma_pohja: bool = True):
    """Lisää merkin Excel-taulukkoon (esim. otsikkopalkin oikeaan reunaan)."""
    polku = MERKKI_NEGATIIVI if tumma_pohja else MERKKI_VARI
    try:
        from openpyxl.drawing.image import Image as XLImage
        img = XLImage(str(polku))
        img.width = img.height = korkeus_px
        ws.add_image(img, solu)
    except Exception:
        pass   # logo on koriste — ei saa kaataa raporttia
