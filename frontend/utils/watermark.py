"""
ESG Optimizer — Module watermark PDF pour le plan Découverte.
Applique un bandeau diagonal semi-transparent "ESG Optimizer — Rapport partiel"
sur chaque page d'un PDF généré par ReportLab.

Usage dans reporter.py :
    from frontend.utils.watermark import apply_watermark_to_pdf
    apply_watermark_to_pdf("rapport_brut.pdf", "rapport_watermarked.pdf")

Ou avec PyPDF (merge pages) :
    from frontend.utils.watermark import build_watermark_page
    # renvoie un BytesIO contenant une page PDF watermark-only
    wm = build_watermark_page(width=595, height=842)
"""

import io
import math
from typing import Optional


def build_watermark_page(
    width: float = 595,
    height: float = 842,
    text: str = "ESG Optimizer — Rapport partiel",
    color_hex: str = "#1A3D22",
    opacity: float = 0.12,
    font_size: float = 32,
    repeat: int = 4,
) -> io.BytesIO:
    """
    Génère une page PDF transparente avec le texte watermark en diagonal.

    Args:
        width:     Largeur de la page en points (595 = A4)
        height:    Hauteur de la page en points (842 = A4)
        text:      Texte à afficher
        color_hex: Couleur Forest brand (#1A3D22)
        opacity:   Opacité du texte (0–1). 0.12 = visible mais discret
        font_size: Taille de la police en points
        repeat:    Nombre de fois où le texte est répété verticalement

    Returns:
        BytesIO contenant la page PDF watermark.
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor
    except ImportError:
        raise ImportError(
            "reportlab est requis pour générer les watermarks. "
            "Installe-le avec : pip install reportlab"
        )

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))

    # Couleur brand avec opacité
    r, g, b = _hex_to_rgb(color_hex)
    c.setFillColorRGB(r, g, b, alpha=opacity)
    c.setStrokeColorRGB(r, g, b, alpha=opacity * 0.5)

    # Angle diagonal (45°)
    angle = 35
    angle_rad = math.radians(angle)

    c.saveState()
    c.setFont("Helvetica-Bold", font_size)

    # Répétition verticale du watermark
    step = height / (repeat + 1)
    for i in range(1, repeat + 1):
        y = step * i
        x = width / 2
        c.saveState()
        c.translate(x, y)
        c.rotate(angle)
        c.drawCentredString(0, 0, text)
        c.restoreState()

    c.restoreState()
    c.save()
    buf.seek(0)
    return buf


def apply_watermark_to_pdf(
    input_path: str,
    output_path: str,
    text: str = "ESG Optimizer — Rapport partiel",
    max_pages: Optional[int] = None,
) -> None:
    """
    Applique le watermark sur toutes les pages d'un PDF existant.

    Args:
        input_path:  Chemin du PDF source (rapport complet)
        output_path: Chemin de sortie (rapport watermarké)
        text:        Texte du watermark
        max_pages:   Si fourni, tronque le PDF à ce nombre de pages
                     (utile pour le plan Découverte = 3 pages sur 8)
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        raise ImportError(
            "pypdf est requis. Installe-le avec : pip install pypdf"
        )

    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Déterminer le nombre de pages à conserver
    n_pages = len(reader.pages)
    if max_pages is not None:
        n_pages = min(n_pages, max_pages)

    # Générer une page watermark aux dimensions de la première page
    first_page = reader.pages[0]
    page_width  = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)

    wm_buf = build_watermark_page(
        width=page_width,
        height=page_height,
        text=text,
    )
    wm_reader = PdfReader(wm_buf)
    wm_page = wm_reader.pages[0]

    for i in range(n_pages):
        page = reader.pages[i]
        page.merge_page(wm_page)
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)


def apply_watermark_to_bytes(
    pdf_bytes: bytes,
    text: str = "ESG Optimizer — Rapport partiel",
    max_pages: Optional[int] = None,
) -> bytes:
    """
    Version in-memory : prend des bytes PDF en entrée, retourne des bytes watermarkés.
    Utilisé directement dans reporter.py pour éviter les I/O fichiers.

    Args:
        pdf_bytes: Contenu du PDF source
        text:      Texte du watermark
        max_pages: Tronquer à N pages (plan Découverte = 3)

    Returns:
        bytes du PDF watermarké
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        raise ImportError("pypdf est requis. pip install pypdf")

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    n_pages = len(reader.pages)
    if max_pages is not None:
        n_pages = min(n_pages, max_pages)

    first_page = reader.pages[0]
    page_width  = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)

    wm_buf = build_watermark_page(
        width=page_width,
        height=page_height,
        text=text,
        opacity=0.13,
    )
    wm_reader = PdfReader(wm_buf)
    wm_page = wm_reader.pages[0]

    for i in range(n_pages):
        page = reader.pages[i]
        page.merge_page(wm_page)
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


# Helpers

def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """Convertit #RRGGBB en tuple (r, g, b) normalisé 0–1."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return r, g, b
