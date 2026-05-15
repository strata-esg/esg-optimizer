# ESG Optimizer AI - Plan d'Architecture MVP Web App

> Version 1.0 - 16 avril 2026
> Stack : Python 3.11+ · FastAPI · Streamlit · SQLite · GPT-4o · Railway/Render

---

## 1. Vue d'ensemble

Le MVP transforme le pipeline Make.com existant en application web autonome. L'utilisateur uploade un rapport de durabilité, obtient une analyse ESG structurée en moins de 3 minutes, et peut consulter son historique.

```
┌---------------------------------------------------------┐
│                    STREAMLIT (Frontend)                  │
│  ┌----------┐ ┌--------------┐ ┌----------------------┐ │
│  │  Login /  │ │   Upload &   │ │  Dashboard &         │ │
│  │  Register │ │   Analyse    │ │  Historique          │ │
│  └----------┘ └--------------┘ └----------------------┘ │
└------------------------┬--------------------------------┘
                         │ HTTP (requests)
┌------------------------▼--------------------------------┐
│                    FASTAPI (Backend)                     │
│  ┌----------┐ ┌--------------┐ ┌----------------------┐ │
│  │  Auth     │ │  Analyse     │ │  History &           │ │
│  │  Routes   │ │  Pipeline    │ │  Reports             │ │
│  └----------┘ └--------------┘ └----------------------┘ │
│         │              │                    │            │
│  ┌------▼--------------▼--------------------▼---------┐ │
│  │              Services Layer                         │ │
│  │  auth_service · extractor · analyzer · reporter     │ │
│  └---------┬-----------┬--------------------┬---------┘ │
└------------┼-----------┼--------------------┼-----------┘
             │           │                    │
     ┌-------▼--┐  ┌-----▼------┐  ┌---------▼--------┐
     │  SQLite  │  │  OpenAI    │  │  File Extractors  │
     │  (DB)    │  │  GPT-4o    │  │  (PDF/DOCX/XLSX)  │
     └----------┘  └------------┘  └------------------┘
```

---

## 2. Structure des fichiers

```
esg-optimizer-mvp/
│
├-- backend/
│   ├-- main.py                  # Point d'entrée FastAPI
│   ├-- config.py                # Settings (Pydantic BaseSettings)
│   ├-- database.py              # Connexion SQLite + session factory
│   ├-- models.py                # Modèles SQLAlchemy (User, Analysis, Company)
│   ├-- schemas.py               # Schémas Pydantic (request/response)
│   │
│   ├-- routers/
│   │   ├-- __init__.py
│   │   ├-- auth.py              # POST /auth/register, /auth/login, /auth/me
│   │   ├-- analysis.py          # POST /analysis/upload, GET /analysis/{id}
│   │   └-- history.py           # GET /history, GET /history/{company}
│   │
│   ├-- services/
│   │   ├-- __init__.py
│   │   ├-- auth_service.py      # Hashing passwords, JWT tokens
│   │   ├-- extractor.py         # PDF/DOCX/XLSX -> texte brut
│   │   ├-- analyzer.py          # Appel GPT-4o + parsing JSON
│   │   ├-- delta_service.py     # Comparaison N vs N-1, calcul des deltas
│   │   └-- reporter.py          # Génération du rapport PDF final
│   │
│   ├-- prompts/
│   │   ├-- system_analysis.py   # System prompt pour l'analyse ESG initiale
│   │   └-- system_delta.py      # System prompt pour le Delta Report
│   │
│   └-- tests/
│       ├-- test_extractor.py
│       ├-- test_analyzer.py
│       └-- test_auth.py
│
├-- frontend/
│   ├-- app.py                   # Point d'entrée Streamlit (routing pages)
│   ├-- pages/
│   │   ├-- 1_🔐_Login.py        # Authentification
│   │   ├-- 2_📤_Upload.py       # Upload & lancement analyse
│   │   ├-- 3_📊_Résultats.py    # Affichage résultats + téléchargement PDF
│   │   ├-- 4_📈_Dashboard.py    # Dashboard historique & tendances
│   │   └-- 5_⚙️_Paramètres.py   # Profil utilisateur & paramètres
│   ├-- components/
│   │   ├-- score_gauge.py       # Widget jauge score 0-100
│   │   ├-- esrs_coverage.py     # Grille couverture ESRS
│   │   ├-- delta_card.py        # Carte delta avec indicateur tendance
│   │   └-- sidebar.py           # Sidebar navigation + branding
│   └-- utils/
│       ├-- api_client.py        # Wrapper requests vers le backend
│       └-- session.py           # Gestion du token JWT en session_state
│
├-- data/
│   └-- esg_optimizer.db         # Base SQLite (gitignored)
│
├-- .env.example                 # Template variables d'environnement
├-- requirements.txt             # Dépendances Python
├-- Dockerfile                   # Build multi-stage (backend + frontend)
├-- docker-compose.yml           # Orchestration locale dev
├-- railway.toml                 # Config déploiement Railway
└-- README.md
```

