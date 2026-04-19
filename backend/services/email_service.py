"""
ESG Optimizer MVP — Service d'envoi d'emails transactionnels via Resend.
Emails : bienvenue, analyse terminée, weekly digest.
"""

import logging
from typing import Optional

import resend

from backend.config import settings

logger = logging.getLogger(__name__)

# Configure Resend SDK
resend.api_key = settings.resend_api_key

# Constantes
FROM_EMAIL = "ESG Optimizer <noreply@esg-optimizer.fr>"
APP_URL = "https://esg-optimizer.fr"

# Couleurs du brand
GREEN = "#1A3D22"
DARK = "#111827"
GRAY = "#6B7280"
LIGHT_BG = "#F9FAFB"


def _is_configured() -> bool:
    """Vérifie que Resend est configuré."""
    return bool(settings.resend_api_key)


def _base_template(title: str, content: str) -> str:
    """Template HTML de base pour tous les emails."""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background: {LIGHT_BG}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background: {LIGHT_BG}; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: #FFFFFF; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: {DARK}; padding: 24px 32px; text-align: center;">
                            <span style="font-size: 24px; font-weight: 800; color: {GREEN};">ESG Optimizer</span>
                            <br>
                            <span style="font-size: 12px; color: #9CA3AF;">Reporting ESG intelligent</span>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px;">
                            {content}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background: {LIGHT_BG}; padding: 20px 32px; text-align: center; border-top: 1px solid #E5E7EB;">
                            <span style="font-size: 11px; color: #9CA3AF;">
                                ESG Optimizer AI — Analyse CSRD/ESRS automatisée
                                <br>
                                <a href="{APP_URL}" style="color: {GREEN}; text-decoration: none;">{APP_URL}</a>
                            </span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""


def _send(to: str, subject: str, html: str) -> bool:
    """Envoie un email via Resend. Retourne True si succès."""
    if not _is_configured():
        logger.warning("Resend non configuré — email non envoyé à %s", to)
        return False

    try:
        result = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        logger.info("Email envoyé à %s — id=%s", to, result.get("id", "?"))
        return True
    except Exception as e:
        logger.error("Erreur envoi email à %s : %s", to, e)
        return False


# EMAIL 1 : BIENVENUE (après inscription)

def send_welcome_email(email: str, company_name: Optional[str] = None) -> bool:
    """Envoie l'email de bienvenue après inscription."""
    greeting = f"pour <strong>{company_name}</strong>" if company_name else ""

    content = f"""
    <h2 style="color: {DARK}; margin: 0 0 16px 0; font-size: 22px;">
        Bienvenue sur ESG Optimizer !
    </h2>
    <p style="color: {GRAY}; font-size: 15px; line-height: 1.6; margin: 0 0 16px 0;">
        Votre compte a été créé avec succès {greeting}.
        Vous avez <strong>1 analyse ESG gratuite</strong> pour découvrir notre plateforme.
    </p>
    <p style="color: {GRAY}; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
        Uploadez votre rapport de durabilité et obtenez en quelques minutes :
    </p>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px 0;">
        <tr>
            <td style="padding: 8px 0; color: {DARK}; font-size: 14px;">
                ✅ Scores E / S / G détaillés (0-100)
            </td>
        </tr>
        <tr>
            <td style="padding: 8px 0; color: {DARK}; font-size: 14px;">
                ✅ Conformité CSRD et couverture ESRS
            </td>
        </tr>
        <tr>
            <td style="padding: 8px 0; color: {DARK}; font-size: 14px;">
                ✅ KPIs détectés et recommandations priorisées
            </td>
        </tr>
        <tr>
            <td style="padding: 8px 0; color: {DARK}; font-size: 14px;">
                ✅ Synthèse exécutive prête à partager
            </td>
        </tr>
    </table>
    <div style="text-align: center; margin: 24px 0;">
        <a href="{APP_URL}" style="display: inline-block; background: {GREEN}; color: #FFFFFF;
           font-weight: 700; font-size: 16px; padding: 14px 32px; border-radius: 8px;
           text-decoration: none;">
            Lancer mon analyse gratuite
        </a>
    </div>
    <p style="color: #9CA3AF; font-size: 12px; margin-top: 24px;">
        Des questions ? Répondez directement à cet email, nous vous répondrons rapidement.
    </p>
    """

    html = _base_template("Bienvenue sur ESG Optimizer", content)
    return _send(email, "Bienvenue sur ESG Optimizer — Votre analyse ESG gratuite vous attend", html)


# EMAIL 2 : ANALYSE TERMINÉE

