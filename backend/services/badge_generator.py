"""
ESG Optimizer MVP — Générateur de badge social partageable.
Produit une image PNG 1200x630 (format Open Graph optimal pour LinkedIn/Twitter).

Contenu du badge :
  - Logo ESG Optimizer (texte)
  - Score global en très grand
  - Nom de l'entreprise
  - Année du rapport
  - Badge "CSRD Ready" ou "Non conforme"
  - URL esg-optimizer.fr
"""

import io
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont


# Couleurs
BG_COLOR = (249, 250, 251)          # #F9FAFB — gris très clair
BRAND_GREEN = (26, 61, 34)           # #1A3D22 (Forest)
BRAND_DARK = (17, 24, 39)           # #111827
BRAND_GRAY = (107, 114, 128)        # #6B7280
BRAND_LIGHT_GRAY = (229, 231, 235)  # #E5E7EB
WHITE = (255, 255, 255)
RED = (220, 38, 38)                 # #DC2626
AMBER = (245, 158, 11)              # #F59E0B

# Tailles de police (Pillow utilise les fonts système)
# On utilise des fonts par défaut car les polices custom ne sont pas dispo partout


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Charge une police truetype ou fallback sur la police par défaut."""
    # Essayer plusieurs chemins de polices communs
    font_paths = [
        # Linux (Railway, Docker)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        # Windows
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    # Fallback ultime
    return ImageFont.load_default()


def _score_color(score: float) -> tuple:
    """Retourne la couleur RGB selon le score."""
    if score >= 60:
        return BRAND_GREEN
    elif score >= 40:
        return AMBER
    return RED


def generate_badge(
    company_name: str,
    score_global: float,
    csrd_ready: bool,
    report_year: int | None = None,
    analysis_date: datetime | None = None,
    app_url: str = "esg-optimizer.fr",
) -> bytes:
    """
    Génère un badge PNG 1200x630 pour le partage social.

    Returns:
        Contenu binaire PNG.
    """
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Bordure supérieure verte
    draw.rectangle([(0, 0), (W, 6)], fill=BRAND_GREEN)

    # Logo ESG Optimizer (texte)
    font_logo = _get_font(24, bold=True)
    draw.text((50, 30), "ESG Optimizer", fill=BRAND_GREEN, font=font_logo)

    font_logo_sub = _get_font(14)
    draw.text((50, 60), "Analyse ESG automatisée par IA", fill=BRAND_GRAY, font=font_logo_sub)

    # Nom de l'entreprise
    font_company = _get_font(32, bold=True)
    # Tronquer si trop long
    display_name = company_name if len(company_name) <= 40 else company_name[:37] + "..."
    draw.text((50, 120), display_name, fill=BRAND_DARK, font=font_company)

    # Année
    if report_year:
        font_year = _get_font(20)
        draw.text((50, 165), f"Rapport {report_year}", fill=BRAND_GRAY, font=font_year)

    # Score global en GRAND
    score_int = int(round(score_global))
    color = _score_color(score_global)

    # Cercle de fond pour le score
    cx, cy = 600, 350
    radius = 130
    draw.ellipse(
        [(cx - radius, cy - radius), (cx + radius, cy + radius)],
        fill=WHITE,
        outline=color,
        width=8,
    )

    # Score au centre
    font_score = _get_font(90, bold=True)
    score_text = str(score_int)
    bbox = draw.textbbox((0, 0), score_text, font=font_score)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 15), score_text, fill=color, font=font_score)

    # "/100" sous le score
    font_100 = _get_font(24)
    bbox_100 = draw.textbbox((0, 0), "/100", font=font_100)
    tw_100 = bbox_100[2] - bbox_100[0]
    draw.text((cx - tw_100 // 2, cy + 55), "/100", fill=BRAND_GRAY, font=font_100)

    # Label "Score ESG Global"
    font_label = _get_font(18)
    label = "Score ESG Global"
    bbox_l = draw.textbbox((0, 0), label, font=font_label)
    tw_l = bbox_l[2] - bbox_l[0]
    draw.text((cx - tw_l // 2, cy + 90), label, fill=BRAND_GRAY, font=font_label)

    # Jauge graphique à gauche (barres E/S/G)
    bar_x = 100
    bar_w = 300
    bar_h = 28
    bars = [
        ("Environnement", BRAND_GREEN, score_global * 0.95),  # Approximation visuelle
        ("Social", (37, 99, 235), score_global * 0.88),
        ("Gouvernance", (124, 58, 237), score_global * 0.82),
    ]
    for i, (label_text, bar_color, val) in enumerate(bars):
        y = 260 + i * 60
        # Fond de la barre
        draw.rounded_rectangle(
            [(bar_x, y), (bar_x + bar_w, y + bar_h)],
            radius=6,
            fill=BRAND_LIGHT_GRAY,
        )
        # Remplissage
        fill_w = max(int(bar_w * min(val, 100) / 100), 12)
        draw.rounded_rectangle(
            [(bar_x, y), (bar_x + fill_w, y + bar_h)],
            radius=6,
            fill=bar_color,
        )
        # Label
        font_bar = _get_font(14)
        draw.text((bar_x, y - 18), label_text, fill=BRAND_DARK, font=font_bar)

    # Badge CSRD
    badge_x = 900
    badge_y = 250
    if csrd_ready:
        draw.rounded_rectangle(
            [(badge_x, badge_y), (badge_x + 220, badge_y + 50)],
            radius=12,
            fill=(209, 250, 229),  # vert clair
        )
        font_badge = _get_font(18, bold=True)
        draw.text((badge_x + 20, badge_y + 12), "CSRD Ready  ✓", fill=(5, 150, 105), font=font_badge)
    else:
        draw.rounded_rectangle(
            [(badge_x, badge_y), (badge_x + 220, badge_y + 50)],
            radius=12,
            fill=(254, 226, 226),  # rouge clair
        )
        font_badge = _get_font(18, bold=True)
        draw.text((badge_x + 15, badge_y + 12), "Non conforme  ✗", fill=RED, font=font_badge)

    # Date de l'analyse
    date_str = (analysis_date or datetime.now()).strftime("%d/%m/%Y")
    font_date = _get_font(14)
    draw.text((badge_x + 20, badge_y + 65), f"Analyse du {date_str}", fill=BRAND_GRAY, font=font_date)

    # Footer avec URL
    draw.rectangle([(0, H - 50), (W, H)], fill=WHITE)
    draw.line([(0, H - 50), (W, H - 50)], fill=BRAND_LIGHT_GRAY, width=1)

    font_url = _get_font(16, bold=True)
    draw.text((50, H - 35), app_url, fill=BRAND_GREEN, font=font_url)

    font_cta = _get_font(14)
    cta = "Analysez votre rapport ESG gratuitement →"
    bbox_cta = draw.textbbox((0, 0), cta, font=font_cta)
    tw_cta = bbox_cta[2] - bbox_cta[0]
    draw.text((W - tw_cta - 50, H - 33), cta, fill=BRAND_GRAY, font=font_cta)

    # Export PNG
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()
