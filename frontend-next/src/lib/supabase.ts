import { createClient } from "@supabase/supabase-js";

// Client côté navigateur (public) — instanciation différée pour éviter les crashes au build
// quand les env vars ne sont pas encore disponibles (Vercel build phase)
const _supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const _supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const supabase = (_supabaseUrl && _supabaseAnonKey)
  ? createClient(_supabaseUrl, _supabaseAnonKey)
  : (undefined as unknown as ReturnType<typeof createClient>);

// Client côté serveur (service role — uniquement dans les API routes / Server Components)
// Lit toutes ses vars localement pour ne pas dépendre du scope module
export function createSupabaseAdmin() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
  return createClient(url, serviceKey, {
    auth: { persistSession: false },
  });
}

// Types de la table users
export interface UserRow {
  id: string;           // Clerk user_id (ex: "user_2abc...")
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  plan: "discovery" | "essential" | "pro" | "enterprise";
  analyses_count: number;
  analyses_limit: number;
  stripe_customer_id: string | null;
  created_at: string;
  updated_at: string;
}