def send_analysis_complete_email(
    email: str,
    analysis_id: int,
    company_name: str,
    score_global: float,
    csrd_ready: bool,
    report_year: Optional[int] = None,
) -> bool:
    """Envoie l'email de notification quand une analyse est terminée."""
    csrd_badge = (
        '<span style="background: #D4F0D8; color: #1A3D22; padding: 4px 12px; '
        'border-radius: 8px; font-size: 13px; font-weight: 600;">CSRD Ready ✓</span>'
        if csrd_ready else
        '<span style="background: #FEE2E2; color: #DC2626; padding: 4px 12px; '
        'border-radius: 8px; font-size: 13px; font-weight: 600;">Non conforme CSRD ✗</span>'
    )

    score_color = GREEN if score_global >= 60 else "#F59E0B" if score_global >= 40 else "#EF4444"
    year_text = f" ({report_year})" if report_year else ""

    content = f"""
    <h2 style="color: {DARK}; margin: 0 0 16px 0; font-size: 22px;">
        Votre analyse ESG est prête !
    </h2>
    <p style="color: {GRAY}; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
        L'analyse du rapport de <strong>{company_name}</strong>{year_text} est terminée.
        Voici un aperçu de vos résultats :
    </p>

    <!-- Score card -->
    <table width="100%" cellpadding="0" cellspacing="0"
           style="background: {LIGHT_BG}; border: 1px solid #E5E7EB; border-radius: 12px;
                  margin: 0 0 24px 0; overflow: hidden;">
        <tr>
            <td style="padding: 24px; text-align: center;">
                <div style="font-size: 48px; font-weight: 800; color: {score_color};">
                    {int(score_global)}<span style="font-size: 18px; color: #9CA3AF;">/100</span>
                </div>
                <div style="font-weight: 600; font-size: 16px; color: {DARK}; margin-top: 4px;">
                    {company_name}
                </div>
                <div style="margin-top: 12px;">
                    {csrd_badge}
                </div>
            </td>
        </tr>
    </table>

    <div style="text-align: center; margin: 24px 0;">
        <a href="{APP_URL}" style="display: inline-block; background: {GREEN}; color: #FFFFFF;
           font-weight: 700; font-size: 16px; padding: 14px 32px; border-radius: 8px;
           text-decoration: none;">
            Voir les résultats complets
        </a>
    </div>

    <p style="color: {GRAY}; font-size: 13px; line-height: 1.6; margin-top: 16px;">
        Consultez le détail de vos scores E/S/G, la couverture ESRS,
        les KPIs détectés et les recommandations priorisées dans votre tableau de bord.
    </p>
    """

    html = _base_template(f"Analyse ESG terminée — {company_name}", content)
    subject = f"Votre analyse ESG est prête — {company_name} : {int(score_global)}/100"
    return _send(email, subject, html)


# EMAIL 3 : ANALYSE ÉCHOUÉE

def send_analysis_failed_email(
    email: str,
    analysis_id: int,
    company_name: str,
    error_message: Optional[str] = None,
) -> bool:
    """Envoie un email si l'analyse a échoué."""
    error_text = f"<em>{error_message}</em>" if error_message else "Une erreur inattendue s'est produite."

    content = f"""
    <h2 style="color: {DARK}; margin: 0 0 16px 0; font-size: 22px;">
        Problème avec votre analyse
    </h2>
    <p style="color: {GRAY}; font-size: 15px; line-height: 1.6; margin: 0 0 16px 0;">
        L'analyse du rapport de <strong>{company_name}</strong> n'a pas pu aboutir.
    </p>
    <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px;
         padding: 16px; margin: 0 0 20px 0;">
        <p style="color: #991B1B; font-size: 14px; margin: 0;">
            {error_text}
        </p>
    </div>
    <p style="color: {GRAY}; font-size: 14px; line-height: 1.6;">
        Cela peut arriver si le fichier est corrompu, protégé par mot de passe,
        ou ne contient pas assez de texte exploitable.
        Essayez avec un autre format (PDF, DOCX, XLSX) ou répondez à cet email pour obtenir de l'aide.
    </p>
    <div style="text-align: center; margin: 24px 0;">
        <a href="{APP_URL}" style="display: inline-block; background: {GREEN}; color: #FFFFFF;
           font-weight: 700; font-size: 14px; padding: 12px 28px; border-radius: 8px;
           text-decoration: none;">
            Réessayer une analyse
        </a>
    </div>
    """

    html = _base_template(f"Problème avec votre analyse — {company_name}", content)
    return _send(email, f"Problème avec votre analyse ESG — {company_name}", html)


# EMAIL 4 : WEEKLY DIGEST

