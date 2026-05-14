"use client";

/**
 * PostHogProvider — wrapper client à placer dans le root layout.
 *
 * Responsabilités :
 * 1. Initialise posthog-js au premier rendu
 * 2. Identifie l'utilisateur Clerk dans PostHog (userId + email)
 * 3. Track les pageviews à chaque changement de route (App Router)
 * 4. Reset l'identité PostHog à la déconnexion
 */

import { useEffect, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { PostHogProvider as PHProvider } from "posthog-js/react";
import { initPostHog, posthog } from "@/lib/posthog";

// ── Pageview tracker (séparé pour éviter les re-renders inutiles) ────────────
function PostHogPageview() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (pathname) {
      const url =
        searchParams?.toString()
          ? `${pathname}?${searchParams}`
          : pathname;
      posthog.capture("$pageview", { $current_url: url });
    }
  }, [pathname, searchParams]);

  return null;
}

// ── Identify Clerk user dans PostHog ─────────────────────────────────────────
function PostHogIdentity() {
  const { user, isLoaded, isSignedIn } = useUser();
  const identifiedRef = useRef<string | null>(null);

  useEffect(() => {
    if (!isLoaded) return;

    if (isSignedIn && user) {
      // Éviter d'appeler identify() à chaque render si c'est le même user
      if (identifiedRef.current === user.id) return;
      identifiedRef.current = user.id;

      posthog.identify(user.id, {
        email: user.primaryEmailAddress?.emailAddress,
        name: user.fullName ?? undefined,
      });
    } else {
      // Déconnexion → reset pour ne pas mélanger les sessions
      if (identifiedRef.current !== null) {
        posthog.reset();
        identifiedRef.current = null;
      }
    }
  }, [isLoaded, isSignedIn, user]);

  return null;
}

// ── Provider principal ────────────────────────────────────────────────────────
export default function PostHogProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    initPostHog();
  }, []);

  return (
    <PHProvider client={posthog}>
      <PostHogPageview />
      <PostHogIdentity />
      {children}
    </PHProvider>
  );
}
