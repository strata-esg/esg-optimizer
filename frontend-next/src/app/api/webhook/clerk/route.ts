/**
 * Webhook Clerk -> Supabase
 * Sync automatique des users : created / updated / deleted
 *
 * Config Clerk Dashboard :
 *   Webhooks -> Add Endpoint -> URL: https://ton-domaine.vercel.app/api/webhook/clerk
 *   Events : user.created, user.updated, user.deleted
 */

import { headers } from "next/headers";
import { NextResponse } from "next/server";
import { Webhook } from "svix";
import { createSupabaseAdmin } from "@/lib/supabase";
import { PostHog } from "posthog-node";

export const dynamic = 'force-dynamic';

const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET;

function getPostHogClient() {
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  const host = process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://eu.i.posthog.com";
  if (!key) return null;
  return new PostHog(key, { host });
}

export async function POST(req: Request) {
  if (!WEBHOOK_SECRET) {
    return NextResponse.json({ error: "No webhook secret" }, { status: 500 });
  }

  const headerPayload = headers();
  const svix_id = headerPayload.get("svix-id");
  const svix_timestamp = headerPayload.get("svix-timestamp");
  const svix_signature = headerPayload.get("svix-signature");

  if (!svix_id || !svix_timestamp || !svix_signature) {
    return NextResponse.json({ error: "Missing svix headers" }, { status: 400 });
  }

  const payload = await req.json();
  const body = JSON.stringify(payload);

  let evt: { type: string; data: Record<string, unknown> };
  try {
    const wh = new Webhook(WEBHOOK_SECRET);
    evt = wh.verify(body, {
      "svix-id": svix_id,
      "svix-timestamp": svix_timestamp,
      "svix-signature": svix_signature,
    }) as typeof evt;
  } catch {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  const supabase = createSupabaseAdmin();
  const { type, data } = evt;

  switch (type) {
    case "user.created": {
      const email =
        (data.email_addresses as Array<{ email_address: string }>)?.[0]
          ?.email_address ?? "";
      const fullName = [data.first_name, data.last_name]
        .filter(Boolean)
        .join(" ") || null;

      await supabase.from("users").upsert({
        id: data.id as string,
        email,
        full_name: fullName,
        avatar_url: (data.image_url as string) ?? null,
        plan: "discovery",
        analyses_count: 0,
        analyses_limit: 3,
      });

      const ph = getPostHogClient();
      if (ph) {
        ph.identify({
          distinctId: data.id as string,
          properties: { email, name: fullName ?? undefined, plan: "discovery" },
        });
        ph.capture({
          distinctId: data.id as string,
          event: "user_signed_up",
          properties: { plan: "discovery", source: "clerk" },
        });
        await ph.shutdown();
      }
      break;
    }

    case "user.updated": {
      const email =
        (data.email_addresses as Array<{ email_address: string }>)?.[0]
          ?.email_address ?? "";
      const fullName = [data.first_name, data.last_name]
        .filter(Boolean)
        .join(" ") || null;

      await supabase.from("users").update({
        email,
        full_name: fullName,
        avatar_url: (data.image_url as string) ?? null,
      }).eq("id", data.id as string);
      break;
    }

    case "user.deleted": {
      await supabase
        .from("users")
        .delete()
        .eq("id", data.id as string);

      const ph = getPostHogClient();
      if (ph) {
        ph.capture({
          distinctId: data.id as string,
          event: "user_deleted",
        });
        await ph.shutdown();
      }
      break;
    }

    default:
      break;
  }

  return NextResponse.json({ received: true }, { status: 200 });
}