# Guide de déploiement

> Document de référence pour mettre ESG Optimizer en production. Durée totale estimée : **3 à 5 heures** (si tout va bien).

---

## Prérequis

- Compte GitHub (pour push le code)
- Compte Railway - `https://railway.app` (connexion via GitHub, plan Hobby 5$/mois ou free tier)
- Compte OpenAI avec crédit
- Compte Resend (emails) - `https://resend.com`
- Compte Stripe activé en mode live
- Compte Sentry - `https://sentry.io` (free 5k events/mois)
- Domaine `esg-optimizer.fr` acheté (OVH, Gandi, Porkbun... ~15€/an)

---

## Étape 1 - Préparer le repo Git

```bash
# Dans le dossier du projet
git init  # si pas encore fait
git add .
git commit -m "Polish final et configuration de deploiement"
git branch -M main
# Créer un repo GitHub privé, puis :
git remote add origin https://github.com/<TON_USER>/esg-optimizer.git
git push -u origin main
```

**Vérifie que `.env` est dans `.gitignore`.** Sinon tes clés API partent sur GitHub.

---

## Étape 2 - Tester Sentry en local (10 min)

1. Créer un compte sur `https://sentry.io`.
2. New Project -> Platform: **FastAPI** -> Nom: `esg-optimizer-backend`.
3. Copier le **DSN** affiché à l'écran.
4. Dans ton `.env` local, coller `SENTRY_DSN=https://...`.
5. Démarrer le backend : `uvicorn backend.main:app --reload`.
6. Ouvrir `http://localhost:8000/debug/sentry` - erreur volontaire déclenchée.
7. Vérifier sur `sentry.io` que l'erreur remonte (arrivée en ~10s).
8. Supprimer la route `/debug/sentry` de `main.py` avant le push prod (ou la laisser protégée par `settings.is_dev`, déjà fait).

---

## Étape 3 - Tests de charge Locust (30 min)

```bash
# 1. Démarrer le backend
uvicorn backend.main:app --port 8000

# 2. Dans un autre terminal
pip install locust
locust -f tests/locustfile.py --host http://localhost:8000

# 3. Ouvrir http://localhost:8089
#    Number of users : 10
#    Spawn rate      : 2
#    Run time        : 5m
#    Host            : http://localhost:8000
```

**Critères de succès :**

- Taux d'échec < 1 %
- p95 < 5 s
- Pas de "database is locked" en logs

**Si échec** -> migrer SQLite -> Postgres **avant** de déployer.

---

## Étape 4 - Build & test Docker local (15 min)

```bash
# Build
docker build -t esg-optimizer:latest .

# Run (penser à adapter le .env)
docker run --rm -p 8501:8501 -p 8000:8000 --env-file .env esg-optimizer:latest

# Test
# Browser -> http://localhost:8501  (Streamlit)
# Browser -> http://localhost:8000/docs  (FastAPI Swagger)
```

---

## Étape 5 - Déployer sur Railway (30 min)

1. Se connecter sur `https://railway.app` avec ton compte GitHub.
2. `New Project` -> `Deploy from GitHub repo` -> sélectionner `esg-optimizer`.
3. Railway détecte le `Dockerfile` et commence le build.
4. Onglet **Variables** -> ajouter toutes les variables du `.env.example` avec tes vraies valeurs.
   - **Attention** : ne pas définir `PORT` - Railway s'en charge.
   - Générer un nouveau `JWT_SECRET` pour la prod (différent du local).
5. Onglet **Settings** -> **Volumes** -> `+ Add Volume` -> Mount path `/app/data`, size 1 GB. Permet de persister SQLite + uploads entre deploys.
6. Onglet **Settings** -> **Networking** -> `Generate Domain`. Railway te donne une URL `*.up.railway.app`.

**(Optionnel mais recommandé) Postgres managé** : `New -> Database -> Add Postgres`. Railway génère `DATABASE_URL` et l'injecte comme variable. Coller dans le service web.

---

## Étape 6 - Brancher le domaine esg-optimizer.fr (20 min)

1. Acheter le domaine chez **OVH / Gandi / Porkbun** (~15€/an).
2. Sur Railway, **Settings** -> **Networking** -> `+ Custom Domain` -> saisir `esg-optimizer.fr`. Railway affiche un enregistrement CNAME.
3. Chez ton registrar DNS, ajouter :
   ```
   Type  Nom   Valeur                        TTL
   CNAME @     <id>.up.railway.app           300    (apex via CNAME flattening ou ALIAS)
   CNAME www   <id>.up.railway.app           300
   ```
   Si ton registrar ne gère pas l'ALIAS/CNAME flattening pour l'apex, utilise la redirection A vers Cloudflare (gratuit, CNAME flattening inclus).
4. Attendre 10-60 min la propagation DNS. Railway génère automatiquement le certificat Let's Encrypt.
5. Redirection `www` -> apex : dans Railway, ajouter les 2 domaines, la redirection se fait côté DNS (ALIAS www -> apex) ou via un middleware simple FastAPI.

---

## Étape 7 - Stripe en mode live (20 min)

1. Passer Stripe en **Live mode** (toggle en haut à droite du dashboard).
2. Récupérer `sk_live_...` -> mettre dans Railway `STRIPE_SECRET_KEY`.
3. Créer les deux **Payment Links** (mode live) :
   - Produit "ESG Optimizer Essentiel" - 39€ one-shot
   - Produit "ESG Optimizer Pro" - 129€/mois récurrent
