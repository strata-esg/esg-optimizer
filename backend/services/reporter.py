"""
ESG Optimizer MVP - Service de génération de rapports PDF.
Utilise ReportLab pour produire :
  - Rapport d'analyse ESG complet (≥ 8 pages, logo en header)
  - Rapport Preview (3 pages, watermark PRÉVISUALISATION) - Plan Découverte
  - Rapport Delta (comparaison N vs N-1)
"""

import io
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.models import Analysis, Company
from backend.utils import safe_json_loads as _safe_json_loads

logger = logging.getLogger(__name__)

# --- Couleurs ESG Optimizer --------------------------------------------------
BRAND_GREEN = colors.HexColor("#16A34A")
BRAND_DARK = colors.HexColor("#1E293B")
BRAND_LIGHT = colors.HexColor("#F1F5F9")
BRAND_BLUE = colors.HexColor("#2563EB")
BRAND_ORANGE = colors.HexColor("#EA580C")
BRAND_RED = colors.HexColor("#DC2626")
BRAND_GRAY = colors.HexColor("#94A3B8")
BRAND_CREAM = colors.HexColor("#F5F2EC")

PILLAR_COLORS = {
    "E": colors.HexColor("#16A34A"),
    "S": colors.HexColor("#2563EB"),
    "G": colors.HexColor("#7C3AED"),
}

# FIX #13 : Chemin logo pour le header PDF
_LOGO_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "frontend" / "static" / "web-app-manifest-192x192.png"
)


# --- Styles ------------------------------------------------------------------

