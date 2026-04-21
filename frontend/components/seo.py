"""
frontend/components/seo.py — Injection des meta tags SEO/OpenGraph (Sprint 6H).

Streamlit ne supporte pas nativement les meta tags dans <head> : on utilise
`st.markdown(..., unsafe_allow_html=True)` avec un petit hack JS pour injecter
dynamiquement dans le document HEAD au load de la page.

Usage (à appeler en tout début de chaque page, juste après st.set_page_config) :

    from frontend.components.seo import inject_seo

    inject_seo(
        page_title="Analyse CSRD automatique en 3 minutes — ESG Optimizer",
        description="Conformité CSRD/ESRS évaluée par IA. Rapport audit-ready en 3 min.",
        path="/",  # slug de la page pour l'URL canonique
    )
"""

from __future__ import annotations

import streamlit as st

APP_URL = "https://esg-optimizer.fr"
DEFAULT_OG_IMAGE = f"{APP_URL}/static/og-image.png"  # badge générique 1200x630


def inject_seo(
    page_title: str,
    description: str,
    path: str = "/",
    og_image: str | None = None,
    twitter_card: str = "summary_large_image",
    robots: str = "index,follow",
) -> None:
    """Injecte meta title, description, OpenGraph, Twitter Card, canonical."""
    canonical = f"{APP_URL.rstrip('/')}{path}"
    image = og_image or DEFAULT_OG_IMAGE

    # Caractères spéciaux à échapper pour éviter la casse des attributs HTML
    def _esc(s: str) -> str:
        return (
            s.replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    title_esc = _esc(page_title)
    desc_esc = _esc(description)

    html = f"""
    <script>
    (function() {{
      const head = document.head;
      if (!head) return;

      // Nettoie les anciennes balises injectées (évite doublons lors des reruns)
      document.querySelectorAll('meta[data-esg-seo], link[data-esg-seo]').forEach(el => el.remove());

      function add(tag, attrs) {{
        const el = document.createElement(tag);
        Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
        el.setAttribute('data-esg-seo', '1');
        head.appendChild(el);
      }}

      // Title
      document.title = "{title_esc}";

      // Meta classiques
      add('meta', {{ name: 'description', content: "{desc_esc}" }});
      add('meta', {{ name: 'robots',      content: "{robots}" }});
      add('meta', {{ name: 'viewport',    content: 'width=device-width, initial-scale=1' }});

      // Canonical
      add('link', {{ rel: 'canonical', href: "{canonical}" }});

      // OpenGraph
      add('meta', {{ property: 'og:title',       content: "{title_esc}" }});
      add('meta', {{ property: 'og:description', content: "{desc_esc}" }});
      add('meta', {{ property: 'og:url',         content: "{canonical}" }});
      add('meta', {{ property: 'og:image',       content: "{image}" }});
      add('meta', {{ property: 'og:type',        content: 'website' }});
      add('meta', {{ property: 'og:site_name',   content: 'ESG Optimizer' }});
      add('meta', {{ property: 'og:locale',      content: 'fr_FR' }});

      // Twitter
      add('meta', {{ name: 'twitter:card',        content: "{twitter_card}" }});
      add('meta', {{ name: 'twitter:title',       content: "{title_esc}" }});
      add('meta', {{ name: 'twitter:description', content: "{desc_esc}" }});
      add('meta', {{ name: 'twitter:image',       content: "{image}" }});

      // Schema.org SoftwareApplication (rich snippet Google)
      const ld = document.createElement('script');
      ld.setAttribute('type', 'application/ld+json');
      ld.setAttribute('data-esg-seo', '1');
      ld.textContent = JSON.stringify({{
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "ESG Optimizer",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "description": "{desc_esc}",
        "url": "{APP_URL}",
        "offers": {{
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "EUR",
          "description": "Plan Découverte gratuit, puis 39 €/analyse ou 129 €/mois"
        }}
      }});
      head.appendChild(ld);
    }})();
    </script>
    """
    st.markdown(html, unsafe_allow_html=True)


# --- Presets par page -------------------------------------------------
SEO_PRESETS = {
    "landing": {
        "page_title": "ESG Optimizer — Analyse CSRD automatique en 3 minutes",
        "description": "Analyse de conformité CSRD/ESRS par IA. Score ESG, rapport audit-ready, delta annuel. De 0€ à 129€/mois. Démarrez gratuitement.",
        "path": "/",
    },
    "quick_check": {
        "page_title": "Quick-check ESG gratuit — Score CSRD en 60 secondes",
        "description": "Testez gratuitement la conformité CSRD de votre rapport. Score instantané sur les 12 ESRS. Aucune inscription requise.",
        "path": "/quick-check",
    },
    # --- AJOUTS POUR LES PAGES D'APPLICATION ---
    "upload": {
        "page_title": "Nouvelle Analyse — ESG Optimizer",
        "description": "Uploadez votre rapport de durabilité pour lancer une analyse complète assistée par IA.",
        "path": "/upload",
    },
    "results": {
        "page_title": "Résultats de l'analyse — ESG Optimizer",
        "description": "Détails de votre score ESG, couverture ESRS et recommandations stratégiques.",
        "path": "/resultats",
    },
    "dashboard": {
        "page_title": "Tableau de Bord — ESG Optimizer",
        "description": "Suivez l'évolution de vos scores ESG et gérez vos rapports d'analyse.",
        "path": "/dashboard",
    },
    # --------------------------------------------
    "pricing": {
        "page_title": "Tarifs ESG Optimizer — de 0€ à 129€/mois",
        "description": "4 plans pour tous les profils : PME one-shot à 39€, consultants à 129€/mois, Enterprise sur devis. Sans engagement.",
        "path": "/pricing",
    },
    "methodologie": {
        "page_title": "Méthodologie ESG Optimizer — GHG Protocol, SBTi, EFRAG, TCFD",
        "description": "Notre scoring ESG s'appuie sur les standards GHG Protocol, SBTi, EFRAG ESRS et TCFD. Transparence totale sur la méthode.",
        "path": "/methodologie",
    },
    "rgpd": {
        "page_title": "RGPD & DPA — ESG Optimizer",
        "description": "Hébergement UE, sous-traitants DPA-signés, droit à l'effacement, export des données. 100% conforme RGPD.",
        "path": "/rgpd",
        "robots": "index,follow",
    },
}


def seo_for(page_key: str, **overrides) -> None:
    """Raccourci : inject_seo(**SEO_PRESETS[page_key], **overrides)."""
    cfg = {**SEO_PRESETS[page_key], **overrides}
    inject_seo(**cfg)
