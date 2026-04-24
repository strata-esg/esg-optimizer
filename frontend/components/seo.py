"""
frontend/components/seo.py - Injection meta tags SEO/OpenGraph.

Utilise components.html + window.parent (meme technique qu'Umami) pour
injecter les balises dans le head reel de la page. Les crawlers JS-capable
(Google, Slack, Discord, Telegram) les voient. WhatsApp/LinkedIn lisent
le HTML brut de Streamlit (limitation sans reverse-proxy).
"""

from __future__ import annotations
import streamlit.components.v1 as components

APP_URL = "https://esg-optimizer.fr"
APP_NAME = "ESG Optimizer"
DEFAULT_OG_IMAGE = f"{APP_URL}/static/og-image.png"


def inject_seo(
    page_title: str,
    description: str,
    path: str = "/",
    og_image: str | None = None,
    twitter_card: str = "summary_large_image",
    robots: str = "index,follow",
) -> None:
    """Injecte title, description, OG, Twitter Card, canonical via window.parent."""
    canonical = f"{APP_URL.rstrip('/')}{path}"
    image = og_image or DEFAULT_OG_IMAGE

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ").replace("\r", "")

    t = esc(page_title)
    d = esc(description)
    img = esc(image)
    can = esc(canonical)
    an = esc(APP_NAME)

    schema = (
        '{"@context":"https://schema.org","@type":"SoftwareApplication",'
        f'"name":"{an}","applicationCategory":"BusinessApplication",'
        '"operatingSystem":"Web",'
        f'"description":"{d}","url":"{APP_URL}",'
        '"offers":{"@type":"Offer","price":"0","priceCurrency":"EUR",'
        '"description":"Plan Decouverte gratuit, puis 39 euros/analyse ou 129 euros/mois"}'
        "}"
    )

    components.html(
        f"""<script>
(function(){{
    var p=window.parent;
    if(!p||!p.document)return;
    var head=p.document.head;
    if(!head)return;
    p.document.querySelectorAll('[data-esg-seo]').forEach(function(el){{el.remove();}});
    function meta(attrs){{
        var el=p.document.createElement('meta');
        Object.keys(attrs).forEach(function(k){{el.setAttribute(k,attrs[k]);}});
        el.setAttribute('data-esg-seo','1');
        head.appendChild(el);
    }}
    function link(attrs){{
        var el=p.document.createElement('link');
        Object.keys(attrs).forEach(function(k){{el.setAttribute(k,attrs[k]);}});
        el.setAttribute('data-esg-seo','1');
        head.appendChild(el);
    }}
    p.document.title='{t}';
    meta({{name:'description',content:'{d}'}});
    meta({{name:'robots',content:'{robots}'}});
    link({{rel:'canonical',href:'{can}'}});
    meta({{property:'og:title',content:'{t}'}});
    meta({{property:'og:description',content:'{d}'}});
    meta({{property:'og:url',content:'{can}'}});
    meta({{property:'og:image',content:'{img}'}});
    meta({{property:'og:type',content:'website'}});
    meta({{property:'og:site_name',content:'{an}'}});
    meta({{property:'og:locale',content:'fr_FR'}});
    meta({{name:'twitter:card',content:'{twitter_card}'}});
    meta({{name:'twitter:title',content:'{t}'}});
    meta({{name:'twitter:description',content:'{d}'}});
    meta({{name:'twitter:image',content:'{img}'}});
    var ld=p.document.createElement('script');
    ld.type='application/ld+json';
    ld.setAttribute('data-esg-seo','1');
    ld.textContent='{schema}';
    head.appendChild(ld);
}})();
</script>""",
        height=0,
    )


SEO_PRESETS: dict[str, dict] = {
    "landing": {
        "page_title": "ESG Optimizer - Analyse CSRD automatique en 3 minutes",
        "description": "Analyse de conformite CSRD/ESRS par IA. Score ESG, rapport audit-ready, delta annuel. De 0 a 129 euros/mois. Demarrez gratuitement.",
        "path": "/",
    },
    "upload": {
        "page_title": "Nouvelle Analyse - ESG Optimizer",
        "description": "Uploadez votre rapport de durabilite pour lancer une analyse complete assistee par IA.",
        "path": "/upload",
    },
    "results": {
        "page_title": "Resultats de l'analyse - ESG Optimizer",
        "description": "Details de votre score ESG, couverture ESRS et recommandations strategiques.",
        "path": "/resultats",
    },
    "dashboard": {
        "page_title": "Tableau de Bord - ESG Optimizer",
        "description": "Suivez l'evolution de vos scores ESG et gerez vos rapports d'analyse.",
        "path": "/dashboard",
    },
    "pricing": {
        "page_title": "Tarifs ESG Optimizer - de 0 a 129 euros/mois",
        "description": "4 plans pour tous les profils : PME one-shot a 39 euros, consultants a 129 euros/mois, Enterprise sur devis. Sans engagement.",
        "path": "/pricing",
    },
    "login": {
        "page_title": "Connexion - ESG Optimizer",
        "description": "Connectez-vous ou creez votre compte gratuit pour analyser vos rapports de durabilite.",
        "path": "/login",
        "robots": "noindex,nofollow",
    },
    "methodologie": {
        "page_title": "Methodologie ESG Optimizer - GHG Protocol, SBTi, EFRAG, TCFD",
        "description": "Notre scoring s'appuie sur les standards GHG Protocol, SBTi, EFRAG ESRS et TCFD. Transparence totale.",
        "path": "/methodologie",
    },
}


def seo_for(page_key: str, **overrides) -> None:
    """Raccourci : inject_seo(**SEO_PRESETS[page_key], **overrides)."""
    cfg = {**SEO_PRESETS.get(page_key, SEO_PRESETS["landing"]), **overrides}
    inject_seo(**cfg)