---

## 3. Modèle de données (SQLite via SQLAlchemy)

### 3.1 Table `users`

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Identifiant unique |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email de connexion |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hash |
| company_name | VARCHAR(255) | | Nom de l'entreprise |
| plan | VARCHAR(20) | DEFAULT 'free' | 'free' ou 'pro' |
| analyses_this_month | INTEGER | DEFAULT 0 | Compteur freemium |
| created_at | DATETIME | DEFAULT NOW | Date d'inscription |

### 3.2 Table `companies`

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | |
| user_id | INTEGER | FK -> users.id | Propriétaire |
| name | VARCHAR(255) | NOT NULL | Nom entreprise analysée |
| sector | VARCHAR(255) | | Secteur d'activité |
| created_at | DATETIME | DEFAULT NOW | |

**Contrainte unique** : (user_id, name) - un utilisateur ne peut pas avoir deux entreprises du même nom.

### 3.3 Table `analyses`

| Colonne | Type | Contraintes | Description |
|---------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | |
| company_id | INTEGER | FK -> companies.id | Entreprise analysée |
| user_id | INTEGER | FK -> users.id | Utilisateur |
| report_year | INTEGER | | Année du rapport source |
| source_filename | VARCHAR(255) | NOT NULL | Nom du fichier uploadé |
| source_format | VARCHAR(10) | | pdf, docx, xlsx |
| score_env | FLOAT | | Score Environnement 0-100 |
| score_social | FLOAT | | Score Social 0-100 |
| score_gov | FLOAT | | Score Gouvernance 0-100 |
| score_global | FLOAT | | Score Global 0-100 |
| csrd_ready | BOOLEAN | | Verdict conformité |
| csrd_coverage_pct | FLOAT | | % couverture CSRD |
| missing_disclosures | TEXT | | JSON array des disclosures manquantes |
| kpis_detected | TEXT | | JSON array des KPIs avec refs ESRS |
| strengths | TEXT | | JSON array points forts |
| weaknesses | TEXT | | JSON array lacunes |
| recommendations | TEXT | | JSON array recommandations priorisées |
| esrs_coverage | TEXT | | JSON objet {E1:bool, E2:bool, ..., G1:bool} |
| executive_summary | TEXT | | Synthèse exécutive |
| raw_llm_response | TEXT | | JSON complet retourné par GPT-4o |
| delta_env | FLOAT | NULL | Delta score E vs précédent |
| delta_social | FLOAT | NULL | Delta score S vs précédent |
| delta_gov | FLOAT | NULL | Delta score G vs précédent |
| delta_global | FLOAT | NULL | Delta score global vs précédent |
| delta_narrative | TEXT | NULL | Synthèse d'évolution (2e appel GPT-4o) |
| processing_time_s | FLOAT | | Durée d'exécution en secondes |
| status | VARCHAR(20) | DEFAULT 'pending' | pending, processing, success, failed |
| error_message | TEXT | NULL | Message d'erreur si échec |
| created_at | DATETIME | DEFAULT NOW | |

---

## 4. API Endpoints (FastAPI)

### 4.1 Auth

| Méthode | Route | Body / Params | Réponse | Description |
|---------|-------|---------------|---------|-------------|
| POST | `/auth/register` | `{email, password, company_name?}` | `{user_id, email, token}` | Inscription |
| POST | `/auth/login` | `{email, password}` | `{token, user}` | Connexion, retourne JWT |
| GET | `/auth/me` | Header: `Authorization: Bearer <token>` | `{user}` | Profil utilisateur |

**Auth technique** : JWT (PyJWT), expiration 24h, secret dans `.env`. Pas d'OAuth pour le MVP - on reste simple.

### 4.2 Analysis

