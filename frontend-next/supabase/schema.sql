-- ============================================================
-- ESG Optimizer — Schema Supabase
-- Coller dans : Supabase Dashboard > SQL Editor > Run
-- ============================================================

-- Extension UUID (activée par défaut dans Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── TABLE USERS ──────────────────────────────────────────────
-- Synchronisée avec Clerk via webhook (api/webhook/clerk)
-- La colonne `id` = clerk user_id (format "user_2abc...")
CREATE TABLE IF NOT EXISTS public.users (
  id                 TEXT PRIMARY KEY,              -- Clerk user_id
  email              TEXT NOT NULL UNIQUE,
  full_name          TEXT,
  avatar_url         TEXT,
  plan               TEXT NOT NULL DEFAULT 'discovery'
                     CHECK (plan IN ('discovery', 'essential', 'pro', 'enterprise')),
  analyses_count     INTEGER NOT NULL DEFAULT 0,
  analyses_limit     INTEGER NOT NULL DEFAULT 3,    -- Plan discovery = 3 analyses
  stripe_customer_id TEXT UNIQUE,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index rapide sur email
CREATE INDEX IF NOT EXISTS users_email_idx ON public.users (email);

-- Trigger pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
  BEFORE UPDATE ON public.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();


-- ── TABLE ANALYSES ────────────────────────────────────────────
-- Stocke le résumé de chaque analyse (la partie lourde reste dans FastAPI/PostgreSQL Railway)
-- Optionnel : utilisez-la pour la synchro cross-service ou le dashboard temps réel
CREATE TABLE IF NOT EXISTS public.analyses (
  id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id            TEXT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  company_name       TEXT,
  report_year        INTEGER,
  score_global       INTEGER,
  score_env          INTEGER,
  score_social       INTEGER,
  score_gov          INTEGER,
  status             TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending', 'processing', 'completed', 'error')),
  file_name          TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS analyses_user_id_idx ON public.analyses (user_id);
CREATE INDEX IF NOT EXISTS analyses_created_at_idx ON public.analyses (created_at DESC);

CREATE TRIGGER analyses_updated_at
  BEFORE UPDATE ON public.analyses
  FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();


-- ── ROW LEVEL SECURITY (RLS) ─────────────────────────────────
-- Les utilisateurs ne voient que leurs propres données

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;

-- Policy users : lecture de son propre profil uniquement
CREATE POLICY "users_select_own" ON public.users
  FOR SELECT USING (auth.uid()::TEXT = id);

CREATE POLICY "users_update_own" ON public.users
  FOR UPDATE USING (auth.uid()::TEXT = id);

-- Policy analyses : CRUD sur ses propres analyses
CREATE POLICY "analyses_select_own" ON public.analyses
  FOR SELECT USING (auth.uid()::TEXT = user_id);

CREATE POLICY "analyses_insert_own" ON public.analyses
  FOR INSERT WITH CHECK (auth.uid()::TEXT = user_id);

CREATE POLICY "analyses_update_own" ON public.analyses
  FOR UPDATE USING (auth.uid()::TEXT = user_id);

CREATE POLICY "analyses_delete_own" ON public.analyses
  FOR DELETE USING (auth.uid()::TEXT = user_id);

-- Service role bypass (pour le webhook Clerk — côté serveur seulement)
-- Le service role ignore automatiquement le RLS, pas besoin de policy supplémentaire.


-- ── FONCTION PLANS ────────────────────────────────────────────
-- Mise à jour du plan + limite d'analyses en une seule requête
CREATE OR REPLACE FUNCTION public.upgrade_user_plan(
  p_user_id TEXT,
  p_plan    TEXT
) RETURNS VOID AS $$
DECLARE
  v_limit INTEGER;
BEGIN
  v_limit := CASE p_plan
    WHEN 'discovery'  THEN 3
    WHEN 'essential'  THEN 20
    WHEN 'pro'        THEN 999
    WHEN 'enterprise' THEN 999
    ELSE 3
  END;
  UPDATE public.users
     SET plan = p_plan, analyses_limit = v_limit
   WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