def _get_styles() -> dict:
    """Retourne un dict de styles personnalisés."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CustomTitle",
            parent=base["Title"],
            fontSize=26,
            textColor=BRAND_DARK,
            spaceAfter=6 * mm,
            spaceBefore=4 * mm,
            alignment=TA_CENTER,
            leading=32,
        ),
        "subtitle": ParagraphStyle(
            "CustomSubtitle",
            parent=base["Normal"],
            fontSize=12,
            textColor=BRAND_GRAY,
            alignment=TA_CENTER,
            spaceAfter=8 * mm,
            leading=16,
        ),
        "h1": ParagraphStyle(
            "CustomH1",
            parent=base["Heading1"],
            fontSize=16,
            textColor=BRAND_GREEN,
            spaceBefore=10 * mm,
            spaceAfter=5 * mm,
            leading=20,
            borderPad=2,
        ),
        "h2": ParagraphStyle(
            "CustomH2",
            parent=base["Heading2"],
            fontSize=13,
            textColor=BRAND_DARK,
            spaceBefore=6 * mm,
            spaceAfter=3 * mm,
            leading=17,
        ),
        "body": ParagraphStyle(
            "CustomBody",
            parent=base["Normal"],
            fontSize=10,
            textColor=BRAND_DARK,
            alignment=TA_JUSTIFY,
            spaceAfter=4 * mm,
            leading=15,
        ),
        "body_left": ParagraphStyle(
            "CustomBodyLeft",
            parent=base["Normal"],
            fontSize=10,
            textColor=BRAND_DARK,
            alignment=TA_LEFT,
            spaceAfter=3 * mm,
            leading=15,
        ),
        "small": ParagraphStyle(
            "CustomSmall",
            parent=base["Normal"],
            fontSize=8,
            textColor=BRAND_GRAY,
            leading=11,
            wordWrap="CJK",
        ),
        "small_dark": ParagraphStyle(
            "CustomSmallDark",
            parent=base["Normal"],
            fontSize=8,
            textColor=BRAND_DARK,
            leading=11,
            wordWrap="CJK",
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            leading=12,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontSize=8,
            textColor=BRAND_DARK,
            leading=11,
            wordWrap="CJK",
        ),
        "score_big": ParagraphStyle(
            "ScoreBig",
            parent=base["Normal"],
            fontSize=28,
            textColor=BRAND_GREEN,
            alignment=TA_CENTER,
            leading=32,
        ),
        "callout": ParagraphStyle(
            "Callout",
            parent=base["Normal"],
            fontSize=10,
            textColor=BRAND_DARK,
            backColor=BRAND_CREAM,
            alignment=TA_JUSTIFY,
            spaceAfter=5 * mm,
            spaceBefore=3 * mm,
            leading=15,
            leftIndent=10,
            rightIndent=10,
            borderPad=6,
        ),
        "preview_banner": ParagraphStyle(
            "PreviewBanner",
            parent=base["Normal"],
            fontSize=11,
            textColor=colors.white,
            backColor=BRAND_ORANGE,
            alignment=TA_CENTER,
            spaceAfter=6 * mm,
            leading=16,
            borderPad=6,
        ),
    }


# --- Utilitaires -------------------------------------------------------------

def _score_color(score: float | None) -> colors.HexColor:
    if score is None:
        return BRAND_GRAY
    if score >= 80:
        return BRAND_GREEN
    if score >= 60:
        return BRAND_BLUE
    if score >= 40:
        return BRAND_ORANGE
    return BRAND_RED


def _score_level(score: float | None) -> str:
    if score is None:
        return "N/A"
    if score >= 80:
        return "Mature"
    if score >= 60:
        return "Avancé"
    if score >= 40:
        return "Basique"
    if score >= 20:
        return "Embryonnaire"
    return "Quasi absent"


def _trend_symbol(delta: float | None) -> str:
    if delta is None:
        return "-"
    if delta >= 15:
        return "++ Forte hausse"
    if delta >= 5:
        return "+ Hausse"
    if delta > -5:
        return "= Stable"
    if delta > -15:
        return "- Baisse"
    return "-- Forte baisse"


def _p(text: str, style) -> Paragraph:
    """Raccourci sécurisé pour créer un Paragraph (échappe None)."""
    return Paragraph(str(text) if text is not None else "-", style)


# --- Header/Footer callbacks -------------------------------------------------

def _make_footer(show_logo: bool = True):
    """Fabrique la fonction de pied de page avec logo optionnel."""
    def _footer(canvas, doc):
        canvas.saveState()
        # Logo en haut à gauche (FIX #13)
        if show_logo and _LOGO_PATH.exists():
            try:
                canvas.drawImage(
                    str(_LOGO_PATH),
                    x=2 * cm,
                    y=A4[1] - 1.8 * cm,
                    width=1.2 * cm,
                    height=1.2 * cm,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                pass  # Logo non critique
        # Titre dans le header
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(BRAND_GREEN)
        canvas.drawString(3.8 * cm, A4[1] - 1.3 * cm, "ESG Optimizer AI")
        # Ligne de séparation header
        canvas.setStrokeColor(BRAND_LIGHT)
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, A4[1] - 2 * cm, A4[0] - 2 * cm, A4[1] - 2 * cm)
        # Pied de page
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(BRAND_GRAY)
        canvas.drawString(2 * cm, 1.2 * cm, "ESG Optimizer AI - Rapport généré automatiquement - Confidentiel")
        canvas.drawRightString(
            A4[0] - 2 * cm, 1.2 * cm,
            f"Page {doc.page} - {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}"
        )
        # Ligne de séparation footer
        canvas.line(2 * cm, 1.8 * cm, A4[0] - 2 * cm, 1.8 * cm)
        canvas.restoreState()

    return _footer


def _make_preview_footer():
    """Footer pour le rapport preview : ajoute watermark PRÉVISUALISATION."""
    def _footer(canvas, doc):
        # D'abord footer standard
        _make_footer(show_logo=True)(canvas, doc)
        # Watermark diagonal (FIX #12)
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 72)
        canvas.setFillColor(colors.Color(0.85, 0.85, 0.85, alpha=0.25))
        canvas.translate(A4[0] / 2, A4[1] / 2)
        canvas.rotate(45)
        canvas.drawCentredString(0, 0, "PRÉVISUALISATION")
        canvas.restoreState()

    return _footer


# --- Construction du story complet -------------------------------------------

def _build_full_story(analysis: Analysis, company: Company, styles: dict) -> list:
    """
    Construit la liste complète des éléments ReportLab pour le rapport d'analyse.
    Garantit ≥ 8 pages (FIX #13) via des sections détaillées et mise en page aérée.
    """
    story = []

    # -- PAGE 1 : COUVERTURE --------------------------------------------------
    story.append(Spacer(1, 2.5 * cm))
    story.append(_p("ESG Optimizer AI", styles["title"]))
    story.append(_p("Rapport d'Analyse ESG", styles["subtitle"]))
    story.append(Spacer(1, 0.8 * cm))

    # Nom entreprise mis en valeur
    story.append(_p(f"<b>{company.name}</b>", ParagraphStyle(
        "CoverCompany", parent=styles["title"], fontSize=22, textColor=BRAND_DARK,
    )))
    if company.sector:
        story.append(_p(f"Secteur : {company.sector}", styles["subtitle"]))
    if analysis.report_year:
        story.append(_p(f"Exercice de reporting : <b>{analysis.report_year}</b>", styles["subtitle"]))
    story.append(Spacer(1, 1.5 * cm))

    # Score global en grand
    global_score = analysis.score_global
    score_color_hex = (
        "#16A34A" if (global_score or 0) >= 80 else
        "#2563EB" if (global_score or 0) >= 60 else
        "#EA580C" if (global_score or 0) >= 40 else "#DC2626"
    )
    story.append(_p(
        f'<font color="{score_color_hex}"><b>{int(global_score) if global_score else "-"}</b></font>'
        f'<font size="14" color="#94A3B8"> /100</font>',
        styles["score_big"],
    ))
    story.append(_p("Score ESG Global", styles["subtitle"]))

    story.append(Spacer(1, 1 * cm))
    date_str = analysis.created_at.strftime("%d/%m/%Y") if analysis.created_at else "N/A"
    story.append(_p(
        f"Analyse réalisée le {date_str} · Durée : {analysis.processing_time_s or 0:.1f}s",
        styles["small"],
    ))
    story.append(Spacer(1, 0.5 * cm))
    story.append(_p(
        "<i>Ce rapport a été généré automatiquement par ESG Optimizer AI sur la base "
        "des informations contenues dans le document analysé. Il constitue un outil "
        "d'aide à la décision et ne remplace pas un audit réalisé par un expert certifié.</i>",
        styles["small"],
    ))
    story.append(PageBreak())

    # -- PAGE 2 : RÉSUMÉ EXÉCUTIF ---------------------------------------------
    story.append(_p("1. Résumé exécutif", styles["h1"]))
    if analysis.executive_summary:
        story.append(_p(analysis.executive_summary, styles["body"]))
    else:
        story.append(_p("<i>Aucun résumé disponible.</i>", styles["body"]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(_p(
        "Ce rapport couvre les trois piliers du reporting extra-financier : "
        "<b>Environnement (E)</b>, <b>Social (S)</b> et <b>Gouvernance (G)</b>, "
        "tels que définis par les standards <b>ESRS</b> (European Sustainability Reporting Standards) "
        "de la directive CSRD. Chaque score est calculé sur 100 points selon la densité "
        "et la qualité des informations divulguées dans le rapport analysé.",
        styles["body"],
    ))
    story.append(Spacer(1, 0.5 * cm))
    story.append(_p(
        "<b>Méthodologie d'évaluation :</b> L'analyse est conduite par GPT-4o avec un système "
        "prompt calibré sur les 10 standards ESRS (E1-E5, S1-S4, G1). La température de génération "
        "est fixée à 0,2 pour garantir des résultats reproductibles. Les scores reflètent la "
        "couverture des indicateurs requis, pas leur performance absolue.",
        styles["body"],
    ))
    story.append(PageBreak())

    # -- PAGE 3 : SCORES ESG --------------------------------------------------
    story.append(_p("2. Scores ESG détaillés", styles["h1"]))

    pillar_descriptions = {
        "Environnement": (
            "Mesure la qualité des informations relatives au changement climatique, "
            "à la biodiversité, à la gestion de l'eau et à l'économie circulaire."
        ),
        "Social": (
            "Évalue le traitement des effectifs propres, des travailleurs de la chaîne "
            "de valeur, des communautés affectées et des consommateurs finaux."
        ),
        "Gouvernance": (
            "Analyse les pratiques de conduite des affaires, la transparence fiscale "
            "et les dispositifs de lutte contre la corruption."
        ),
        "Global": (
            "Score composite pondéré reflétant la maturité globale du reporting ESG."
        ),
    }

    scores_data = [
        [
            _p("<b>Pilier</b>", styles["table_header"]),
            _p("<b>Score</b>", styles["table_header"]),
            _p("<b>Niveau</b>", styles["table_header"]),
            _p("<b>Interprétation</b>", styles["table_header"]),
        ],
    ]
    for pillar, score_val, desc in [
        ("Environnement", analysis.score_env, pillar_descriptions["Environnement"]),
        ("Social", analysis.score_social, pillar_descriptions["Social"]),
        ("Gouvernance", analysis.score_gov, pillar_descriptions["Gouvernance"]),
        ("GLOBAL", analysis.score_global, pillar_descriptions["Global"]),
    ]:
        scores_data.append([
            _p(f"<b>{pillar}</b>", styles["table_cell"]),
            _p(
                f"<b>{int(score_val)}/100</b>" if score_val is not None else "N/A",
                styles["table_cell"],
            ),
            _p(_score_level(score_val), styles["table_cell"]),
            _p(desc, styles["table_cell"]),
        ])

    # FIX #13 : colWidths ajustées pour éviter les chevauchements
    scores_table = Table(scores_data, colWidths=[3.5 * cm, 2.5 * cm, 3 * cm, 8 * cm])
    scores_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(scores_table)
    story.append(Spacer(1, 0.8 * cm))

    # Grille de niveaux
    story.append(_p("<b>Grille de lecture des niveaux :</b>", styles["h2"]))
    levels_data = [
        [_p("<b>Score</b>", styles["table_header"]), _p("<b>Niveau</b>", styles["table_header"]),
         _p("<b>Signification</b>", styles["table_header"])],
        [_p("80-100", styles["table_cell"]), _p("Mature", styles["table_cell"]),
         _p("Reporting complet, indicateurs quantifiés, objectifs définis", styles["table_cell"])],
        [_p("60-79", styles["table_cell"]), _p("Avancé", styles["table_cell"]),
         _p("Bonne couverture, quelques lacunes quantitatives", styles["table_cell"])],
        [_p("40-59", styles["table_cell"]), _p("Basique", styles["table_cell"]),
         _p("Indicateurs partiels, approche qualitative dominante", styles["table_cell"])],
        [_p("20-39", styles["table_cell"]), _p("Embryonnaire", styles["table_cell"]),
         _p("Informations éparses, peu structurées", styles["table_cell"])],
        [_p("0-19", styles["table_cell"]), _p("Quasi absent", styles["table_cell"]),
         _p("Reporting ESG inexistant ou insuffisant", styles["table_cell"])],
    ]
    levels_table = Table(levels_data, colWidths=[2.5 * cm, 3 * cm, 11.5 * cm])
    levels_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(levels_table)
    story.append(PageBreak())

    # -- PAGE 4 : CONFORMITÉ CSRD ---------------------------------------------
    story.append(_p("3. Conformité CSRD", styles["h1"]))
    csrd_pct = analysis.csrd_coverage_pct or 0

    if csrd_pct == 100:
        csrd_status = "CSRD Ready ✓"
        csrd_color = "green"
    elif csrd_pct >= 80:
        csrd_status = "Conformité Avancée"
        csrd_color = "#EA580C"
    else:
        csrd_status = "Non conforme CSRD"
        csrd_color = "red"

    story.append(_p(
        f"Statut CSRD : <font color='{csrd_color}'><b>{csrd_status}</b></font> - "
        f"Couverture des standards ESRS : <b>{csrd_pct:.0f}%</b>",
        styles["body"],
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(_p(
        "La conformité CSRD requiert une couverture à <b>100%</b> des standards ESRS applicables "
        "à votre secteur. Entre 80 et 99%, le rapport est considéré en <b>Conformité Avancée</b> "
        "mais des efforts complémentaires sont nécessaires avant la date limite de dépôt.",
        styles["body"],
    ))

    missing = _safe_json_loads(analysis.missing_disclosures) or []
    if missing:
        story.append(_p("Disclosures manquantes identifiées :", styles["h2"]))
        for item in missing[:15]:
            story.append(_p(f"-> {item}", styles["body_left"]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(_p(
        "<b>Calendrier CSRD :</b> La directive s'applique aux grandes entreprises depuis 2025 "
        "(exercice 2024), aux PME cotées en 2026 (exercice 2025). Les PME non cotées peuvent "
        "appliquer un standard simplifié (VSME) à partir de 2026.",
        styles["callout"],
    ))
    story.append(PageBreak())

    # -- PAGE 5 : COUVERTURE ESRS ---------------------------------------------
    story.append(_p("4. Couverture ESRS détaillée", styles["h1"]))
    esrs = _safe_json_loads(analysis.esrs_coverage) or {}

    esrs_descriptions = {
        "E1_climate_change": ("E1 - Changement climatique",
            "Émissions GES (scope 1-2-3), objectifs climatiques, risques physiques et de transition"),
        "E2_pollution": ("E2 - Pollution",
            "Pollution de l'air, de l'eau, des sols ; substances dangereuses"),
        "E3_water_marine": ("E3 - Eau et ressources marines",
            "Consommation d'eau, gestion des effluents, biodiversité marine"),
        "E4_biodiversity": ("E4 - Biodiversité et écosystèmes",
            "Impacts sur la biodiversité, déforestation, utilisation des terres"),
        "E5_circular_economy": ("E5 - Économie circulaire",
            "Déchets, recyclage, gestion en fin de vie des produits"),
        "S1_own_workforce": ("S1 - Effectifs propres",
            "Conditions de travail, santé/sécurité, diversité, rémunération"),
        "S2_value_chain_workers": ("S2 - Travailleurs de la chaîne de valeur",
            "Droits des travailleurs chez les fournisseurs et sous-traitants"),
        "S3_affected_communities": ("S3 - Communautés affectées",
            "Impacts sociaux locaux, droits des populations riveraines"),
        "S4_consumers": ("S4 - Consommateurs et utilisateurs finaux",
            "Sécurité des produits, marketing responsable, confidentialité"),
        "G1_business_conduct": ("G1 - Conduite des affaires",
            "Anti-corruption, conformité fiscale, protection des lanceurs d'alerte"),
    }

    if esrs:
        esrs_data = [
            [
                _p("<b>Standard ESRS</b>", styles["table_header"]),
                _p("<b>Description</b>", styles["table_header"]),
                _p("<b>Couvert</b>", styles["table_header"]),
            ]
        ]
        for key, (label, desc) in esrs_descriptions.items():
            covered = esrs.get(key, False)
            status_text = "✓ OUI" if covered else "✗ NON"
            status_color = "green" if covered else "red"
            esrs_data.append([
                _p(f"<b>{label}</b>", styles["table_cell"]),
                _p(desc, styles["table_cell"]),
                _p(f'<font color="{status_color}"><b>{status_text}</b></font>', styles["table_cell"]),
            ])

        esrs_table = Table(esrs_data, colWidths=[4.5 * cm, 9 * cm, 2.5 * cm])
        esrs_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(esrs_table)
    else:
        story.append(_p("<i>Données ESRS non disponibles.</i>", styles["body"]))

    story.append(PageBreak())

    # -- PAGE 6 : KPIs --------------------------------------------------------
    kpis = _safe_json_loads(analysis.kpis_detected) or []
    story.append(_p("5. KPIs détectés dans le rapport", styles["h1"]))

    if kpis:
        story.append(_p(
            f"{len(kpis)} indicateur(s) clé(s) de performance ont été identifiés dans le document. "
            "Ils sont classés par pilier ESG.",
            styles["body"],
        ))
        story.append(Spacer(1, 0.3 * cm))
        kpi_data = [
            [
                _p("<b>Indicateur</b>", styles["table_header"]),
                _p("<b>Valeur</b>", styles["table_header"]),
                _p("<b>Unité</b>", styles["table_header"]),
                _p("<b>Réf. ESRS</b>", styles["table_header"]),
                _p("<b>Pilier</b>", styles["table_header"]),
            ]
        ]
        for kpi in kpis[:15]:  # FIX #13 : plus de KPIs affichés
            kpi_data.append([
                _p(kpi.get("name", "-"), styles["table_cell"]),
                _p(str(kpi.get("value", "-")), styles["table_cell"]),
                _p(kpi.get("unit", "-"), styles["table_cell"]),
                _p(kpi.get("esrs_reference", "-"), styles["table_cell"]),
                _p(kpi.get("pillar", "-"), styles["table_cell"]),
            ])

        # FIX #13 : colWidths adaptées pour éviter chevauchements
        kpi_table = Table(kpi_data, colWidths=[5.5 * cm, 2.5 * cm, 2 * cm, 3 * cm, 1.5 * cm])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (4, 0), (4, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(kpi_table)
    else:
        story.append(_p("<i>Aucun KPI quantifié détecté dans le document.</i>", styles["body"]))

    story.append(PageBreak())

    # -- PAGE 7 : FORCES & FAIBLESSES -----------------------------------------
    strengths = _safe_json_loads(analysis.strengths) or []
    weaknesses = _safe_json_loads(analysis.weaknesses) or []

    story.append(_p("6. Forces et lacunes identifiées", styles["h1"]))

    if strengths:
        story.append(_p("Points forts", styles["h2"]))
        story.append(_p(
            "Les éléments suivants constituent des atouts dans le reporting ESG de l'entreprise :",
            styles["body"],
        ))
        for s in strengths[:8]:
            story.append(_p(
                f"<font color='green'>&#9654;</font> <b>[{s.get('pillar', '?')}]</b> {s.get('description', '')}",
                styles["body_left"],
            ))
            story.append(Spacer(1, 1 * mm))

    story.append(Spacer(1, 0.5 * cm))

    if weaknesses:
        story.append(_p("Lacunes identifiées", styles["h2"]))
        story.append(_p(
            "Les points suivants nécessitent une amélioration pour renforcer la conformité CSRD :",
            styles["body"],
        ))
        for w in weaknesses[:8]:
            story.append(_p(
                f"<font color='red'>&#9654;</font> <b>[{w.get('pillar', '?')}]</b> {w.get('description', '')}",
                styles["body_left"],
            ))
            story.append(Spacer(1, 1 * mm))

    story.append(PageBreak())

    # -- PAGE 8 : RECOMMANDATIONS ---------------------------------------------
    recommendations = _safe_json_loads(analysis.recommendations) or []
    story.append(_p("7. Plan d'actions recommandées", styles["h1"]))

    if recommendations:
        story.append(_p(
            f"{len(recommendations)} recommandation(s) priorisée(s) ont été générées. "
            "La priorité 1 correspond à l'action à impact immédiat le plus élevé.",
            styles["body"],
        ))
        story.append(Spacer(1, 0.3 * cm))

        rec_data = [
            [
                _p("<b>Prio.</b>", styles["table_header"]),
                _p("<b>Pilier</b>", styles["table_header"]),
                _p("<b>Action recommandée</b>", styles["table_header"]),
                _p("<b>Impact attendu</b>", styles["table_header"]),
                _p("<b>Réf. ESRS</b>", styles["table_header"]),
            ]
        ]
        sorted_recs = sorted(recommendations, key=lambda r: r.get("priority", 5))
        for rec in sorted_recs[:10]:
            rec_data.append([
                _p(str(rec.get("priority", "-")), styles["table_cell"]),
                _p(rec.get("pillar", "-"), styles["table_cell"]),
                _p(rec.get("action", "-"), styles["table_cell"]),
                _p(rec.get("expected_impact", "-") or "-", styles["table_cell"]),
                _p(rec.get("esrs_reference", "-"), styles["table_cell"]),
            ])

        # FIX #13 : colWidths pensées pour contenu long dans colonnes Action/Impact
        rec_table = Table(rec_data, colWidths=[1.2 * cm, 1.5 * cm, 5.5 * cm, 4.8 * cm, 2 * cm])
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_ORANGE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (1, -1), "CENTER"),
            ("ALIGN", (2, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(rec_table)
    else:
        story.append(_p("<i>Aucune recommandation disponible.</i>", styles["body"]))

    story.append(PageBreak())

    # -- PAGE 9 (si delta) : ÉVOLUTION vs ANNÉE PRÉCÉDENTE -------------------
    if analysis.delta_global is not None:
        story.append(_p("8. Évolution vs année précédente (Delta Report)", styles["h1"]))
        story.append(_p(
            "Le Delta Report mesure la progression de vos scores ESG par rapport "
            "à l'exercice précédent. Une variation positive indique une amélioration "
            "de la qualité et de la complétude du reporting.",
            styles["body"],
        ))
        story.append(Spacer(1, 0.3 * cm))

        delta_data = [
            [
                _p("<b>Pilier</b>", styles["table_header"]),
                _p("<b>Delta</b>", styles["table_header"]),
                _p("<b>Tendance</b>", styles["table_header"]),
            ],
            ["Environnement",
             f"{analysis.delta_env:+.0f}" if analysis.delta_env is not None else "-",
             _trend_symbol(analysis.delta_env)],
            ["Social",
             f"{analysis.delta_social:+.0f}" if analysis.delta_social is not None else "-",
             _trend_symbol(analysis.delta_social)],
            ["Gouvernance",
             f"{analysis.delta_gov:+.0f}" if analysis.delta_gov is not None else "-",
             _trend_symbol(analysis.delta_gov)],
            ["GLOBAL",
             f"{analysis.delta_global:+.0f}" if analysis.delta_global is not None else "-",
             _trend_symbol(analysis.delta_global)],
        ]
        # Convertir les cellules texte en Paragraphs
        for i in range(1, len(delta_data)):
            delta_data[i] = [_p(str(c), styles["table_cell"]) for c in delta_data[i]]

        delta_table = Table(delta_data, colWidths=[5 * cm, 3 * cm, 9 * cm])
        delta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(delta_table)
        story.append(PageBreak())

    # -- PAGE FINALE : MÉTHODOLOGIE & DISCLAIMER ------------------------------
    sec_num = 9 if analysis.delta_global is not None else 8
    story.append(_p(f"{sec_num}. Méthodologie et avertissements", styles["h1"]))
    story.append(_p("<b>Modèle d'analyse</b>", styles["h2"]))
    story.append(_p(
        "L'analyse est conduite par le modèle GPT-4o d'OpenAI, configuré avec un système "
        "prompt spécialisé sur les standards ESRS de la CSRD. Le document soumis est extrait "
        "puis transmis au modèle qui produit un JSON structuré comprenant : scores E/S/G, "
        "couverture ESRS, KPIs, forces/faiblesses et recommandations.",
        styles["body"],
    ))
    story.append(_p("<b>Limites de l'analyse automatisée</b>", styles["h2"]))
    story.append(_p(
        "• Les scores reflètent la qualité de la divulgation, non la performance réelle de l'entreprise.\n"
        "• Un score élevé indique un reporting bien documenté, pas nécessairement des pratiques exemplaires.\n"
        "• L'IA peut manquer des informations présentées sous forme d'images, graphiques ou tableaux complexes.\n"
        "• Ce rapport ne constitue pas une certification ni un audit au sens réglementaire.",
        styles["body"],
    ))
    story.append(_p("<b>Protection des données</b>", styles["h2"]))
    story.append(_p(
        "Vos documents sont traités sur des serveurs européens et ne sont pas utilisés "
        "pour entraîner les modèles d'IA (header OpenAI `x-openai-skip-training` activé). "
        "Les fichiers originaux sont supprimés après analyse. Les résultats sont conservés "
        "selon les termes de votre abonnement (12 mois pour le plan Essentiel, illimité pour Pro).",
        styles["body"],
    ))
    story.append(Spacer(1, 1 * cm))
    story.append(_p(
        f"Rapport généré par ESG Optimizer AI · contact@esg-optimizer.fr · {datetime.now(timezone.utc).strftime('%d/%m/%Y')}",
        styles["small"],
    ))

    return story


# --- RAPPORT COMPLET ---------------------------------------------------------

def generate_analysis_pdf(analysis: Analysis, company: Company) -> bytes:
    """
    Génère le rapport PDF complet d'une analyse ESG.
    FIX #13 : Logo en header, ≥ 8 pages, mise en page aérée, tableaux sans chevauchements.
    Retourne les bytes du PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2.5 * cm,  # espace pour le header logo
        bottomMargin=2.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = _get_styles()
    story = _build_full_story(analysis, company, styles)
    footer_fn = _make_footer(show_logo=True)
    doc.build(story, onFirstPage=footer_fn, onLaterPages=footer_fn)
    return buffer.getvalue()


# --- RAPPORT PREVIEW (FIX #12) -----------------------------------------------

def generate_preview(analysis: Analysis, company: Company) -> bytes:
    """
    FIX #12 : Génère un PDF de prévisualisation limité à 3 pages avec watermark PRÉVISUALISATION.
    Destiné au plan Découverte (gratuit).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = _get_styles()
    story = []

    # -- PAGE 1 : COUVERTURE PREVIEW ------------------------------------------
    story.append(_p(
        "- APERÇU GRATUIT - Plan Découverte",
        styles["preview_banner"],
    ))
    story.append(Spacer(1, 0.5 * cm))
    story.append(_p("ESG Optimizer AI", styles["title"]))
    story.append(_p("Rapport d'Analyse ESG - Prévisualisation", styles["subtitle"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(_p(f"<b>{company.name}</b>", ParagraphStyle(
        "CoverPreview", parent=styles["title"], fontSize=20, textColor=BRAND_DARK,
    )))
    if company.sector:
        story.append(_p(f"Secteur : {company.sector}", styles["subtitle"]))
    if analysis.report_year:
        story.append(_p(f"Exercice de reporting : {analysis.report_year}", styles["subtitle"]))
    story.append(Spacer(1, 1 * cm))

    global_score = analysis.score_global
    story.append(_p(
        f"<b>{int(global_score) if global_score else '-'}</b><font size='14' color='#94A3B8'>/100</font>",
        styles["score_big"],
    ))
    story.append(_p("Score ESG Global", styles["subtitle"]))
    story.append(Spacer(1, 1.5 * cm))
    story.append(_p(
        "Ce document est une <b>prévisualisation gratuite</b> de votre rapport ESG complet. "
        "Il contient les 3 premières pages (couverture, résumé, scores). "
        "Le rapport intégral (8+ pages) est disponible à partir du plan <b>Essentiel</b>.",
        styles["body"],
    ))
    story.append(PageBreak())

    # -- PAGE 2 : RÉSUMÉ EXÉCUTIF ---------------------------------------------
    story.append(_p("Résumé exécutif", styles["h1"]))
    if analysis.executive_summary:
        story.append(_p(analysis.executive_summary, styles["body"]))
    else:
        story.append(_p("<i>Résumé non disponible.</i>", styles["body"]))
    story.append(Spacer(1, 1 * cm))

    # Teaser scores partiels
    story.append(_p("<i>Les scores détaillés E/S/G sont disponibles sur la page suivante.</i>", styles["small"]))
    story.append(PageBreak())

    # -- PAGE 3 : SCORES + CTA UPGRADE ---------------------------------------
    story.append(_p("Scores ESG", styles["h1"]))

    scores_preview = [
        [_p("<b>Pilier</b>", styles["table_header"]), _p("<b>Score</b>", styles["table_header"])],
        [_p("Environnement", styles["table_cell"]),
         _p(f"{int(analysis.score_env)}/100" if analysis.score_env else "-", styles["table_cell"])],
        [_p("Social", styles["table_cell"]),
         _p(f"{int(analysis.score_social)}/100" if analysis.score_social else "-", styles["table_cell"])],
        [_p("Gouvernance", styles["table_cell"]),
         _p(f"{int(analysis.score_gov)}/100" if analysis.score_gov else "-", styles["table_cell"])],
        [_p("<b>GLOBAL</b>", styles["table_cell"]),
         _p(f"<b>{int(analysis.score_global)}/100</b>" if analysis.score_global else "-", styles["table_cell"])],
    ]
    t = Table(scores_preview, colWidths=[8 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 1.5 * cm))

    # CTA déblocage
    cta_data = [[_p(
        "<b>Débloquez le rapport complet</b>\n\n"
        "Le rapport intégral contient : couverture ESRS détaillée, "
        "liste des KPIs détectés, forces &amp; lacunes, plan d'actions priorisé, "
        "et Delta Report si vous avez déjà analysé un rapport précédent.\n\n"
        "-> Plan Essentiel : 39 € par analyse\n"
        "-> Plan Pro : 129 € / mois · analyses illimitées\n\n"
        "Rendez-vous sur esg-optimizer.fr pour passer au plan supérieur.",
        styles["body"],
    )]]
    cta_table = Table(cta_data, colWidths=[15 * cm])
    cta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
        ("BOX", (0, 0), (-1, -1), 1.5, BRAND_GREEN),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(cta_table)

    preview_footer = _make_preview_footer()
    doc.build(story, onFirstPage=preview_footer, onLaterPages=preview_footer)
    return buffer.getvalue()


# --- RAPPORT DELTA PDF -------------------------------------------------------

def generate_delta_pdf(
    current: Analysis,
    previous: Analysis,
    company: Company,
    delta_narrative: dict,
) -> bytes:
    """
    Génère le rapport PDF delta (comparaison N vs N-1).
    FIX #13 : Tableaux avec Paragraphs + colWidths adaptées.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = _get_styles()
    story = []

    # COUVERTURE
    story.append(Spacer(1, 2.5 * cm))
    story.append(_p("ESG Optimizer AI", styles["title"]))
    story.append(_p("Rapport d'Évolution ESG (Delta Report)", styles["subtitle"]))
    story.append(Spacer(1, 1 * cm))
    story.append(_p(f"<b>{company.name}</b>", ParagraphStyle(
        "DeltaCover", parent=styles["title"], fontSize=20, textColor=BRAND_DARK,
    )))
    year_label = ""
    if previous.report_year and current.report_year:
        year_label = f"{previous.report_year} -> {current.report_year}"
    story.append(_p(f"Période couverte : {year_label}", styles["subtitle"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(_p(
        "Ce rapport compare votre performance ESG entre deux exercices consécutifs. "
        "Il identifie les améliorations, régressions et nouvelles opportunités.",
        styles["body"],
    ))
    story.append(PageBreak())

    # SYNTHÈSE
    story.append(_p("1. Synthèse de l'évolution", styles["h1"]))
    story.append(_p(delta_narrative.get("delta_summary", "Aucune synthèse disponible."), styles["body"]))
    story.append(PageBreak())

    # ÉVOLUTION DES SCORES
    story.append(_p("2. Évolution des scores", styles["h1"]))
    score_evo = delta_narrative.get("score_evolution", {})
    evo_data = [
        [
            _p("<b>Pilier</b>", styles["table_header"]),
            _p(f"<b>N-1 ({previous.report_year})</b>", styles["table_header"]),
            _p(f"<b>N ({current.report_year})</b>", styles["table_header"]),
            _p("<b>Delta</b>", styles["table_header"]),
            _p("<b>Tendance</b>", styles["table_header"]),
        ]
    ]
    for pillar_key, pillar_label in [
        ("environment", "Environnement"),
        ("social", "Social"),
        ("governance", "Gouvernance"),
        ("global", "GLOBAL"),
    ]:
        evo = score_evo.get(pillar_key, {})
        prev_val = evo.get("previous", "-")
        curr_val = evo.get("current", "-")
        delta_val = evo.get("delta", "-")
        trend = evo.get("trend", "-")
        delta_str = f"{delta_val:+d}" if isinstance(delta_val, (int, float)) else str(delta_val)
        trend_label = {
            "forte_amelioration": "++ Forte hausse",
            "amelioration": "+ Hausse",
            "stable": "= Stable",
            "degradation": "- Baisse",
            "forte_degradation": "-- Forte baisse",
        }.get(trend, str(trend))
        evo_data.append([
            _p(pillar_label, styles["table_cell"]),
            _p(str(prev_val), styles["table_cell"]),
            _p(str(curr_val), styles["table_cell"]),
            _p(delta_str, styles["table_cell"]),
            _p(trend_label, styles["table_cell"]),
        ])

    evo_table = Table(evo_data, colWidths=[3.5 * cm, 3 * cm, 3 * cm, 2.5 * cm, 4.5 * cm])
    evo_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (3, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(evo_table)
    story.append(PageBreak())

    # ÉVOLUTION ESRS
    esrs_evo = delta_narrative.get("esrs_evolution", {})
    if esrs_evo:
        story.append(_p("3. Évolution de la couverture ESRS", styles["h1"]))
        cov_prev = esrs_evo.get("coverage_previous", "-")
        cov_curr = esrs_evo.get("coverage_current", "-")
        story.append(_p(
            f"Couverture N-1 : <b>{cov_prev}%</b> -> Couverture N : <b>{cov_curr}%</b>",
            styles["body"],
        ))
        gained = esrs_evo.get("gained", [])
        lost = esrs_evo.get("lost", [])
        if gained:
            story.append(_p("Standards nouvellement couverts :", styles["h2"]))
            for g in gained:
                story.append(_p(f"<font color='green'>+ </font>{g}", styles["body_left"]))
        if lost:
            story.append(_p("Standards qui ne sont plus couverts :", styles["h2"]))
            for item in lost:
                story.append(_p(f"<font color='red'>- </font>{item}", styles["body_left"]))

    # COMPARAISON KPIs
    kpi_comp = delta_narrative.get("kpi_comparison", [])
    if kpi_comp:
        story.append(_p("4. Comparaison des KPIs", styles["h1"]))
        kpi_data = [
            [
                _p("<b>KPI</b>", styles["table_header"]),
                _p("<b>N-1</b>", styles["table_header"]),
                _p("<b>N</b>", styles["table_header"]),
                _p("<b>Évolution</b>", styles["table_header"]),
                _p("<b>Statut</b>", styles["table_header"]),
            ]
        ]
        for kpi in kpi_comp[:10]:
            status_symbol = {
                "improved": "+ Amélioré",
                "stable": "= Stable",
                "degraded": "- Dégradé",
                "new": "* Nouveau",
                "removed": "x Supprimé",
            }.get(kpi.get("status", ""), kpi.get("status", ""))
            kpi_data.append([
                _p(kpi.get("name", "-"), styles["table_cell"]),
                _p(str(kpi.get("previous_value", "-") or "-"), styles["table_cell"]),
                _p(str(kpi.get("current_value", "-") or "-"), styles["table_cell"]),
                _p(kpi.get("evolution", "-") or "-", styles["table_cell"]),
                _p(status_symbol, styles["table_cell"]),
            ])

        kpi_table = Table(kpi_data, colWidths=[4 * cm, 2.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 0), (2, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(kpi_table)
        story.append(PageBreak())

    # AMÉLIORATIONS / RÉGRESSIONS
    improvements = delta_narrative.get("key_improvements", [])
    regressions = delta_narrative.get("key_regressions", [])

    if improvements or regressions:
        story.append(_p("5. Améliorations et régressions clés", styles["h1"]))
        if improvements:
            story.append(_p("Améliorations", styles["h2"]))
            for imp in improvements[:6]:
                story.append(_p(
                    f"<font color='green'>[{imp.get('pillar', '?')}]</font> {imp.get('description', '')}",
                    styles["body_left"],
                ))
        if regressions:
            story.append(_p("Régressions", styles["h2"]))
            for reg in regressions[:6]:
                story.append(_p(
                    f"<font color='red'>[{reg.get('pillar', '?')}]</font> {reg.get('description', '')}",
                    styles["body_left"],
                ))

    # ACTIONS PRIORITAIRES
    actions = delta_narrative.get("priority_actions", [])
    if actions:
        story.append(_p("6. Actions prioritaires", styles["h1"]))
        act_data = [
            [
                _p("<b>Prio.</b>", styles["table_header"]),
                _p("<b>Pilier</b>", styles["table_header"]),
                _p("<b>Action</b>", styles["table_header"]),
                _p("<b>Justification</b>", styles["table_header"]),
            ]
        ]
        for act in actions[:6]:
            act_data.append([
                _p(str(act.get("priority", "-")), styles["table_cell"]),
                _p(act.get("pillar", "-"), styles["table_cell"]),
                _p(act.get("action", "-"), styles["table_cell"]),
                _p(act.get("rationale", "-") or "-", styles["table_cell"]),
            ])
        act_table = Table(act_data, colWidths=[1.5 * cm, 1.5 * cm, 6 * cm, 6 * cm])
        act_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_ORANGE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(act_table)

    footer_fn = _make_footer(show_logo=True)
    doc.build(story, onFirstPage=footer_fn, onLaterPages=footer_fn)
    return buffer.getvalue()