| Méthode | Route | Body / Params | Réponse | Description |
|---------|-------|---------------|---------|-------------|
| POST | `/analysis/upload` | `multipart/form-data: file, company_name, report_year, sector?` | `{analysis_id, status: "processing"}` | Lance l'analyse |
| GET | `/analysis/{id}` | Path: analysis_id | `{analysis complète}` | Récupère les résultats |
| GET | `/analysis/{id}/pdf` | Path: analysis_id | `application/pdf` | Télécharge le rapport PDF |
| GET | `/analysis/{id}/delta-pdf` | Path: analysis_id | `application/pdf` | Télécharge le Delta Report |

**Flow POST /analysis/upload :**
1. Vérifier quota freemium (≤1/mois si plan=free)
2. Valider extension fichier (pdf, docx, xlsx)
3. Sauvegarder fichier temporaire
4. Créer entrée `analyses` avec status=processing
5. Lancer le pipeline en background (BackgroundTasks FastAPI)
6. Retourner immédiatement l'analysis_id

### 4.3 History

| Méthode | Route | Params | Réponse | Description |
|---------|-------|--------|---------|-------------|
| GET | `/history` | Query: `?page=1&per_page=20` | `{analyses[], total, page}` | Liste paginée |
| GET | `/history/companies` | - | `{companies[]}` | Liste des entreprises analysées |
| GET | `/history/stats` | - | `{total_analyses, avg_scores, csrd_ready_pct}` | Stats agrégées pour dashboard |

---

## 5. Pipeline d'analyse (services/)

### 5.1 Extraction du texte (`extractor.py`)

```python
# Librairies utilisées :
# - PDF : PyMuPDF (fitz) - extraction texte rapide, pas de dépendance externe
# - DOCX : python-docx - lecture paragraphes + tableaux
# - XLSX : openpyxl - lecture cellules, conversion en texte structuré

def extract_text(file_path: str, file_format: str) -> str:
    """Retourne le texte brut du document, tronqué à 30 000 caractères."""
    ...
```

Avantage par rapport à v1 : plus besoin de CloudConvert API. Extraction 100% locale, gratuite, et sans latence réseau.

### 5.2 Analyse GPT-4o (`analyzer.py`)

```python
async def analyze_report(text: str, company_name: str, sector: str) -> dict:
    """
    Envoie le texte extrait à GPT-4o avec le system prompt ESG expert.
    Retourne un dict structuré avec scores, KPIs, conformité, recommandations.
    """
    response = await openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_ANALYSIS_PROMPT},
            {"role": "user", "content": f"Entreprise: {company_name}\nSecteur: {sector}\n\nRapport:\n{text[:30000]}"}
        ],
        response_format={"type": "json_object"},
        temperature=0.2,  # Basse pour reproductibilité
        max_tokens=4000
    )
    return json.loads(response.choices[0].message.content)
```

**Paramètre clé** : `response_format={"type": "json_object"}` force GPT-4o à retourner un JSON valide, éliminant les erreurs de parsing de la v1.

### 5.3 System Prompt - Analyse initiale (`system_analysis.py`)

Le system prompt est le cœur métier. Il doit produire un JSON nested avec cette structure exacte :

```json
{
  "executive_summary": "string (3-5 phrases)",
  "scores": {
    "environment": 0-100,
    "social": 0-100,
    "governance": 0-100,
    "global": 0-100
  },
  "esrs_coverage": {
    "E1_climate_change": true/false,
    "E2_pollution": true/false,
    "E3_water_marine": true/false,
    "E4_biodiversity": true/false,
    "E5_circular_economy": true/false,
    "S1_own_workforce": true/false,
    "S2_value_chain_workers": true/false,
    "S3_affected_communities": true/false,
    "S4_consumers": true/false,
    "G1_business_conduct": true/false
  },
  "csrd_compliance": {
    "coverage_percentage": 0-100,
    "csrd_ready": true/false,
    "missing_disclosures": ["string"]
  },
  "kpis": [
    {
      "name": "string",
      "value": "string",
      "unit": "string",
      "esrs_reference": "E1-5" ,
      "pillar": "E|S|G"
    }
  ],
  "strengths": [{"pillar": "E|S|G", "description": "string"}],
  "weaknesses": [{"pillar": "E|S|G", "description": "string"}],
  "recommendations": [
    {
      "priority": 1-5,
      "pillar": "E|S|G",
      "action": "string",
      "expected_impact": "string",
      "esrs_reference": "string"
    }
  ]
}
```

**Instructions critiques dans le prompt** :
- Scorer selon la maturité réelle du reporting, pas l'ambition déclarée
- Un score de 50 = couverture minimale acceptable, 80+ = reporting mature
- Ne jamais inventer de KPI non présent dans le document
- Anonymiser tout nom de personne physique (RGPD)
- Citer la référence ESRS pour chaque KPI et recommandation

