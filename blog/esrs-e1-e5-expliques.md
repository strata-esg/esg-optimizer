---
title: "ESRS E1 à E5 expliqués simplement : le guide environnemental complet"
slug: esrs-e1-e5-expliques
description: "Les 5 standards ESRS Environnement décodés sans jargon. Climat (E1), pollution (E2), eau (E3), biodiversité (E4), économie circulaire (E5)."
author: "Équipe ESG Optimizer"
date: 2026-04-20
category: "Réglementation"
tags: ["ESRS", "CSRD", "environnement", "climat", "biodiversité", "économie circulaire"]
og_image: "https://esg-optimizer.fr/static/blog/esrs-e1-e5.png"
canonical: "https://esg-optimizer.fr/blog/esrs-e1-e5-expliques"
reading_time: "14 min"
---

# ESRS E1 à E5 expliqués simplement : le guide environnemental complet

> **TL;DR** — Les 5 standards ESRS Environnement représentent 60 % du volume d'un rapport CSRD. Ce guide les explique sans jargon, donne les KPI clés à calculer et pointe les pièges qu'on voit le plus souvent dans les rapports.

Sur les 12 standards ESRS, 5 concernent l'environnement : **E1 Climat, E2 Pollution, E3 Eau, E4 Biodiversité, E5 Économie circulaire**. Chacun pèse lourd dans un rapport CSRD bien fait, et chacun a ses spécificités méthodologiques. Voici le guide que j'aurais aimé avoir quand j'ai démarré mon premier rapport.

---

## ESRS E1 — Changement climatique (le plus lourd)

### Ce que le standard exige

L'ESRS E1 est **de loin** le standard le plus détaillé (47 pages, 67 points de disclosure). Il couvre :

- **Plan de transition** vers la neutralité carbone : trajectoire 2030/2050, alignement 1.5°C
- **Inventaire GHG** selon le GHG Protocol : Scope 1 (émissions directes), Scope 2 (énergie achetée, en méthode location-based ET market-based), Scope 3 (15 catégories, identification des matérielles)
- **Risques et opportunités climatiques** : risques de transition (prix carbone, réglementation, marché), risques physiques (canicules, inondations, stress hydrique), sur 3 horizons temporels
- **Indicateurs financiers** : CapEx et OpEx alignés taxonomie verte, prix interne du carbone, impact sur les EBITDA
- **Politiques et actions** : mécanismes de gouvernance, ressources allouées, indicateurs de suivi

### Les 5 KPI à calculer absolument

| KPI | Unité | Source méthodo |
|---|---|---|
| Émissions Scope 1 | tCO2e | GHG Protocol Corporate Standard |
| Émissions Scope 2 (market + location based) | tCO2e | GHG Protocol Scope 2 Guidance |
| Émissions Scope 3 (par catégorie matérielle) | tCO2e | GHG Protocol Scope 3 Standard |
| Intensité carbone | tCO2e / M€ de CA | ESRS E1-6 §53 |
| % d'énergie renouvelable consommée | % | ESRS E1-5 §38 |

### Les 3 erreurs qu'on voit le plus

1. **Scope 2 en méthode location-based seulement** : l'ESRS demande explicitement les deux méthodes (location ET market based). Si vous achetez des certificats d'origine renouvelable, le market-based peut être très différent du location-based.
2. **Scope 3 catégorie 11 (utilisation des produits vendus) absent** pour des industriels dont c'est pourtant la catégorie dominante.
3. **Trajectoire exprimée en % de baisse sans baseline claire** : « -40 % d'ici 2030 » par rapport à quoi ? 2015 ? 2019 ? 2024 ? Précisez l'année de référence et le périmètre couvert.

> 💡 **Repère** — Pour une PME de services, Scope 3 pèse typiquement 70-85 % de l'empreinte totale. Pour un industriel, Scope 1+2 pèse souvent 50-70 %. Connaître ce ratio vous permet de prioriser les efforts de calcul.

---

## ESRS E2 — Pollution

### Ce que le standard exige

Bien moins connu que E1, l'ESRS E2 couvre :

