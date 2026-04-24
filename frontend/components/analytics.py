"""
ESG Optimizer MVP - Composant analytics Umami.

Pourquoi components.html et pas st.markdown ?
Les navigateurs n'executent pas les scripts injectes via innerHTML.
st.markdown utilise ce mecanisme -> les scripts n'arrivent jamais a Umami.
Solution : components.html cree un iframe (meme origine) dont les scripts
s'executent et peuvent acceder a window.parent pour appeler Umami.

Configuration : UMAMI_WEBSITE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

Funnel de conversion (6 events) :
    1. cta_landing_click     - Clic CTA landing page
    2. quick_check_submit    - Soumission quick-check
    3. upload_started        - Debut upload (authentifie)
    4. analysis_completed    - Fin d'analyse succes
    5. pricing_plan_click    - Clic plan tarifaire
    6. payment_completed     - Paiement Stripe complete
"""

import os
import json
import streamlit.components.v1 as components

UMAMI_WEBSITE_ID = os.getenv("UMAMI_WEBSITE_ID", "")


def inject_analytics_script():
    """Injecte Umami dans le head de la page parente via window.parent."""
    if not UMAMI_WEBSITE_ID:
        return
    uid = UMAMI_WEBSITE_ID
    components.html(
        f"""<script>
(function(){{
    var p=window.parent;
    if(!p||!p.document)return;
    if(p.document.getElementById('_umami_sdk'))return;
    var s=p.document.createElement('script');
    s.id='_umami_sdk';
    s.src='https://cloud.umami.is/script.js';
    s.defer=true;
    s.setAttribute('data-website-id','{uid}');
    p.document.head.appendChild(s);
    if(typeof p.umami==='undefined'){{
        p._uq=p._uq||[];
        p.umami={{track:function(n,d){{p._uq.push({{name:n,data:d}});}}}};
        s.onload=function(){{
            (p._uq||[]).forEach(function(e){{
                if(p.umami&&p.umami.track)p.umami.track(e.name,e.data);
            }});
            p._uq=[];
        }};
    }}
}})();
</script>""",
        height=0,
    )


inject_umami_script = inject_analytics_script


def track_event(event_name, data=None):
    """Envoie un event a Umami via window.parent."""
    if not UMAMI_WEBSITE_ID:
        return
    data_js = json.dumps(data) if data else "undefined"
    name_safe = event_name.replace("'", "\\'")
    components.html(
        f"""<script>
(function(){{
    var p=window.parent;
    if(!p)return;
    var r=0;
    function fire(){{
        if(p.umami&&typeof p.umami.track==='function'){{
            p.umami.track('{name_safe}',{data_js});
        }}else if(r++<15){{
            setTimeout(fire,400);
        }}
    }}
    fire();
}})();
</script>""",
        height=0,
    )


# ── 6 events du funnel ──────────────────────────────────────────────────────

def track_cta_landing_click(cta_label="unknown", source="landing"):
    """1. Clic CTA landing page."""
    track_event("cta_landing_click", {"cta_label": cta_label, "source": source})


def track_quick_check_submit(filename=None):
    """2. Soumission quick-check."""
    data = {}
    if filename and "." in filename:
        data["format"] = filename.rsplit(".", 1)[-1].lower()
    track_event("quick_check_submit", data or None)


def track_upload_started(company_name=None, sector=None):
    """3. Debut upload (authentifie)."""
    data = {}
    if sector:
        data["sector"] = sector
    track_event("upload_started", data or None)


def track_analysis_completed(score=None, plan=None):
    """4. Fin d'analyse avec succes."""
    data = {}
    if score is not None:
        data["score_global"] = round(float(score), 1)
        data["score_tier"] = "high" if score >= 70 else ("medium" if score >= 40 else "low")
    if plan:
        data["plan"] = plan
    track_event("analysis_completed", data or None)


def track_pricing_plan_click(plan, source="pricing_page"):
    """5. Clic plan tarifaire."""
    track_event("pricing_plan_click", {"plan": plan, "source": source})


def track_payment_completed(plan):
    """6. Paiement Stripe complete."""
    track_event("payment_completed", {"plan": plan})


# ── Legacy (retro-compat) ────────────────────────────────────────────────────

def track_landing_view(persona=None):
    track_event("landing_view", {"persona": persona} if persona else None)

def track_quick_check_started():
    track_event("quick_check_submit")

def track_quick_check_completed(score=None):
    track_event("quick_check_completed", {"score": score} if score is not None else None)

def track_signup_started(source="direct"):
    track_event("signup_started", {"source": source})

def track_signup_completed(source="direct"):
    track_event("signup_completed", {"source": source})

def track_first_analysis_completed(score=None):
    track_analysis_completed(score)

def track_pricing_viewed(persona=None):
    track_event("pricing_viewed", {"persona": persona} if persona else None)

def track_upgrade_clicked(plan="pro"):
    track_pricing_plan_click(plan, source="legacy")