### 5.4 Delta Service (`delta_service.py`)

```python
def compute_deltas(current: Analysis, previous: Analysis) -> dict:
    """Calcule les écarts numériques et indicateurs de tendance."""
    return {
        "delta_env": current.score_env - previous.score_env,
        "delta_social": current.score_social - previous.score_social,
        "delta_gov": current.score_gov - previous.score_gov,
        "delta_global": current.score_global - previous.score_global,
        "trends": {
            "environment": "up" if delta_env > 2 else "down" if delta_env < -2 else "stable",
            "social": ...,
            "governance": ...
        },
        "previous_analysis_date": previous.created_at,
        "previous_report_year": previous.report_year
    }
```

Si un historique existe -> 2e appel GPT-4o avec le system prompt delta qui reçoit les deux analyses en contexte et produit une synthèse narrative d'évolution.

### 5.5 Génération PDF (`reporter.py`)

Utilisation de **ReportLab** pour générer les rapports PDF côté serveur (plus besoin de Google Docs templates). Le rapport contient :
- Page de garde avec logo, nom entreprise, date
- Synthèse exécutive
- Jauges de scores E/S/G/Global (graphiques via ReportLab ou matplotlib)
- Grille de couverture ESRS (tableau coloré)
- Tableau des KPIs détectés
- Points forts et lacunes par pilier
- Recommandations priorisées
- Verdict conformité CSRD

---

## 6. Interface Streamlit (Frontend)

### 6.1 Page Login/Register

- Formulaire email + mot de passe
- Toggle inscription / connexion
- Stockage du JWT dans `st.session_state["token"]`
- Redirect auto vers Upload après login

### 6.2 Page Upload & Analyse

- `st.file_uploader` avec accept = [".pdf", ".docx", ".xlsx"]
- Champs : nom entreprise, année du rapport, secteur (selectbox)
- Bouton "Analyser" -> POST /analysis/upload
- `st.spinner` + polling GET /analysis/{id} toutes les 3 secondes
- Affichage du statut en temps réel (processing -> success)

### 6.3 Page Résultats

- **Score global** : grande jauge circulaire au centre
- **Scores E/S/G** : trois jauges côte à côte (st.columns)
- **Synthèse exécutive** : st.info box
- **Couverture ESRS** : grille 10 cases colorées (vert=couvert, rouge=manquant)
- **Conformité CSRD** : badge "CSRD Ready ✓" ou "Non conforme ✗" + % couverture
- **KPIs détectés** : st.dataframe triable par pilier
- **Recommandations** : st.expander par priorité
- **Delta** (si disponible) : cartes avec flèches ↑↓-> et synthèse narrative
- **Boutons** : Télécharger rapport PDF, Télécharger Delta Report PDF

### 6.4 Page Dashboard

- **KPIs header** : total analyses, score moyen global, % CSRD ready
- **Graphique barres** : scores par entreprise (Plotly via st.plotly_chart)
- **Courbe temporelle** : évolution des scores dans le temps
- **Tableau historique** : st.dataframe paginé avec filtres
- **Filtre secteur** : st.selectbox pour filtrer le dashboard

### 6.5 Page Paramètres

- Modifier email, mot de passe, nom entreprise
- Affichage du plan (free/pro) et du compteur d'analyses
- Bouton "Passer en Pro" (placeholder pour Stripe)

---

## 7. Sécurité & Conformité

| Aspect | Implémentation |
|--------|----------------|
| Auth | JWT (python-jose) + bcrypt (passlib), expiration 24h |
| CORS | FastAPI CORSMiddleware, origin = frontend URL uniquement |
| Upload | Validation extension + taille max 20 MB |
| RGPD | Anonymisation noms dans le prompt GPT, suppression fichiers temp après extraction |
| Rate limiting | Quota freemium en DB, slowapi pour rate limit global |
| Secrets | .env (jamais commité), variables d'environnement en prod |
| SQL Injection | SQLAlchemy ORM exclusivement, pas de raw SQL |

---

## 8. Configuration & Variables d'environnement

```env
# .env.example
OPENAI_API_KEY=sk-...
JWT_SECRET=<random-32-chars>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
DATABASE_URL=sqlite:///./data/esg_optimizer.db
MAX_UPLOAD_SIZE_MB=20
MAX_TEXT_LENGTH=30000
FREE_TIER_MONTHLY_LIMIT=1
ENVIRONMENT=development  # development | production
```

