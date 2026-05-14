import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

// Client côté navigateur (public)
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Client côté serveur (service role — uniquement dans les API routes / Server Components)
export function createSupabaseAdmin() {
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
  return createClient(supabaseUrl, serviceKey, {
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
