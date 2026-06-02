"""
Tulostuspohja konetarroille — A4-arkki pieniä QR-tarroja.
Jokainen tarra: QR-koodi + laitetunnus + laitenimi.
"""

import io
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


# Tarrakoot (leveys × korkeus mm) — valittavissa
TARRAKOOT = {
    "Pieni (38×24 mm, 65/arkki)":   {"w": 38, "h": 24, "cols": 5, "rows": 11, "qr": 18},
    "Keskikoko (51×34 mm, 40/arkki)": {"w": 51, "h": 34, "cols": 4, "rows": 8, "qr": 26},
    "Iso kone (70×50 mm, 12/arkki)":  {"w": 70, "h": 50, "cols": 2, "rows": 4, "qr": 38},
}


def _qr_image(url: str) -> ImageReader:
    qr = qrcode.QRCode(version=1, box_size=10, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def luo_tarra_pdf(laitteet: list, app_url: str, koko_avain: str,
                  yritys: str = "Uudenmaan Asbestipurku Oy") -> bytes:
    """
    laitteet: list[dict] joissa 'nro' ja 'laite'
    app_url:  esim. https://kalusto-uap.streamlit.app
    koko_avain: avain TARRAKOOT-sanakirjasta
    """
    koko = TARRAKOOT.get(koko_avain, list(TARRAKOOT.values())[1])
    lw, lh = koko["w"] * mm, koko["h"] * mm
    cols, rows = koko["cols"], koko["rows"]
    qr_size = koko["qr"] * mm

    page_w, page_h = A4
    per_page = cols * rows

    # Lasketaan marginaalit niin että ruudukko keskittyy
    grid_w = cols * lw
    grid_h = rows * lh
    margin_x = (page_w - grid_w) / 2
    margin_y = (page_h - grid_h) / 2

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    for i, laite in enumerate(laitteet):
        sivu_idx = i % per_page
        if i > 0 and sivu_idx == 0:
            c.showPage()

        rivi = sivu_idx // cols
        sar  = sivu_idx % cols

        x = margin_x + sar * lw
        # ylhäältä alas
        y = page_h - margin_y - (rivi + 1) * lh

        # Tarran reunaviiva (leikkausapu)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.3)
        c.rect(x, y, lw, lh)

        nro   = laite.get("nro", "")
        nimi  = laite.get("laite", "")
        url   = f"{app_url}/?kalusto={nro}"

        # QR vasemmalle
        qr_img = _qr_image(url)
        qr_x = x + 1.5 * mm
        qr_y = y + (lh - qr_size) / 2
        c.drawImage(qr_img, qr_x, qr_y, qr_size, qr_size)

        # Teksti oikealle
        teksti_x = qr_x + qr_size + 2 * mm
        teksti_w = lw - (qr_size + 5 * mm)

        # Laitetunnus — iso ja lihava
        tunnus_koko = min(16, max(9, int(lh / mm / 2.2)))
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", tunnus_koko)
        c.drawString(teksti_x, y + lh - (tunnus_koko + 4), nro)

        # Laitenimi — pienempi, katkaistaan tarvittaessa
        nimi_koko = min(8, max(5, int(lh / mm / 4)))
        c.setFont("Helvetica", nimi_koko)
        max_merkit = int(teksti_w / (nimi_koko * 0.5 * mm)) if teksti_w > 0 else 18
        nimi_lyh = nimi if len(nimi) <= max_merkit else nimi[:max_merkit-1] + "…"
        c.drawString(teksti_x, y + lh - (tunnus_koko + nimi_koko + 8), nimi_lyh)

        # Yritys alareunaan pienellä
        if koko["h"] >= 34:
            c.setFont("Helvetica", 4.5)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawString(teksti_x, y + 2 * mm, yritys)

    c.showPage()
    c.save()
    return buf.getvalue()