---

## 9. Dépendances (requirements.txt)

```
# Backend
fastapi==0.111.*
uvicorn[standard]==0.30.*
sqlalchemy==2.0.*
pydantic==2.*
pydantic-settings==2.*
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*
python-multipart==0.0.*
openai==1.*
slowapi==0.1.*

# Extractors
PyMuPDF==1.24.*      # PDF -> texte
python-docx==1.*     # DOCX -> texte
openpyxl==3.*        # XLSX -> texte

# Report generation
reportlab==4.*       # Génération PDF
matplotlib==3.*      # Graphiques pour le PDF

# Frontend
streamlit==1.37.*
plotly==5.*
requests==2.*

# Dev
pytest==8.*
httpx==0.27.*        # Pour tester FastAPI (TestClient)
python-dotenv==1.*
```

---

## 10. Plan de déploiement

### 10.1 Développement local

```bash
# Terminal 1 - Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend && streamlit run app.py --server.port 8501
```

### 10.2 Production (Railway)

Deux services Railway dans un même projet :
1. **backend** : Dockerfile qui lance uvicorn, port 8000
2. **frontend** : Dockerfile qui lance streamlit, port 8501, variable `BACKEND_URL` pointant vers le service backend

Alternative : un seul service avec un script de lancement qui démarre les deux processus.

### 10.3 Docker Compose (dev)

```yaml
version: "3.8"
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    volumes:
      - ./data:/app/data
  frontend:
    build: ./frontend
    ports: ["8501:8501"]
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
```

---

## 11. Ordre d'implémentation recommandé

L'implémentation se fait en 6 sprints logiques. Chaque sprint produit un incrément testable.

### Sprint 1 - Fondations (backend skeleton)
1. `config.py` + `.env.example`
2. `database.py` + `models.py` (créer les 3 tables)
3. `schemas.py` (tous les schémas Pydantic)
4. `main.py` (FastAPI app avec CORS)
5. **Test** : `uvicorn main:app` démarre sans erreur

### Sprint 2 - Auth
1. `services/auth_service.py` (hash, JWT, verify)
2. `routers/auth.py` (register, login, me)
3. **Test** : créer un user via curl, obtenir un token, appeler /auth/me

### Sprint 3 - Pipeline d'analyse
1. `services/extractor.py` (PDF, DOCX, XLSX)
2. `prompts/system_analysis.py`
3. `services/analyzer.py` (appel GPT-4o)
4. `routers/analysis.py` (upload + background task)
5. **Test** : upload un PDF via curl, vérifier que l'analyse est en DB

### Sprint 4 - Delta + Rapport PDF
1. `services/delta_service.py`
2. `prompts/system_delta.py`
3. `services/reporter.py` (génération PDF)
4. Endpoints `/analysis/{id}/pdf` et `/analysis/{id}/delta-pdf`
5. **Test** : uploader deux rapports de la même entreprise, vérifier le delta

### Sprint 5 - Frontend Streamlit
1. `app.py` + `utils/api_client.py` + `utils/session.py`
2. Pages Login -> Upload -> Résultats -> Dashboard -> Paramètres
3. Composants visuels (jauges, grille ESRS, delta cards)
4. **Test** : parcours complet login -> upload -> voir résultats -> dashboard

### Sprint 6 - Polish & Deploy
1. Error handling robuste (try/except, messages utilisateur)
2. Dockerfile + docker-compose.yml
3. railway.toml + déploiement
4. README.md final
5. **Test** : e2e en production

---

## 12. Métriques de succès du MVP

| Métrique | Cible |
|----------|-------|
| Temps d'analyse end-to-end | < 3 minutes |
| Formats supportés | PDF, DOCX, XLSX |
| Taux de succès pipeline | > 95% |
| Couverture ESRS scoring | 10/10 catégories |
| Authentification | Email/password + JWT |
| Quota freemium | 1 analyse/mois gratuite |
| Déployé en production | Railway ou Render |

---

## 13. Évolutions post-MVP (hors scope actuel)

- Intégration Stripe pour le paiement Pro
- Analyse de tendances pluriannuelles (N, N-1, N-2...)
- Export Excel des KPIs
- Notifications email automatiques (réintégration Make.com)
- Multi-langue (EN/FR)
- API publique avec clés API pour intégrateurs
- Migration SQLite -> PostgreSQL si >100 users
