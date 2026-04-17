"""
ESG Optimizer MVP — Service de génération de rapports PDF.
Utilise ReportLab pour produire :
  - Rapport d'analyse ESG complet
  - Rapport Delta (comparaison N vs N-1)
"""

import io
import json
import logging
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
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

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Couleurs ESG Optimizer
# ──────────────────────────────────────────────
BRAND_GREEN = colors.HexColor("#16A34A")
BRAND_DARK = colors.HexColor("#1E293B")
BRAND_LIGHT = colors.HexColor("#F1F5F9")
BRAND_BLUE = colors.HexColor("#2563EB")
BRAND_ORANGE = colors.HexColor("#EA580C")
BRAND_RED = colors.HexColor("#DC2626")
BRAND_GRAY = colors.HexColor("#94A3B8")

PILLAR_COLORS = {
    "E": colors.HexColor("#16A34A"),  # Vert
    "S": colors.HexColor("#2563EB"),  # Bleu
    "G": colors.HexColor("#7C3AED"),  # Violet
}


def _safe_json_loads(raw: str | None) -> dict | list | None:
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


# ──────────────────────────────────────────────
# Styles
# ──────────────────────────────────────────────
def _get_styles() -> dict:
    """Retourne un dict de styles personnalisés."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CustomTitle",
            parent=base["Title"],
            fontSize=24,
            textColor=BRAND_DARK,
            spaceAfter=6 * mm,
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "CustomSubtitle",
            parent=base["Normal"],
            fontSize=12,
            textColor=BRAND_GRAY,
            alignment=TA_CENTER,
            spaceAfter=10 * mm,
        ),
        "h1": ParagraphStyle(
            "CustomH1",
            parent=base["Heading1"],
            fontSize=16,
            textColor=BRAND_GREEN,
            spaceBefore=8 * mm,
            spaceAfter=4 * mm,
        ),
        "h2": ParagraphStyle(
            "CustomH2",
            parent=base["Heading2"],
            fontSize=13,
            textColor=BRAND_DARK,
            spaceBefore=5 * mm,
            spaceAfter=3 * mm,
        ),
        "body": ParagraphStyle(
            "CustomBody",
            parent=base["Normal"],
            fontSize=10,
            textColor=BRAND_DARK,
            alignment=TA_JUSTIFY,
            spaceAfter=3 * mm,
            leading=14,
        ),
        "small": ParagraphStyle(
            "CustomSmall",
            parent=base["Normal"],
            fontSize=8,
            textColor=BRAND_GRAY,
        ),
        "score_big": ParagraphStyle(
            "ScoreBig",
            parent=base["Normal"],
            fontSize=28,
            textColor=BRAND_GREEN,
            alignment=TA_CENTER,
        ),
    }


def _score_color(score: float | None) -> colors.HexColor:
    """Retourne une couleur en fonction du score."""
    if score is None:
        return BRAND_GRAY
    if score >= 80:
        return BRAND_GREEN
    if score >= 60:
        return BRAND_BLUE
    if score >= 40:
        return BRAND_ORANGE
    return BRAND_RED


def _trend_symbol(delta: float | None) -> str:
    """Retourne un symbole textuel pour la tendance."""
    if delta is None:
        return "–"
    if delta >= 15:
        return "++ Forte hausse"
    if delta >= 5:
        return "+ Hausse"
    if delta > -5:
        return "= Stable"
    if delta > -15:
        return "- Baisse"
    return "-- Forte baisse"


def _footer(canvas, doc):
    """Pied de page avec numéro et branding."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(BRAND_GRAY)
    canvas.drawString(2 * cm, 1.2 * cm, "ESG Optimizer AI — Rapport généré automatiquement")
    canvas.drawRightString(
        A4[0] - 2 * cm, 1.2 * cm,
        f"Page {doc.page} — {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}"
    )
    canvas.restoreState()


# ══════════════════════════════════════════════
# RAPPORT D'ANALYSE ESG
# ══════════════════════════════════════════════