4. Mettre les URLs dans `STRIPE_LINK_ESSENTIEL` et `STRIPE_LINK_PRO`.
5. Configurer le webhook : **Developers -> Webhooks** -> `+ Add endpoint` -> URL `https://esg-optimizer.fr/stripe/webhook` -> événements `checkout.session.completed`, `invoice.paid`, `customer.subscription.updated`, `customer.subscription.deleted`. Récupérer le `whsec_...` -> Railway `STRIPE_WEBHOOK_SECRET`.

---

## Étape 8 - Emails Resend + domaine d'envoi (15 min)

1. Compte Resend -> **Domains -> Add Domain** -> `esg-optimizer.fr`.
2. Ajouter les enregistrements DNS (MX, TXT SPF, DKIM) fournis par Resend chez ton registrar.
3. Attendre la vérification (~15 min). Resend passe au statut **Verified**.
4. API key (Resend) -> Railway `RESEND_API_KEY`.
5. Dans ton code (`email_service.py`), les expéditeurs `no-reply@esg-optimizer.fr` et `hello@esg-optimizer.fr` deviennent autorisés.

---

## Étape 9 - SEO & vérification moteurs de recherche (15 min)

1. `https://esg-optimizer.fr/robots.txt` -> doit renvoyer le fichier.
2. `https://esg-optimizer.fr/sitemap.xml` -> idem.
3. **Google Search Console** -> `+ Ajouter une propriété` -> `esg-optimizer.fr` -> vérification par balise DNS TXT.
4. Soumettre le sitemap dans l'onglet **Sitemaps**.
5. **Bing Webmaster Tools** -> même démarche.
6. Tester les meta OG avec :
   - `https://www.opengraph.xyz/url/https%3A%2F%2Fesg-optimizer.fr`
   - `https://metatags.io/?url=https%3A%2F%2Fesg-optimizer.fr`
7. Si l'image OG n'est pas définie : créer une image `static/og-image.png` (1200×630, badge générique) et la référencer dans `config.py`.

---

## Étape 10 - Publication des 3 articles de blog (30 min par article)

Les 3 articles sont dans le dossier `blog/`. Choisir une des deux stratégies :

**Option A - Pages Streamlit dédiées** (rapide, mauvais pour SEO)
- Créer `frontend/pages/6_📝_Blog.py` qui liste les articles + `frontend/pages/7_📄_Article.py` qui affiche le Markdown via `st.markdown(...)`.
- Injecter `seo_for("blog_article", ...)` en début de page.

**Option B - Notion + Super.so** (recommandé pour SEO)
- Créer un workspace Notion "ESG Optimizer Blog".
- Coller chaque Markdown comme page Notion.
- Connecter `https://super.so` au workspace -> déploiement instantané sur `blog.esg-optimizer.fr`.
- DNS : CNAME `blog` -> `target.super.so`.
- Coût : 16$/mois mais SEO top + gestion éditoriale simple.

Placer un CTA `"👉 Tester le quick-check"` tous les 400-600 mots dans chaque article.

---

## Étape 11 - Derniers contrôles avant annonce (15 min)

- [ ] Lighthouse score > 90 sur mobile et desktop
- [ ] Un parcours complet : register -> upload -> analyse -> PDF téléchargé OK
- [ ] Un paiement Stripe test de bout en bout (utiliser le mode live avec un vrai 1€, puis rembourser)
- [ ] Email transactionnel reçu (welcome)
- [ ] Sentry reçoit bien une erreur forcée en prod
- [ ] Analytics Umami/Plausible affiche la première visite
- [ ] `https://www.esg-optimizer.fr` redirige vers `https://esg-optimizer.fr`
- [ ] Page RGPD et mentions légales à jour avec ton adresse/SIRET
- [ ] Désactiver la route `/debug/sentry` si tu ne l'as pas déjà fait

---

## Étape 12 - Annonce (LinkedIn, X, mailing)

Modèle LinkedIn :

> Après 6 mois de R&D, je lance officiellement **ESG Optimizer AI**.
>
> L'idée : permettre à **n'importe quelle PME** de passer au crible son rapport de durabilité pour la CSRD, sans cabinet conseil, en 3 minutes et à partir de 0€.
>
> Ce que l'outil fait :
> - Scan automatique des 12 ESRS
> - Score ESG sur 100, audit-ready
> - Delta annuel pour suivre la progression
> - PDF propre à partager au COMEX
>
> Pourquoi c'est utile : les CAC vont commencer à auditer les rapports CSRD en mode « assurance limitée ». 80 % des brouillons que j'ai analysés contiennent des non-conformités évitables.
>
> 👉 Tester gratuitement : https://esg-optimizer.fr/quick-check
>
> Feedback, critiques et retours d'expérience bienvenus. ♻️

---

## Ressources utiles

- Railway docs : `https://docs.railway.app`
- Sentry FastAPI : `https://docs.sentry.io/platforms/python/integrations/fastapi/`
- Resend DNS : `https://resend.com/docs/dashboard/domains/introduction`
- Stripe Payment Links : `https://stripe.com/docs/payment-links`
- Google Search Console : `https://search.google.com/search-console`
