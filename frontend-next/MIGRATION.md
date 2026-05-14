# ESG Optimizer — Guide de migration Next.js

Branche : `next-migration` | Le site Streamlit sur `main` reste **intact**.

---

## 1. Setup local (5 min)

```bash
cd frontend-next
npm install
cp .env.local.example .env.local
# Remplir les clés dans .env.local (voir section 2)
npm run dev
# → http://localhost:3000
```

---

## 2. Clés à configurer

### A — Clerk (auth)
1. Va sur [dashboard.clerk.com](https://dashboard.clerk.com) → Create application
2. Choisis "Email + Google" comme méthodes de connexion
3. Copie `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` et `CLERK_SECRET_KEY` dans `.env.local`
4. Dans Clerk Dashboard → Webhooks → Add Endpoint :
   - URL : `https://ton-domaine.vercel.app/api/webhook/clerk`
   - Events : `user.created`, `user.updated`, `user.deleted`
   - Copie le Signing Secret → `CLERK_WEBHOOK_SECRET`

### B — Supabase (base de données)
1. Va sur [app.supabase.com](https://app.supabase.com) → New project
2. Dans **SQL Editor** → colle tout le contenu de `supabase/schema.sql` → Run
3. Dans **Settings → API** → copie les clés dans `.env.local`

### C — FastAPI backend (Railway — inchangé)
- `NEXT_PUBLIC_API_URL` = l'URL de ton app Railway actuelle (ex: `https://esg-optimizer.railway.app`)

---

## 3. Déployer sur Vercel (gratuit)

```bash
# Depuis la racine du repo (pas frontend-next/)
# Vercel détecte automatiquement que le dossier Next.js est dans frontend-next/
```

1. Va sur [vercel.com](https://vercel.com) → Import Git Repository → sélectionne ton repo
2. Configure **Root Directory** = `frontend-next`
3. Ajoute toutes les variables de `.env.local` dans **Environment Variables**
4. Deploy → ton URL Vercel est prête

> ⚠️ Le backend FastAPI reste sur Railway ($5/mois). Le frontend Next.js est sur Vercel (gratuit).

---

## 4. Basculer en production

Quand le site Next.js est validé :
```bash
git checkout main
git merge next-migration
git push origin main
# → Railway redéploie le backend (inchangé)
# → Tu peux couper le frontend Streamlit sur Railway si tu veux économiser
```

---

## Structure des fichiers

```
frontend-next/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Clerk provider + metadata
│   │   ├── page.tsx            # Landing page publique
│   │   ├── globals.css         # Design tokens ESG
│   │   ├── sign-in/            # Page connexion Clerk
│   │   ├── sign-up/            # Page inscription Clerk
│   │   ├── tarifs/             # Page tarifs (publique)
│   │   ├── mentions/           # Mentions légales (publique)
│   │   ├── (app)/              # Pages protégées (auth requise)
│   │   │   ├── layout.tsx      # Vérif auth + Sidebar
│   │   │   ├── dashboard/      # Dashboard KPIs
│   │   │   ├── upload/         # Upload rapport
│   │   │   ├── resultats/      # Résultats & historique
│   │   │   └── parametres/     # Paramètres compte (Clerk UserProfile)
│   │   └── api/
│   │       └── webhook/clerk/  # Sync Clerk → Supabase
│   ├── components/
│   │   ├── Sidebar.tsx         # Navigation latérale
│   │   └── AppLayout.tsx       # Layout avec sidebar
│   ├── lib/
│   │   ├── api.ts              # Client HTTP → FastAPI
│   │   └── supabase.ts         # Client Supabase
│   └── middleware.ts           # Protection des routes (Clerk)
├── supabase/
│   └── schema.sql              # Tables users + analyses (à coller dans Supabase)
├── .env.local.example          # Template variables d'env
└── MIGRATION.md                # Ce guide
```