def generate_analysis_pdf(analysis: Analysis, company: Company) -> bytes:
    """
    Génère le rapport PDF complet d'une analyse ESG.
    Retourne les bytes du PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = _get_styles()
    story = []

    # ── PAGE DE TITRE ──
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("ESG Optimizer AI", styles["title"]))
    story.append(Paragraph("Rapport d'Analyse ESG", styles["subtitle"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"<b>{company.name}</b>", ParagraphStyle(
        "CompanyName", parent=styles["title"], fontSize=20, textColor=BRAND_DARK,
    )))
    if company.sector:
        story.append(Paragraph(f"Secteur : {company.sector}", styles["subtitle"]))
    if analysis.report_year:
        story.append(Paragraph(f"Année de reporting : {analysis.report_year}", styles["subtitle"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        f"Analyse réalisée le {analysis.created_at.strftime('%d/%m/%Y') if analysis.created_at else 'N/A'}",
        styles["small"],
    ))
    story.append(PageBreak())

    # ── RÉSUMÉ EXÉCUTIF ──
    story.append(Paragraph("1. Résumé exécutif", styles["h1"]))
    if analysis.executive_summary:
        story.append(Paragraph(analysis.executive_summary, styles["body"]))
    else:
        story.append(Paragraph("<i>Aucun résumé disponible.</i>", styles["body"]))

    # ── SCORES ESG ──
    story.append(Paragraph("2. Scores ESG", styles["h1"]))

    scores_data = [
        ["Pilier", "Score", "Niveau"],
        [
            Paragraph("<b>Environnement</b>", styles["body"]),
            Paragraph(f"<b>{int(analysis.score_env)}/100</b>" if analysis.score_env is not None else "N/A", styles["body"]),
            _score_level(analysis.score_env),
        ],
        [
            Paragraph("<b>Social</b>", styles["body"]),
            Paragraph(f"<b>{int(analysis.score_social)}/100</b>" if analysis.score_social is not None else "N/A", styles["body"]),
            _score_level(analysis.score_social),
        ],
        [
            Paragraph("<b>Gouvernance</b>", styles["body"]),
            Paragraph(f"<b>{int(analysis.score_gov)}/100</b>" if analysis.score_gov is not None else "N/A", styles["body"]),
            _score_level(analysis.score_gov),
        ],
        [
            Paragraph("<b>GLOBAL</b>", styles["body"]),
            Paragraph(f"<b>{int(analysis.score_global)}/100</b>" if analysis.score_global is not None else "N/A", styles["body"]),
            _score_level(analysis.score_global),
        ],
    ]

    scores_table = Table(scores_data, colWidths=[6 * cm, 4 * cm, 6 * cm])
    scores_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(scores_table)

    # ── CONFORMITÉ CSRD ──
    story.append(Paragraph("3. Conformité CSRD", styles["h1"]))
    csrd_status = "Prêt" if analysis.csrd_ready else "Non prêt"
    csrd_color = "green" if analysis.csrd_ready else "red"
    story.append(Paragraph(
        f"Statut CSRD : <font color='{csrd_color}'><b>{csrd_status}</b></font> — "
        f"Couverture : <b>{analysis.csrd_coverage_pct or 0:.0f}%</b>",
        styles["body"],
    ))

    missing = _safe_json_loads(analysis.missing_disclosures) or []
    if missing:
        story.append(Paragraph("Disclosures manquantes :", styles["h2"]))
        for item in missing[:10]:
            story.append(Paragraph(f"  - {item}", styles["body"]))

    # ── COUVERTURE ESRS ──
    story.append(Paragraph("4. Couverture ESRS", styles["h1"]))
    esrs = _safe_json_loads(analysis.esrs_coverage) or {}
    if esrs:
        esrs_data = [["Standard ESRS", "Couvert"]]
        esrs_labels = {
            "E1_climate_change": "E1 — Changement climatique",
            "E2_pollution": "E2 — Pollution",
            "E3_water_marine": "E3 — Eau & ressources marines",
            "E4_biodiversity": "E4 — Biodiversité",
            "E5_circular_economy": "E5 — Économie circulaire",
            "S1_own_workforce": "S1 — Effectifs propres",
            "S2_value_chain_workers": "S2 — Travailleurs chaîne de valeur",
            "S3_affected_communities": "S3 — Communautés affectées",
            "S4_consumers": "S4 — Consommateurs",
            "G1_business_conduct": "G1 — Conduite des affaires",
        }
        for key, label in esrs_labels.items():
            covered = esrs.get(key, False)
            symbol = "OUI" if covered else "NON"
            esrs_data.append([label, symbol])

        esrs_table = Table(esrs_data, colWidths=[10 * cm, 4 * cm])
        esrs_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(esrs_table)

    # ── KPIs ──
    kpis = _safe_json_loads(analysis.kpis_detected) or []
    if kpis:
        story.append(Paragraph("5. KPIs détectés", styles["h1"]))
        kpi_data = [["KPI", "Valeur", "Unité", "Réf. ESRS", "Pilier"]]
        for kpi in kpis[:10]:
            kpi_data.append([
                kpi.get("name", ""),
                kpi.get("value", ""),
                kpi.get("unit", ""),
                kpi.get("esrs_reference", ""),
                kpi.get("pillar", ""),
            ])
        kpi_table = Table(kpi_data, colWidths=[4.5 * cm, 3 * cm, 2 * cm, 3 * cm, 1.5 * cm])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(kpi_table)

    # ── FORCES / FAIBLESSES ──
    strengths = _safe_json_loads(analysis.strengths) or []
    weaknesses = _safe_json_loads(analysis.weaknesses) or []

    if strengths or weaknesses:
        story.append(Paragraph("6. Forces et faiblesses", styles["h1"]))

        if strengths:
            story.append(Paragraph("Points forts", styles["h2"]))
            for s in strengths[:5]:
                story.append(Paragraph(
                    f"<font color='green'>[{s.get('pillar', '?')}]</font> {s.get('description', '')}",
                    styles["body"],
                ))

        if weaknesses:
            story.append(Paragraph("Lacunes identifiées", styles["h2"]))
            for w in weaknesses[:5]:
                story.append(Paragraph(
                    f"<font color='red'>[{w.get('pillar', '?')}]</font> {w.get('description', '')}",
                    styles["body"],
                ))

    # ── RECOMMANDATIONS ──
    recommendations = _safe_json_loads(analysis.recommendations) or []
    if recommendations:
        story.append(Paragraph("7. Recommandations", styles["h1"]))
        rec_data = [["Priorité", "Pilier", "Action", "Impact attendu", "Réf."]]
        for rec in recommendations[:7]:
            rec_data.append([
                str(rec.get("priority", "")),
                rec.get("pillar", ""),
                Paragraph(rec.get("action", ""), styles["small"]),
                Paragraph(rec.get("expected_impact", "") or "", styles["small"]),
                rec.get("esrs_reference", ""),
            ])
        rec_table = Table(rec_data, colWidths=[1.5 * cm, 1.5 * cm, 5 * cm, 4.5 * cm, 2 * cm])
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_ORANGE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(rec_table)

    # ── DELTAS (si disponibles) ──
    if analysis.delta_global is not None:
        story.append(PageBreak())
        story.append(Paragraph("8. Évolution vs année précédente", styles["h1"]))
        delta_data = [
            ["Pilier", "Delta", "Tendance"],
            ["Environnement", f"{analysis.delta_env:+.0f}" if analysis.delta_env is not None else "–", _trend_symbol(analysis.delta_env)],
            ["Social", f"{analysis.delta_social:+.0f}" if analysis.delta_social is not None else "–", _trend_symbol(analysis.delta_social)],
            ["Gouvernance", f"{analysis.delta_gov:+.0f}" if analysis.delta_gov is not None else "–", _trend_symbol(analysis.delta_gov)],
            ["GLOBAL", f"{analysis.delta_global:+.0f}" if analysis.delta_global is not None else "–", _trend_symbol(analysis.delta_global)],
        ]
        delta_table = Table(delta_data, colWidths=[5 * cm, 3 * cm, 6 * cm])
        delta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(delta_table)

    # Build
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()


def _score_level(score: float | None) -> str:
    """Retourne le niveau textuel d'un score."""
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


