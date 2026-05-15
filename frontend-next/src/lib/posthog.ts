/**
 * PostHog - singleton browser client.
 *
 * Importé dans PostHogProvider (client component).
 * Ne jamais importer directement dans un Server Component.
 *
 * Env vars nécessaires (Vercel / Railway) :
 *   NEXT_PUBLIC_POSTHOG_KEY=phc_XXXXXXXXXXXX
 *   NEXT_PUBLIC_POSTHOG_HOST=https://eu.i.posthog.com
 */

import posthog from "posthog-js";

export function initPostHog() {
  if (typeof window === "undefined") return;
  if (posthog.__loaded) return; // déjà initialisé

  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY ?? "", {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://eu.i.posthog.com",
    // On gère manuellement les pageviews (App Router = SPA partielle)
    capture_pageview: false,
    // N'envoyer des données que si l'user est identifié (conformité RGPD)
    person_profiles: "identified_only",
    // Session recording : masquer les passwords uniquement
    session_recording: {
      maskAllInputs: false,
      maskInputOptions: { password: true },
    },
    // Pas de capture en dev local sauf si NEXT_PUBLIC_POSTHOG_KEY est défini
    loaded: (ph) => {
      if (process.env.NODE_ENV === "development" && !process.env.NEXT_PUBLIC_POSTHOG_KEY) {
        ph.opt_out_capturing();
      }
    },
  });
}

export { posthog };
   