def send_weekly_digest_email(
    email: str,
    total_analyses: int,
    avg_score: Optional[float],
    csrd_ready_pct: Optional[float],
    latest_analyses: list[dict],
) -> bool:
    """Envoie le digest hebdomadaire avec un résumé des analyses."""
    avg_text = f"{avg_score:.0f}/100" if avg_score else "—"
    csrd_text = f"{csrd_ready_pct:.0f}%" if csrd_ready_pct is not None else "—"

    # Lignes du tableau des dernières analyses
    rows_html = ""
    for a in latest_analyses[:5]:
        name = a.get("company_name", "?")
        score = a.get("score_global")
        score_str = f"{score:.0f}" if score else "—"
        csrd = "✓" if a.get("csrd_ready") else "✗"
        rows_html += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #F3F4F6; font-size: 13px; color: {DARK};">{name}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #F3F4F6; font-size: 13px; color: {DARK}; text-align: center;">{score_str}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #F3F4F6; font-size: 13px; text-align: center;">{csrd}</td>
        </tr>"""

    content = f"""
    <h2 style="color: {DARK}; margin: 0 0 16px 0; font-size: 22px;">
        Votre résumé ESG hebdomadaire
    </h2>

    <!-- KPI cards -->
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 0 0 24px 0;">
        <tr>
            <td width="33%" style="text-align: center; padding: 16px; background: #EFF6FF; border-radius: 8px;">
                <div style="font-size: 28px; font-weight: 800; color: #2563EB;">{total_analyses}</div>
                <div style="font-size: 12px; color: {GRAY}; margin-top: 4px;">Analyses total</div>
            </td>
            <td width="5%"></td>
            <td width="29%" style="text-align: center; padding: 16px; background: #F0FDF4; border-radius: 8px;">
                <div style="font-size: 28px; font-weight: 800; color: {GREEN};">{avg_text}</div>
                <div style="font-size: 12px; color: {GRAY}; margin-top: 4px;">Score moyen</div>
            </td>
            <td width="5%"></td>
            <td width="28%" style="text-align: center; padding: 16px; background: #FFF7ED; border-radius: 8px;">
                <div style="font-size: 28px; font-weight: 800; color: #EA580C;">{csrd_text}</div>
                <div style="font-size: 12px; color: {GRAY}; margin-top: 4px;">CSRD Ready</div>
            </td>
        </tr>
    </table>

    <!-- Dernières analyses -->
    {"<h3 style='color: " + DARK + "; font-size: 16px; margin: 0 0 12px 0;'>Dernières analyses</h3>" + '''
    <table width="100%" cellpadding="0" cellspacing="0" style="border: 1px solid #E5E7EB; border-radius: 8px; overflow: hidden;">
        <tr style="background: #F9FAFB;">
            <th style="padding: 10px 12px; text-align: left; font-size: 12px; color: ''' + GRAY + '''; font-weight: 600;">Entreprise</th>
            <th style="padding: 10px 12px; text-align: center; font-size: 12px; color: ''' + GRAY + '''; font-weight: 600;">Score</th>
            <th style="padding: 10px 12px; text-align: center; font-size: 12px; color: ''' + GRAY + '''; font-weight: 600;">CSRD</th>
        </tr>''' + rows_html + "</table>" if latest_analyses else "<p style='color: #9CA3AF; font-size: 13px;'>Aucune analyse cette semaine.</p>"}

    <div style="text-align: center; margin: 28px 0 8px 0;">
        <a href="{APP_URL}" style="display: inline-block; background: {GREEN}; color: #FFFFFF;
           font-weight: 700; font-size: 14px; padding: 12px 28px; border-radius: 8px;
           text-decoration: none;">
            Voir mon tableau de bord
        </a>
    </div>
    """

    html = _base_template("Résumé ESG hebdomadaire", content)
    return _send(email, "Votre résumé ESG de la semaine", html)


# EMAIL 5 : UPGRADE CONFIRMATION

def send_upgrade_confirmation_email(email: str, plan: str, amount_display: str) -> bool:
    """Envoie un email de confirmation après upgrade de plan."""
    plan_display = {"essential": "Essentiel", "pro": "Pro", "enterprise": "Enterprise"}.get(plan, plan)

    content = f"""
    <h2 style="color: {DARK}; margin: 0 0 16px 0; font-size: 22px;">
        Bienvenue dans le plan {plan_display} !
    </h2>
    <p style="color: {GRAY}; font-size: 15px; line-height: 1.6; margin: 0 0 16px 0;">
        Votre paiement de <strong>{amount_display}</strong> a été confirmé.
        Votre compte est désormais sur le plan <strong>{plan_display}</strong>.
    </p>
    <div style="background: #D4F0D8; border: 1px solid #7FC686; border-radius: 8px;
         padding: 16px; margin: 0 0 20px 0; text-align: center;">
        <span style="font-size: 14px; font-weight: 600; color: #1A3D22;">
            Plan {plan_display} activé ✓
        </span>
    </div>
    <div style="text-align: center; margin: 24px 0;">
        <a href="{APP_URL}" style="display: inline-block; background: {GREEN}; color: #FFFFFF;
           font-weight: 700; font-size: 16px; padding: 14px 32px; border-radius: 8px;
           text-decoration: none;">
            Lancer une analyse
        </a>
    </div>
    """

    html = _base_template(f"Plan {plan_display} activé", content)
    return _send(email, f"Plan {plan_display} activé — ESG Optimizer", html)
