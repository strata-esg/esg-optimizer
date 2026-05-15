"""
ESG Optimizer MVP - Page Mentions légales, CGU, Confidentialité, Méthodologie.
Page publique, accessible sans connexion.
"""

import sys
from pathlib import Path

import streamlit as st

try:
    from frontend.components.seo import seo_for
    seo_for("legal")
except KeyError:
    # Si 'legal' n'existe pas encore dans SEO_PRESETS, on ne fait rien ou on utilise default
    pass 

# Path setup
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Header
st.markdown(
    """
    <div style="padding: 2rem 0 1rem 0;">
        <h1 style="margin-bottom: 0.25rem;">Documents légaux & Méthodologie</h1>
        <p style="color: #6B7280; font-size: 0.95rem; margin-top: 0;">
            ESG Optimizer · <a href="mailto:hello@esg-optimizer.fr"
            style="color:#1A3D22;">hello@esg-optimizer.fr</a>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs([
    "Mentions légales",
    "CGU",
    "Confidentialité",
    "Méthodologie",
])


# Onglet 1 - Mentions légales
with tab1:
    st.markdown("""
## Mentions légales

**Éditeur du service**

ESG Optimizer - Entreprise individuelle
Représentant légal : Adama
Email : [hello@esg-optimizer.fr](mailto:hello@esg-optimizer.fr)

**Hébergement**

Le service est hébergé sur Railway (Railway Corp., San Francisco, CA, USA).
Les données sont stockées dans des datacenters conformes aux standards SOC 2.

**Propriété intellectuelle**

L'ensemble du contenu de ce site (textes, rapports générés, visuels, code) est
la propriété exclusive d'ESG Optimizer, sauf mention contraire. Toute reproduction
ou représentation, intégrale ou partielle, est interdite sans autorisation préalable.

**Responsabilité**

ESG Optimizer met tout en œuvre pour assurer l'exactitude des analyses générées par
intelligence artificielle. Cependant, les résultats fournis ont une vocation
indicative et ne constituent pas un audit certifié au sens du référentiel CSRD.
L'utilisateur reste seul responsable des décisions prises sur la base de ces analyses.

**Contact**

Pour toute question relative au service : [hello@esg-optimizer.fr](mailto:hello@esg-optimizer.fr)
""")


# Onglet 2 - CGU
with tab2:
    st.markdown("""
## Conditions Générales d'Utilisation

*Dernière mise à jour : avril 2026*

### 1. Objet

Les présentes Conditions Générales d'Utilisation (CGU) régissent l'accès et
l'utilisation de la plateforme ESG Optimizer, accessible à l'adresse
[esg-optimizer.fr](https://esg-optimizer.fr).

### 2. Accès au service

L'accès au service requiert la création d'un compte utilisateur. L'utilisateur
s'engage à fournir des informations exactes lors de son inscription et à maintenir
la confidentialité de ses identifiants.

### 3. Plans et tarifs

Le service est proposé selon quatre formules :
- **Découverte (0 €)** : 1 analyse gratuite avec rapport partiel (3 pages sur 8)
- **Essentiel (39 € / analyse)** : rapport complet, delta annuel inclus
- **Pro (129 € / mois ou 990 € / an)** : analyses illimitées, benchmark sectoriel, white-label
- **Enterprise** : tarif sur devis, SSO, multi-utilisateurs, API, SLA

Les tarifs s'entendent HT. La TVA applicable est celle en vigueur au moment de l'achat.

### 4. Utilisation acceptable

L'utilisateur s'engage à utiliser ESG Optimizer uniquement pour analyser des
documents de durabilité légitimes. Il est interdit de :
- Tenter de contourner les limitations de quota
- Soumettre des documents contenant des données personnelles de tiers non consenties
- Utiliser le service à des fins de désinformation ou de manipulation de données ESG

### 5. Disponibilité du service

ESG Optimizer vise une disponibilité de 99 % hors maintenance planifiée.
Aucune garantie de disponibilité n'est fournie sur le plan Découverte.

### 6. Résiliation

L'utilisateur peut résilier son compte à tout moment depuis les Paramètres.
Les analyses conservées seront supprimées dans un délai de 30 jours après résiliation.

### 7. Droit applicable

Les présentes CGU sont soumises au droit français. En cas de litige, les parties
chercheront d'abord une résolution amiable avant tout recours judiciaire.
""")


# Onglet 3 - Confidentialité
with tab3:
    st.markdown("""
## Politique de Confidentialité (RGPD)

*Dernière mise à jour : avril 2026*

### Responsable de traitement

ESG Optimizer · Email : [hello@esg-optimizer.fr](mailto:hello@esg-optimizer.fr)

### Données collectées

| Donnée | Finalité | Base légale | Durée de conservation |
|---|---|---|---|
| Email + mot de passe hashé | Authentification | Contrat | Durée du compte + 30 j |
| Rapports uploadés | Analyse ESG | Contrat | 12 mois (plan Essentiel+) |
| Résultats d'analyse | Historique utilisateur | Contrat | 12 mois |
| Logs de connexion | Sécurité | Intérêt légitime | 90 jours |
| Analytics anonymes (Plausible) | Amélioration du service | Intérêt légitime | Agrégats - pas de données perso |

### Données non collectées

ESG Optimizer ne collecte **aucune** donnée personnelle sensible au sens de l'article 9
du RGPD. Les documents uploadés sont traités par l'API OpenAI (GPT-4o) conformément
à la politique de traitement des données d'Anthropic/OpenAI, qui n'utilise pas les
données des clients API pour entraîner ses modèles.

### Vos droits

Conformément au RGPD, vous disposez des droits suivants :
- **Accès** : obtenir une copie de vos données
- **Rectification** : corriger des données inexactes
- **Effacement** : supprimer votre compte et vos données
- **Portabilité** : exporter vos analyses au format JSON

Pour exercer ces droits : [hello@esg-optimizer.fr](mailto:hello@esg-optimizer.fr)

Vous pouvez également introduire une réclamation auprès de la **CNIL**
(Commission Nationale de l'Informatique et des Libertés) : [cnil.fr](https://www.cnil.fr)

### Cookies

ESG Optimizer utilise uniquement des cookies fonctionnels (session utilisateur).
Aucun cookie publicitaire ou de tracking tiers n'est déposé. L'analytics est
réalisé via Plausible, solution sans cookies conforme RGPD.
""")


# Onglet 4 - Méthodologie
with tab4:
    st.markdown("""
## Méthodologie d'analyse ESG Optimizer

*Version 1.0 - Avril 2026*

---

### Modèle d'analyse

ESG Optimizer utilise **GPT-4o** (OpenAI), le modèle de référence pour la
compréhension de textes longs et structurés. Chaque rapport soumis est traité
en deux passes successives :

1. **Extraction** : conversion du document (PDF, DOCX, XLSX) en texte structuré,
   préservant les tableaux et les données chiffrées
2. **Analyse** : évaluation de la couverture des exigences CSRD selon le référentiel ESRS

---

### Référentiel utilisé : ESRS (European Sustainability Reporting Standards)

L'analyse est calquée sur les **12 standards ESRS** publiés par l'EFRAG en 2023 :

| Standard | Domaine |
|---|---|
| ESRS 1 | Exigences générales |
| ESRS 2 | Informations générales |
| ESRS E1 | Changement climatique |
| ESRS E2 | Pollution |
| ESRS E3 | Eau et ressources marines |
| ESRS E4 | Biodiversité et écosystèmes |
| ESRS E5 | Utilisation des ressources et économie circulaire |
| ESRS S1 | Effectifs de l'entreprise |
| ESRS S2 | Travailleurs de la chaîne de valeur |
| ESRS S3 | Communautés affectées |
| ESRS S4 | Consommateurs et utilisateurs finaux |
| ESRS G1 | Conduite des affaires |

---

### Calcul des scores

Chaque dimension (E, S, G) reçoit un score de **0 à 100** calculé selon :

- **Présence des divulgations requises** : les exigences obligatoires ESRS 1 & 2
  comptent pour 40 % du score global
- **Couverture des standards thématiques** : les 10 standards E/S/G pour 60 %
- **Qualité des données** : pénalités appliquées en l'absence de données chiffrées
  vérifiables (vs. déclarations qualitatives seules)

**Grille d'interprétation :**

| Score | Signification |
|---|---|
| 80 - 100 | Couverture CSRD solide - rapport prêt pour publication |
| 60 - 79 | Couverture partielle - lacunes identifiées à corriger |
| 40 - 59 | Couverture minimale - travail significatif requis |
| 0 - 39 | Non conforme - rapport à retravailler en profondeur |

---

### Delta Report

Le Delta Report compare deux rapports annuels de la même entreprise.
Il identifie :
- Les **progrès réels** (score en hausse + nouvelles divulgations)
- Les **régressions** (données présentes l'année N-1 mais absentes en N)
- Les **écarts de périmètre** (nouvelles entités consolidées)

---

### Limites de l'analyse automatique

ESG Optimizer est un outil d'**aide à la décision**, pas un auditeur certifié.

1. L'analyse repose sur le texte extrait du document - les graphiques et tableaux
   en image ne sont pas analysés
2. La pertinence des divulgations (double matérialité) n'est pas évaluée
3. Les rapports très longs (>200 pages) peuvent être tronqués à 30 000 caractères
4. Le modèle peut faire des erreurs d'interprétation sur des formulations ambiguës

**Pour un audit certifié CSRD**, nous vous recommandons de faire appel à un
Organisme Tiers Indépendant (OTI) accrédité par le COFRAC.

---

### Questions sur la méthodologie ?

[hello@esg-optimizer.fr](mailto:hello@esg-optimizer.fr)
""")

    # Badge méthodologie
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align:center; padding: 1.5rem;
                        background: #F5F2EC; border-radius: 12px;
                        border: 1px solid #E5E0D8;">
                <div style="font-family:'DM Serif Display',Georgia,serif;
                            font-size:1.1rem; color:#1A3D22; margin-bottom:8px;">
                    Référentiel ESRS - EFRAG 2023
                </div>
                <div style="font-size:0.82rem; color:#6B7280; line-height:1.6;">
                    Notre scoring est aligné sur les standards publiés par<br>
                    l'EFRAG (European Financial Reporting Advisory Group)<br>
                    et entrés en vigueur le 1er janvier 2024.
                </div>
                <div style="margin-top:12px;">
                    <a href="https://www.efrag.org/en/projects/esrs-set-1-standards"
                       target="_blank"
                       style="color:#1A3D22; font-size:0.82rem;
                              text-decoration:underline;">
                        Consulter les standards officiels ->
                    </a>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
