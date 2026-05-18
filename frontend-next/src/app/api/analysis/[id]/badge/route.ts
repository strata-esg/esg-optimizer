/**
 * Proxy du badge PNG LinkedIn.
 * Récupère le share_token via /analysis/{id}/share-info,
 * puis télécharge le badge depuis le backend et le renvoie au navigateur.
 */

import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";
import { API_BASE } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } },
) {
  const { getToken } = await auth();
  const token = await getToken();

  if (!token) {
    return NextResponse.json({ error: "Authentification requise." }, { status: 401 });
  }

  // 1. Récupérer le share_token
  const infoRes = await fetch(`${API_BASE}/analysis/${params.id}/share-info`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!infoRes.ok) {
    return NextResponse.json({ error: "Analyse introuvable." }, { status: infoRes.status });
  }

  const info = await infoRes.json();
  const shareToken: string | null = info?.share_token ?? null;

  if (!shareToken) {
    return NextResponse.json({ error: "Token de partage indisponible." }, { status: 404 });
  }

  // 2. Télécharger le badge PNG (endpoint public)
  const badgeRes = await fetch(`${API_BASE}/analysis/badge/${shareToken}`, {
    cache: "no-store",
  });

  if (!badgeRes.ok) {
    return NextResponse.json({ error: "Erreur génération badge." }, { status: badgeRes.status });
  }

  const buf = await badgeRes.arrayBuffer();

  return new NextResponse(buf, {
    status: 200,
    headers: {
      "Content-Type": "image/png",
      "Content-Disposition": `attachment; filename="badge-esg-${params.id}.png"`,
      "Cache-Control": "public, max-age=86400",
    },
  });
}
