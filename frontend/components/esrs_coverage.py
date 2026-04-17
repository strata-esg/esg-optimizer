"""
ESG Optimizer MVP — Composant grille de couverture ESRS.
Affiche les 10 catégories ESRS avec indicateur visuel couvert/non couvert.
"""

import streamlit as st


# Labels humains pour chaque catégorie ESRS
ESRS_LABELS = {
    "E1_climate_change": ("E1", "Changement climatique"),
    "E2_pollution": ("E2", "Pollution"),
    "E3_water_marine": ("E3", "Eau & ressources marines"),
    "E4_biodiversity": ("E4", "Biodiversité & écosystèmes"),
    "E5_circular_economy": ("E5", "Économie circulaire"),
    "S1_own_workforce": ("S1", "Effectifs propres"),
    "S2_value_chain_workers": ("S2", "Travailleurs chaîne valeur"),
    "S3_affected_communities": ("S3", "Communautés affectées"),
    "S4_consumers": ("S4", "Consommateurs & utilisateurs"),
    "G1_business_conduct": ("G1", "Conduite des affaires"),
}


def render_esrs_grid(esrs_coverage: dict | None) -> None:
    """
    Affiche une grille colorée des 10 catégories ESRS.
    Vert = couvert, Rouge = manquant.

    Args:
        esrs_coverage: dict type {"E1_climate_change": True, "E2_pollution": False, ...}
                       Si None, affiche tout en gris.
    """
    if esrs_coverage is None:
        st.info("Aucune donnée de couverture ESRS disponible.")
        return

    st.subheader("Couverture ESRS")

    covered = sum(1 for v in esrs_coverage.values() if v)
    total = len(ESRS_LABELS)
    pct = (covered / total * 100) if total > 0 else 0

    st.caption(f"{covered}/{total} catégories couvertes ({pct:.0f}%)")

    # Grille : 5 colonnes x 2 lignes
    keys = list(ESRS_LABELS.keys())

    for row_start in range(0, len(keys), 5):
        cols = st.columns(5)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx >= len(keys):
                break
            key = keys[idx]
            code, label = ESRS_LABELS[key]
            is_covered = esrs_coverage.get(key, False)

            with col:
                if is_covered:
                    st.markdown(
                        f"""<div style="
                            background: #D1FAE5; border: 2px solid #10B981;
                            border-radius: 10px; padding: 12px 8px; text-align: center;
                            margin-bottom: 8px;">
                            <div style="font-weight: 700; color: #065F46; font-size: 18px;">{code}</div>
                            <div style="font-size: 11px; color: #065F46; margin-top: 4px;">{label}</div>
                            <div style="color: #10B981; font-size: 20px; margin-top: 4px;">&#10003;</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""<div style="
                            background: #FEE2E2; border: 2px solid #EF4444;
                            border-radius: 10px; padding: 12px 8px; text-align: center;
                            margin-bottom: 8px;">
                            <div style="font-weight: 700; color: #991B1B; font-size: 18px;">{code}</div>
                            <div style="font-size: 11px; color: #991B1B; margin-top: 4px;">{label}</div>
                            <div style="color: #EF4444; font-size: 20px; margin-top: 4px;">&#10007;</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