- **Pollution atmosphérique** : NOx, SOx, particules fines, COV, composés persistants
- **Pollution de l'eau** : rejets industriels (DBO, DCO, métaux lourds, nitrates, phosphates, substances émergentes)
- **Pollution des sols** : sites contaminés, fuites, déversements
- **Substances préoccupantes** et **extrêmement préoccupantes** (SVHC au sens REACH) : volumes utilisés, rejetés, présents dans les produits vendus
- **Microplastiques** : rejets et usage

### Qui est concerné

Matériel pour : industriel (chimie, métallurgie, agroalimentaire), BTP, transport lourd, exploitations agricoles. **Non matériel** pour : services, tech, finance pure — mais ne l'omettez pas sans justification documentée.

### Les pièges fréquents

- **Registre PRTR oublié** : si votre installation est classée ICPE et déclare au registre PRTR (pollutions), ces données **doivent** apparaître dans l'ESRS E2. Le CAC les croisera avec le portail `georisques.gouv.fr`.
- **SVHC (Substances of Very High Concern)** : obligation de déclaration dans la base ECHA SCIP depuis 2021. Si vos produits contiennent > 0.1 % de SVHC, il faut le signaler dans E2 **et** E5.

---

## ESRS E3 — Ressources hydriques et marines

### Ce que le standard exige

- **Prélèvements d'eau** par source (eau municipale, eaux souterraines, eaux de surface, eau de mer)
- **Consommation d'eau** (prélèvement – rejets)
- **Rejets d'eau** par destination (station d'épuration, milieu naturel)
- **Exposition au stress hydrique** : % des sites/opérations dans des zones de stress hydrique élevé ou extrême (selon cartographie WRI Aqueduct)
- **Politiques de gestion de l'eau** et objectifs de réduction

### L'outil à connaître : WRI Aqueduct

[Aqueduct Water Risk Atlas](https://www.wri.org/aqueduct) est **l'outil de référence** cité explicitement par l'ESRS E3 pour cartographier l'exposition au stress hydrique. Gratuit, il géolocalise vos sites et leur attribue un score de risque hydrique selon 13 critères. Intégrez sa cartographie dans votre rapport : c'est une attente directe des auditeurs.

### Les 3 KPI clés

| KPI | Unité | Commentaire |
|---|---|---|
| Prélèvements totaux | m³ ou ML | Ventilés par source |
| Consommation nette | m³ ou ML | Prélèvement – rejet |
| % d'activités en zone de stress hydrique élevé/extrême | % | Selon Aqueduct, indicateur clé |

---

## ESRS E4 — Biodiversité et écosystèmes

### Ce que le standard exige (et pourquoi il fait peur)

L'ESRS E4 est **le plus conceptuellement complexe** car la biodiversité n'a pas d'unité de mesure unique comme la tonne de CO2. Il couvre :

- **Impacts directs** sur la biodiversité : destruction d'habitats, fragmentation, pollution, espèces invasives
- **Dépendance** de l'entreprise aux services écosystémiques (pollinisation, régulation de l'eau, fertilité des sols)
- **Sites situés dans ou à proximité de zones sensibles** : Natura 2000, aires protégées UICN, zones KBA (Key Biodiversity Areas)
- **Plans de transition** vers des activités positives pour la biodiversité

### La méthode recommandée : TNFD

Le **Taskforce on Nature-related Financial Disclosures (TNFD)** publie depuis 2023 un framework méthodologique aligné sur ESRS E4 (et sur les standards ISSB). Structurez votre reporting E4 selon l'approche **LEAP** :

- **L**ocate : identifier les sites géographiques
- **E**valuate : évaluer les dépendances et impacts
- **A**ssess : mesurer les risques et opportunités
- **P**repare : répondre stratégiquement

### Les pièges

- **« Nous sommes dans des locaux en ville, E4 est non matériel »** — vrai en direct, mais votre Scope 3 (achats de biens et services) a un impact biodiversité via vos fournisseurs (soja, huile de palme, coton, bois). Interrogez toute la chaîne.
- **Aucune mesure de dépendance** : E4 impose d'évaluer aussi les dépendances (ex. : un industriel dépendant de l'eau de rivière subit un risque biodiversité via la qualité des écosystèmes aquatiques).

---

## ESRS E5 — Économie circulaire et utilisation des ressources

### Ce que le standard exige

