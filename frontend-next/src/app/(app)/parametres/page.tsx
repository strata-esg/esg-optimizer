"use client";

import { UserProfile, useUser } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import {
  Crown,
  Bell,
  BellOff,
  Shield,
  BarChart2,
  Zap,
  ExternalLink,
  CheckCircle,
  User,
  Mail,
  Calendar,
  TrendingUp,
} from "lucide-react";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

const PLAN_LABELS: Record<string, { label: string; color: string; bg: string; limit: string }> = {
  discovery: { label: "Decouverte", color: "#6B7280", bg: "#F3F4F6", limit: "1 analyse offerte" },
  essential: { label: "Essentiel", color: "#1A3D22", bg: "#D4F0D8", limit: "Pay-per-use" },
  pro: { label: "Pro", color: "#1e40af", bg: "#DBEAFE", limit: "Analyses illimitees" },
  enterprise: { label: "Enterprise", color: "#7c3aed", bg: "#EDE9FE", limit: "Sur devis" },
};

interface UserInfo {
  plan: string;
  analyses_this_month: number;
  email_notifications: boolean;
}

export default function ParametresPage() {
  const { user } = useUser();
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [notifLoading, setNotifLoading] = useState(false);

  useEffect(() => {
    async function fetchInfo() {
      try {
        const token = await (window as unknown as { Clerk?: { session?: { getToken: () => Promise<string> } } }).Clerk?.session?.getToken();
        if (!token) return;
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) setUserInfo(await res.json());
      } catch {}
    }
    fetchInfo();
  }, []);

  async function toggleNotifications() {
    if (!userInfo) return;
    setNotifLoading(true);
    try {
      const token = await (window as unknown as { Clerk?: { session?: { getToken: () => Promise<string> } } }).Clerk?.session?.getToken();
      if (!token) return;
      const newVal = !userInfo.email_notifications;
      const res = await fetch(`${API_BASE}/email/preferences`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ email_notifications: newVal }),
      });
      if (res.ok) setUserInfo((prev) => prev ? { ...prev, email_notifications: newVal } : prev);
    } catch {} finally { setNotifLoading(false); }
  }

  const plan = userInfo?.plan ?? "discovery";
  const planInfo = PLAN_LABELS[plan] ?? PLAN_LABELS.discovery;
  const joinedDate = user?.createdAt ? new Date(user.createdAt).toLocaleDateString("fr-FR", { month: "long", year: "numeric" }) : null;

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1 className="text-4xl text-[#1A3D22] mb-2" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
          Parametres
        </h1>
        <p className="text-[#6B7280]">Gerez votre compte, votre plan et vos preferences.</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Colonne gauche - 2/3 */}
        <div className="lg:col-span-2 space-y-6">

          {/* Mon abonnement */}
          <div className="card">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: planInfo.bg }}>
                  <Crown className="w-5 h-5" style={{ color: planInfo.color }} />
                </div>
                <div>
                  <p className="text-xs text-[#6B7280] font-medium uppercase tracking-wider mb-0.5">Plan actuel</p>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold" style={{ color: planInfo.color }}>{planInfo.label}</span>
                    <span className="px-2 py-0.5 rounded-full text-xs font-medium" style={{ background: planInfo.bg, color: planInfo.color }}>
                      {planInfo.limit}
                    </span>
                  </div>
                </div>
              </div>
              {plan === "discovery" && (
                <a href="/plans" className="flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-sm bg-[#1A3D22] text-[#D4F0D8] hover:bg-[#2A5C34] transition-colors">
                  <Zap className="w-4 h-4" />
                  Passer a Pro
                </a>
              )}
            </div>
            <div className="mt-4 grid grid-cols-3 gap-3">
              <div className="bg-[#F7F2E8] rounded-lg px-4 py-3 text-center">
                <p className="text-2xl font-bold text-[#1A3D22]">{userInfo?.analyses_this_month ?? 0}</p>
                <p className="text-xs text-[#6B7280] mt-0.5">Analyses ce mois</p>
              </div>
              <div className="bg-[#F7F2E8] rounded-lg px-4 py-3 text-center">
                <p className="text-2xl font-bold text-[#1A3D22]">10</p>
                <p className="text-xs text-[#6B7280] mt-0.5">ESRS couverts</p>
              </div>
              <div className="bg-[#F7F2E8] rounded-lg px-4 py-3 text-center">
                <p className="text-2xl font-bold text-[#1A3D22]">3 min</p>
                <p className="text-xs text-[#6B7280] mt-0.5">Temps d&apos;analyse</p>
              </div>
            </div>
            {plan === "discovery" && (
              <div className="mt-4 bg-[#FEF3C7] border border-[#FCD34D] rounded-lg px-4 py-3 text-sm text-[#92400E]">
                <strong>Plan Decouverte :</strong> 1 analyse offerte. Passez au plan Essentiel ou Pro pour acceder aux rapports complets et a l&apos;historique.
              </div>
            )}
          </div>

          {/* Notifications */}
          <div className="card">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#DBEAFE] flex items-center justify-center">
                  {userInfo?.email_notifications ? <Bell className="w-5 h-5 text-[#1e40af]" /> : <BellOff className="w-5 h-5 text-[#6B7280]" />}
                </div>
                <div>
                  <p className="font-semibold text-[#1C1C1C]">Notifications par email</p>
                  <p className="text-xs text-[#6B7280]">
                    {userInfo?.email_notifications
                      ? "Emails d'analyse terminee et digest hebdomadaire actifs."
                      : "Notifications desactivees."}
                  </p>
                </div>
              </div>
              <button
                onClick={toggleNotifications}
                disabled={notifLoading || !userInfo}
                className="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none disabled:opacity-50"
                style={{ background: userInfo?.email_notifications ? "#1A3D22" : "#D1D5DB" }}
              >
                <span
                  className="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
                  style={{ transform: userInfo?.email_notifications ? "translateX(22px)" : "translateX(2px)" }}
                />
              </button>
            </div>
          </div>

          {/* Donnees & confidentialite */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-[#D4F0D8] flex items-center justify-center">
                <Shield className="w-5 h-5 text-[#1A3D22]" />
              </div>
              <div>
                <p className="font-semibold text-[#1C1C1C]">Donnees &amp; confidentialite</p>
                <p className="text-xs text-[#6B7280]">Conformite RGPD. Vos fichiers sont supprimes apres extraction.</p>
              </div>
            </div>
            <div className="grid sm:grid-cols-2 gap-3 text-sm text-[#6B7280]">
              {[
                "Fichiers supprimes immediatement apres extraction",
                "Hebergement en Europe (Google Cloud, Belgique)",
                "Resultats d'analyse conserves dans votre espace",
                "Adresses IP hashees SHA-256, jamais stockees en clair",
              ].map((item) => (
                <div key={item} className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-[#1A3D22] shrink-0 mt-0.5" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
              <a href="mailto:contact@esg-optimizer.fr?subject=Suppression compte" className="text-sm text-[#B53030] hover:underline">
                Demander la suppression de mon compte
              </a>
              <span className="text-[#E5E0D8]">·</span>
              <a href="/mentions" className="text-sm text-[#6B7280] hover:text-[#1A3D22] flex items-center gap-1">
                Mentions legales &amp; RGPD <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          {/* Profil Clerk */}
          <div>
            <p className="text-sm font-semibold text-[#1C1C1C] mb-3">Informations du compte</p>
            <div className="rounded-xl border border-[#E5E0D8] bg-white shadow-sm overflow-hidden">
              <UserProfile
                routing="hash"
                appearance={{
                  elements: {
                    rootBox: "w-full",
                    cardBox: "w-full max-w-full shadow-none border-0 rounded-none",
                    card: "w-full max-w-full shadow-none border-0 rounded-none",
                    navbar: "border-r border-[#E5E0D8] bg-[#F7F2E8]",
                    navbarButton: "text-[#1C1C1C] hover:text-[#1A3D22] hover:bg-white transition-colors",
                    navbarButtonActive: "text-[#1A3D22] bg-white font-semibold",
                    scrollBox: "w-full",
                    pageScrollBox: "w-full",
                    header: "text-[#1A3D22]",
                    formButtonPrimary: "bg-[#1A3D22] hover:bg-[#2A5C34] text-[#D4F0D8] rounded-lg normal-case",
                    formFieldInput: "border-[#E5E0D8] rounded-lg focus:border-[#1A3D22] focus:ring-[#1A3D22]/10",
                    profileSectionPrimaryButton: "text-[#1A3D22]",
                    badge: "bg-[#D4F0D8] text-[#1A3D22]",
                    footer: "hidden",
                  },
                  variables: {
                    colorPrimary: "#1A3D22",
                    colorText: "#1C1C1C",
                    colorTextSecondary: "#6B7280",
                    borderRadius: "0.625rem",
                  },
                }}
              />
            </div>
          </div>
        </div>

        {/* Colonne droite - 1/3 */}
        <div className="space-y-6">

          {/* Profil resume */}
          <div className="card text-center">
            <div className="w-16 h-16 rounded-full bg-[#D4F0D8] flex items-center justify-center mx-auto mb-3">
              {user?.imageUrl
                ? <img src={user.imageUrl} alt="avatar" className="w-16 h-16 rounded-full object-cover" />
                : <User className="w-8 h-8 text-[#1A3D22]" />
              }
            </div>
            <p className="font-bold text-[#1C1C1C] text-lg">{user?.fullName ?? user?.firstName ?? "Utilisateur"}</p>
            <p className="text-xs text-[#6B7280] mt-0.5 flex items-center justify-center gap-1">
              <Mail className="w-3 h-3" />
              {user?.primaryEmailAddress?.emailAddress ?? ""}
            </p>
            {joinedDate && (
              <p className="text-xs text-[#6B7280] mt-1 flex items-center justify-center gap-1">
                <Calendar className="w-3 h-3" />
                Membre depuis {joinedDate}
              </p>
            )}
            <div className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold" style={{ background: planInfo.bg, color: planInfo.color }}>
              <Crown className="w-3 h-3" />
              {planInfo.label}
            </div>
          </div>

          {/* Raccourcis */}
          <div className="card">
            <p className="text-sm font-semibold text-[#1C1C1C] mb-3 flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-[#7c3aed]" />
              Raccourcis
            </p>
            <div className="space-y-2">
              <a href="/upload" className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-[#E5E0D8] hover:border-[#1A3D22] hover:bg-[#F7F2E8] transition-all group">
                <div className="w-7 h-7 rounded-lg bg-[#D4F0D8] flex items-center justify-center shrink-0">
                  <Zap className="w-3.5 h-3.5 text-[#1A3D22]" />
                </div>
                <span className="text-sm font-medium text-[#1C1C1C] group-hover:text-[#1A3D22]">Nouvelle analyse</span>
              </a>
              <a href="/resultats" className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-[#E5E0D8] hover:border-[#1A3D22] hover:bg-[#F7F2E8] transition-all group">
                <div className="w-7 h-7 rounded-lg bg-[#DBEAFE] flex items-center justify-center shrink-0">
                  <BarChart2 className="w-3.5 h-3.5 text-[#1e40af]" />
                </div>
                <span className="text-sm font-medium text-[#1C1C1C] group-hover:text-[#1A3D22]">Mes resultats</span>
              </a>
              <a href="/plans" className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-[#E5E0D8] hover:border-[#1A3D22] hover:bg-[#F7F2E8] transition-all group">
                <div className="w-7 h-7 rounded-lg bg-[#FEF3C7] flex items-center justify-center shrink-0">
                  <Crown className="w-3.5 h-3.5 text-[#D97706]" />
                </div>
                <span className="text-sm font-medium text-[#1C1C1C] group-hover:text-[#1A3D22]">Mes plans</span>
              </a>
              <a href="mailto:contact@esg-optimizer.fr" className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-[#E5E0D8] hover:border-[#1A3D22] hover:bg-[#F7F2E8] transition-all group">
                <div className="w-7 h-7 rounded-lg bg-[#F3F4F6] flex items-center justify-center shrink-0">
                  <ExternalLink className="w-3.5 h-3.5 text-[#6B7280]" />
                </div>
                <span className="text-sm font-medium text-[#1C1C1C] group-hover:text-[#1A3D22]">Support</span>
              </a>
            </div>
          </div>

          {/* Performance */}
          <div className="card">
            <p className="text-sm font-semibold text-[#1C1C1C] mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-[#1A3D22]" />
              Ce que vous couvrez
            </p>
            <div className="space-y-2.5">
              {[
                { label: "Standards ESRS", value: "10 / 10", color: "#1A3D22" },
                { label: "Piliers couverts", value: "E · S · G", color: "#1A3D22" },
                { label: "Analyse en", value: "3 min", color: "#1e40af" },
                { label: "Format acceptes", value: "PDF · DOCX · XLSX", color: "#6B7280" },
              ].map((row) => (
                <div key={row.label} className="flex items-center justify-between text-sm">
                  <span className="text-[#6B7280]">{row.label}</span>
                  <span className="font-semibold" style={{ color: row.color }}>{row.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* STRATA */}
          <div className="rounded-xl border border-[#E5E0D8] bg-[#F7F2E8] px-4 py-4">
            <p className="text-xs font-semibold text-[#1A3D22]/60 uppercase tracking-widest mb-2">A STRATA product</p>
            <p className="text-xs text-[#6B7280] leading-relaxed mb-3">
              ESG Optimizer est le produit flagship de STRATA, l&apos;OS for Sustainable Business pour les PME europeennes.
            </p>
            <a href="https://www.strata-esg.fr" target="_blank" rel="noopener noreferrer"
              className="text-xs font-semibold text-[#1A3D22] hover:underline flex items-center gap-1">
              strata-esg.fr <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
