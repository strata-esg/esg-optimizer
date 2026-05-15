/**
 * Proxy de téléchargement du rapport PDF.
 *
 * Le backend FastAPI protège la route /analysis/{id}/pdf par authentification.
 * Un lien <a> classique ne transporte pas le jeton de session : cette route
 * récupère le jeton côté serveur, appelle le backend, et renvoie le PDF au
 * navigateur.
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
    return NextResponse.json(
      { error: "Authentification requise." },
      { status: 401 },
    );
  }

  const upstream = await fetch(`${API_BASE}/analysis/${params.id}/pdf`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!upstream.ok) {
    return NextResponse.json(
      { error: "Le rapport PDF n'est pas encore disponible pour cette analyse." },
      { status: upstream.status },
    );
  }

  const fileBuffer = await upstream.arrayBuffer();
  const disposition =
    upstream.headers.get("Content-Disposition") ??
    `attachment; filename="rapport-esg-${params.id}.pdf"`;

  return new NextResponse(fileBuffer, {
    status: 200,
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": disposition,
    },
  });
}