- **Flux de matières entrants** : volumes et provenance (vierge vs recyclée, renouvelable vs non renouvelable)
- **Flux de matières sortants** : produits vendus, conçus pour durabilité/réparabilité/recyclabilité
- **Déchets** : volumes par type, destination (réutilisation, recyclage, incinération, enfouissement)
- **Stratégie circulaire** : éco-conception, réparation, réemploi, recyclage, valorisation

### Le cadre de pensée : la pyramide des 9R

La doctrine de l'économie circulaire UE s'appuie sur les **9R**, du plus vertueux au moins vertueux :

1. **Refuse** — refuser une consommation superflue
2. **Rethink** — repenser l'usage (ex : mutualisation)
3. **Reduce** — réduire la matière utilisée
4. **Reuse** — réemployer en l'état
5. **Repair** — réparer
6. **Refurbish** — rénover
7. **Remanufacture** — reconstruire
8. **Repurpose** — détourner
9. **Recycle** — recycler
10. **Recover** — valoriser énergétiquement

**Astuce** : structurez votre narratif E5 en plaçant vos actions sur cette échelle. Un rapport qui ne parle que de recyclage (9) sans aborder les 8 premiers échelons perd des points d'évaluation.

### Les KPI à calculer

| KPI | Unité |
|---|---|
| Matières recyclées en entrée / matières totales | % |
| Matières renouvelables / matières totales | % |
| Taux de déchets valorisés | % |
| Taux de réemploi / réparation | % |
| Durée de vie moyenne des produits vendus | années |

---

## Tableau de synthèse : priorité d'action par type d'entreprise

| Type | E1 Climat | E2 Pollution | E3 Eau | E4 Biodiversité | E5 Circulaire |
|---|---|---|---|---|---|
| **Services / Tech** | 🔴 Très matériel | 🟢 Souvent non matériel | 🟡 Modéré | 🟡 Via Scope 3 | 🟡 Modéré |
| **Industrie manufacturière** | 🔴 Très matériel | 🔴 Très matériel | 🔴 Très matériel | 🟠 Matériel | 🔴 Très matériel |
| **Agroalimentaire** | 🔴 Très matériel | 🔴 Très matériel | 🔴 Très matériel | 🔴 Très matériel | 🟠 Matériel |
| **Retail / Distribution** | 🟠 Matériel | 🟡 Modéré | 🟡 Modéré | 🟠 Via Scope 3 | 🟠 Matériel |
| **BTP / Immobilier** | 🔴 Très matériel | 🟠 Matériel | 🟠 Matériel | 🟠 Matériel | 🔴 Très matériel |
| **Finance** | 🟠 Matériel (portefeuille) | 🟡 Modéré | 🟡 Modéré | 🟠 Via portefeuille | 🟡 Modéré |

Cette matrice est indicative : chaque entreprise doit conduire sa propre analyse de double matérialité pour confirmer.

---

## Ce qu'il faut retenir

1. **E1 pèse le plus lourd** dans le volume et la difficulté méthodologique. Commencez par là.
2. **E2, E3, E4 sont souvent négligés** mais peuvent être éliminatoires s'ils sont matériels et omis sans justification.
3. **E5 est le plus « visible »** pour vos clients et salariés (économie circulaire = sujet grand public). Sous-traiter sa narration à votre équipe marketing peut payer.
4. Tous ces standards **se parlent entre eux** : les émissions GES de E1 sont en partie liées aux flux de matière de E5, le stress hydrique de E3 crée des risques physiques pour E1, la biodiversité de E4 dépend de la pollution de E2…

Un rapport bien fait **met explicitement en évidence ces interconnexions**, typiquement dans une section dédiée en début de chapitre environnement.

---

## Gagnez 20 heures d'analyse

L'[outil ESG Optimizer](https://esg-optimizer.fr/quick-check) scanne automatiquement votre rapport sur les 5 standards E1-E5, chiffre votre couverture ESRS, identifie les KPI manquants et vous renvoie un plan d'action priorisé. **Gratuit pour votre première analyse.**

[**Lancer le diagnostic →**](https://esg-optimizer.fr/quick-check)

---

*Sources : EFRAG ESRS Set 1 (juillet 2023, amendé en 2025), GHG Protocol Corporate Standard + Scope 2 Guidance + Scope 3 Standard, TNFD Recommendations v1.0 (septembre 2023), WRI Aqueduct Water Risk Atlas, Ellen MacArthur Foundation Circular Economy framework.*