# ══════════════════════════════════════════════
# RAPPORT DELTA PDF
# ══════════════════════════════════════════════

def generate_delta_pdf(
    current: Analysis,
    previous: Analysis,
    company: Company,
    delta_narrative: dict,
) -> bytes:
    """
    Génère le rapport PDF delta (comparaison N vs N-1).
    Retourne les bytes du PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = _get_styles()
    story = []

    # ── PAGE DE TITRE ──
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("ESG Optimizer AI", styles["title"]))
    story.append(Paragraph("Rapport d'Évolution ESG (Delta)", styles["subtitle"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"<b>{company.name}</b>", ParagraphStyle(
        "CompanyNameDelta", parent=styles["title"], fontSize=20, textColor=BRAND_DARK,
    )))
    year_label = ""
    if previous.report_year and current.report_year:
        year_label = f"{previous.report_year} → {current.report_year}"
    story.append(Paragraph(f"Période : {year_label}", styles["subtitle"]))
    story.append(PageBreak())

    # ── RÉSUMÉ D'ÉVOLUTION ──
    story.append(Paragraph("1. Synthèse de l'évolution", styles["h1"]))
    summary = delta_narrative.get("delta_summary", "Aucune synthèse disponible.")
    story.append(Paragraph(summary, styles["body"]))

    # ── ÉVOLUTION DES SCORES ──
    story.append(Paragraph("2. Évolution des scores", styles["h1"]))
    score_evo = delta_narrative.get("score_evolution", {})

    evo_data = [["Pilier", "N-1", "N", "Delta", "Tendance"]]
    for pillar_key, pillar_label in [
        ("environment", "Environnement"),
        ("social", "Social"),
        ("governance", "Gouvernance"),
        ("global", "GLOBAL"),
    ]:
        evo = score_evo.get(pillar_key, {})
        prev_val = evo.get("previous", "–")
        curr_val = evo.get("current", "–")
        delta_val = evo.get("delta", "–")
        trend = evo.get("trend", "–")

        delta_str = f"{delta_val:+d}" if isinstance(delta_val, (int, float)) else str(delta_val)
        trend_label = {
            "forte_amelioration": "++ Forte hausse",
            "amelioration": "+ Hausse",
            "stable": "= Stable",
            "degradation": "- Baisse",
            "forte_degradation": "-- Forte baisse",
        }.get(trend, str(trend))

        evo_data.append([pillar_label, str(prev_val), str(curr_val), delta_str, trend_label])

    evo_table = Table(evo_data, colWidths=[3.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 4 * cm])
    evo_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (3, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(evo_table)

    # ── ÉVOLUTION ESRS ──
    esrs_evo = delta_narrative.get("esrs_evolution", {})
    if esrs_evo:
        story.append(Paragraph("3. Évolution de la couverture ESRS", styles["h1"]))
        cov_prev = esrs_evo.get("coverage_previous", "–")
        cov_curr = esrs_evo.get("coverage_current", "–")
        story.append(Paragraph(
            f"Couverture N-1 : <b>{cov_prev}%</b> → Couverture N : <b>{cov_curr}%</b>",
            styles["body"],
        ))
        gained = esrs_evo.get("gained", [])
        lost = esrs_evo.get("lost", [])
        if gained:
            story.append(Paragraph("Standards nouvellement couverts :", styles["h2"]))
            for g in gained:
                story.append(Paragraph(f"  <font color='green'>+</font> {g}", styles["body"]))
        if lost:
            story.append(Paragraph("Standards qui ne sont plus couverts :", styles["h2"]))
            for l in lost:
                story.append(Paragraph(f"  <font color='red'>-</font> {l}", styles["body"]))

    # ── COMPARAISON KPIs ──
    kpi_comp = delta_narrative.get("kpi_comparison", [])
    if kpi_comp:
        story.append(Paragraph("4. Comparaison des KPIs", styles["h1"]))
        kpi_data = [["KPI", "N-1", "N", "Évolution", "Statut"]]
        for kpi in kpi_comp[:8]:
            status_symbol = {
                "improved": "+ Amélioré",
                "stable": "= Stable",
                "degraded": "- Dégradé",
                "new": "* Nouveau",
                "removed": "x Supprimé",
            }.get(kpi.get("status", ""), kpi.get("status", ""))

            kpi_data.append([
                Paragraph(kpi.get("name", ""), styles["small"]),
                kpi.get("previous_value", "–") or "–",
                kpi.get("current_value", "–") or "–",
                Paragraph(kpi.get("evolution", "") or "", styles["small"]),
                status_symbol,
            ])

        kpi_table = Table(kpi_data, colWidths=[3.5 * cm, 2.5 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(kpi_table)

    # ── AMÉLIORATIONS / RÉGRESSIONS ──
    improvements = delta_narrative.get("key_improvements", [])
    regressions = delta_narrative.get("key_regressions", [])

    if improvements or regressions:
        story.append(Paragraph("5. Améliorations et régressions clés", styles["h1"]))
        if improvements:
            story.append(Paragraph("Améliorations", styles["h2"]))
            for imp in improvements[:5]:
                story.append(Paragraph(
                    f"<font color='green'>[{imp.get('pillar', '?')}]</font> {imp.get('description', '')}",
                    styles["body"],
                ))
        if regressions:
            story.append(Paragraph("Régressions", styles["h2"]))
            for reg in regressions[:5]:
                story.append(Paragraph(
                    f"<font color='red'>[{reg.get('pillar', '?')}]</font> {reg.get('description', '')}",
                    styles["body"],
                ))

    # ── ACTIONS PRIORITAIRES ──
    actions = delta_narrative.get("priority_actions", [])
    if actions:
        story.append(Paragraph("6. Actions prioritaires", styles["h1"]))
        act_data = [["Priorité", "Pilier", "Action", "Justification"]]
        for act in actions[:5]:
            act_data.append([
                str(act.get("priority", "")),
                act.get("pillar", ""),
                Paragraph(act.get("action", ""), styles["small"]),
                Paragraph(act.get("rationale", "") or "", styles["small"]),
            ])
        act_table = Table(act_data, colWidths=[1.5 * cm, 1.5 * cm, 5.5 * cm, 5.5 * cm])
        act_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_ORANGE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, BRAND_GRAY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(act_table)

    # Build
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
