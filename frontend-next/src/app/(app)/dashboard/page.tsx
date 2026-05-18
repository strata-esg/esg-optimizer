import { auth, currentUser } from "@clerk/nextjs/server";
import Link from "next/link";
import {
  BarChart2,
  TrendingUp,
  FileText,
  Upload,
  CheckCircle,
  XCircle,
  Clock,
  ArrowUpRight,
  Leaf,
  Users,
  Building2,
} from "lucide-react";
import { apiClient, API_BASE } from "@/lib/api";
import DeltaReport from "./DeltaReport";

interface AnalysisSummary {
  id: number;
  company_name: string;
  report_year: number | null;
  score_global: number | null;
  csrd_ready: boolean | null;
  status: string;
  created_at: string;
}

interface Stats {
  total_analyses: number;
  avg_score_global: number | null;
  avg_score_env: number | null;
  avg_score_social: number | null;
  avg_score_gov: number | null;
  csrd_ready_pct: number | null;
}

function scoreColor(score: number | null) {
  if (score == null) return { text: "text-[#9CA3AF]", bg: "bg-[#F9FAFB]", border: "border-[#E5E7EB]" };
  if (score >= 70) return { text: "text-[#1A3D22]", bg: "bg-[#D4F0D8]", border: "border-[#86EFAC]" };
  if (score >= 40) return { text: "text-[#D97706]", bg: "bg-[#FEF3C7]", border: "border-[#FDE68A]" };
  return { text: "text-[#DC2626]", bg: "bg-[#FEE2E2]", border: "border-[#FECACA]" };
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string; icon: React.ReactNode }> = {
    success: {
      label: "Terminé",
      cls: "bg-[#D1FAE5] text-[#065F46]",
      icon: <CheckCircle className="w-3 h-3" />,
    },
    processing: {
      label: "En cours",
      cls: "bg-[#DBEAFE] text-[#1E40AF]",
      icon: <Clock className="w-3 h-3 animate-pulse" />,
    },
    pending: {
      label: "En attente",
      cls: "bg-[#F3F4F6] text-[#6B7280]",
      icon: <Clock className="w-3 h-3" />,
    },
    failed: {
      label: "Échec",
      cls: "bg-[#FEE2E2] text-[#991B1B]",
      icon: <XCircle className="w-3 h-3" />,
    },
  };
  const { label, cls, icon } = map[status] ?? { label: status, cls: "bg-[#F3F4F6] text-[#6B7280]", icon: null };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${cls}`}>
      {icon}
      {label}
    </span>
  );
}

function MiniScoreBar({ score, color }: { score: number | null; color: string }) {
  const pct = score ?? 0;
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-[#F3F4F6] overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-xs font-semibold text-[#374151] w-6 text-right">
        {score != null ? score.toFixed(0) : "–"}
      </span>
    </div>
  );
}

export default async function DashboardPage() {
  const { getToken } = await auth();
  const user = await currentUser();
  const token = await getToken();

  let stats: Stats = {
    total_analyses: 0,
    avg_score_global: null,
    avg_score_env: null,
    avg_score_social: null,
    avg_score_gov: null,
    csrd_ready_pct: null,
  };
  let historyAll: AnalysisSummary[] = [];
  let userPlan = "discovery";

  try {
    if (token) {
      // Sync email Clerk si nécessaire
      const clerkEmail = user?.emailAddresses?.[0]?.emailAddress;
      if (clerkEmail) {
        try {
          await fetch(
            `${API_BASE}/auth/sync-email?email=${encodeURIComponent(clerkEmail)}`,
            { method: "PATCH", headers: { Authorization: `Bearer ${token}` }, cache: "no-store" }
          );
        } catch { /* Non bloquant */ }
      }

      const client = apiClient(token);
      const [statsRes, histAllRes, meRes] = await Promise.allSettled([
        client.get<Stats>("/history/stats"),
        client.get<{ analyses?: AnalysisSummary[] }>("/history?per_page=100"),
        client.get<{ plan?: string }>("/auth/me"),
      ]);

      if (statsRes.status === "fulfilled") stats = statsRes.value;
      if (histAllRes.status === "fulfilled") historyAll = histAllRes.value.analyses ?? [];
      if (meRes.status === "fulfilled") userPlan = meRes.value.plan ?? "discovery";
    }
  } catch { /* Dashboard vide si API indisponible */ }

  const firstName = user?.firstName ?? "";
  const isPaid = !["discovery", "free"].includes(userPlan);

  // Analyses récentes (5 dernières)
  const recentAnalyses = [...historyAll].slice(0, 5);

  // Regrouper par entreprise pour le delta
  const analysesByCompany: Record<string, AnalysisSummary[]> = {};
  for (const a of historyAll) {
    const key = a.company_name ?? "Entreprise inconnue";
    if (!analysesByCompany[key]) analysesByCompany[key] = [];
    analysesByCompany[key].push(a);
  }

  // Ce mois-ci
  const now = new Date();
  const cesMois = historyAll.filter((a) => {
    const d = new Date(a.created_at);
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth();
  }).length;

  // Nb entreprises uniques
  const nbCompanies = Object.keys(analysesByCompany).length;

  // Plan labels
  const planLabels: Record<string, string> = {
    discovery: "Découverte",
    free: "Gratuit",
    essential: "Essentiel",
    pro: "Pro",
    enterprise: "Entreprise",
  };

  return (
    <div className="w-full space-y-7">

      {/* HERO */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#1A3D22] via-[#2A5C34] to-[#3A7D3C] p-7">
        {/* Cercles décoratifs */}
        <div className="absolute -right-10 -top-10 w-48 h-48 rounded-full bg-white/5 pointer-events-none" />
        <div className="absolute -right-4 top-10 w-24 h-24 rounded-full bg-white/5 pointer-events-none" />
        <div className="absolute bottom-0 right-32 w-16 h-16 rounded-full bg-[#7FC686]/20 pointer-events-none" />

        <div className="relative flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <span className="inline-flex items-center gap-1.5 text-[#96D9A2] text-xs font-semibold bg-white/10 px-2.5 py-1 rounded-full mb-3">
              <Leaf className="w-3 h-3" />
              Plan {planLabels[userPlan] ?? userPlan}
            </span>
            <h1
              className="text-3xl md:text-4xl text-white mb-1"
              style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
            >
              {firstName ? `Bonjour, ${firstName}` : "Dashboard ESG"}
            </h1>
            <p className="text-[#96D9A2] text-sm">
              Vue d&apos;ensemble de vos analyses CSRD/ESRS
            </p>
          </div>
          <Link
            href="/upload"
            className="inline-flex items-center gap-2 bg-[#7FC686] text-[#1A3D22] font-semibold px-5 py-2.5 rounded-xl hover:bg-[#D4F0D8] transition-all text-sm flex-shrink-0"
          >
            <Upload className="w-4 h-4" />
            Nouvelle analyse
          </Link>
        </div>
      </div>

      {/* KPI CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: "Analyses totales",
            value: stats.total_analyses > 0 ? stats.total_analyses : "–",
            suffix: "",
            icon: FileText,
            iconBg: "bg-[#EFF6FF]",
            iconColor: "text-[#3B82F6]",
            sub: `${cesMois} ce mois`,
          },
          {
            label: "Score global moyen",
            value: stats.avg_score_global != null ? stats.avg_score_global.toFixed(1) : "–",
            suffix: stats.avg_score_global != null ? "/100" : "",
            icon: BarChart2,
            iconBg: "bg-[#D4F0D8]",
            iconColor: "text-[#1A3D22]",
            sub: "toutes analyses",
          },
          {
            label: "CSRD Ready",
            value: stats.csrd_ready_pct != null ? `${stats.csrd_ready_pct.toFixed(0)}%` : "–",
            suffix: "",
            icon: CheckCircle,
            iconBg: stats.csrd_ready_pct && stats.csrd_ready_pct >= 50 ? "bg-[#D4F0D8]" : "bg-[#FEF3C7]",
            iconColor: stats.csrd_ready_pct && stats.csrd_ready_pct >= 50 ? "text-[#1A3D22]" : "text-[#D97706]",
            sub: "des rapports analysés",
          },
          {
            label: "Entreprises suivies",
            value: nbCompanies > 0 ? nbCompanies : "–",
            suffix: "",
            icon: Building2,
            iconBg: "bg-[#F3E8FF]",
            iconColor: "text-[#7C3AED]",
            sub: "profils actifs",
          },
        ].map(({ label, value, suffix, icon: Icon, iconBg, iconColor, sub }) => (
          <div key={label} className="card">
            <div className="flex items-start justify-between mb-3">
              <span className="text-xs font-semibold text-[#6B7280] uppercase tracking-wide leading-tight">
                {label}
              </span>
              <div className={`w-8 h-8 ${iconBg} rounded-lg flex items-center justify-center flex-shrink-0`}>
                <Icon className={`w-4 h-4 ${iconColor}`} />
              </div>
            </div>
            <div
              className="text-3xl text-[#1A3D22] leading-none"
              style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
            >
              {value}
              {suffix && (
                <span className="text-base text-[#9CA3AF] font-sans ml-0.5">{suffix}</span>
              )}
            </div>
            <p className="text-xs text-[#9CA3AF] mt-1.5">{sub}</p>
          </div>
        ))}
      </div>

      {/* SCORES PILIERS */}
      {(stats.avg_score_env != null || stats.avg_score_social != null || stats.avg_score_gov != null) && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-[#1A3D22]">
              Scores moyens par pilier
            </h3>
            <span className="text-xs text-[#9CA3AF]">Sur toutes vos analyses</span>
          </div>
          <div className="space-y-3">
            {[
              { label: "Environnement (E)", score: stats.avg_score_env, color: "#1A3D22" },
              { label: "Social (S)", score: stats.avg_score_social, color: "#3B82F6" },
              { label: "Gouvernance (G)", score: stats.avg_score_gov, color: "#7C3AED" },
            ].map(({ label, score, color }) => (
              <div key={label}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-[#374151]">{label}</span>
                  <span className="text-sm font-semibold" style={{ color }}>
                    {score != null ? `${score.toFixed(1)}/100` : "–"}
                  </span>
                </div>
                <MiniScoreBar score={score} color={color} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* DELTA REPORT */}
      {Object.keys(analysesByCompany).length > 0 && (
        <DeltaReport analysesByCompany={analysesByCompany} userPlan={userPlan} />
      )}

      {/* ANALYSES RÉCENTES */}
      <div className="card">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#FEF3C7] flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-[#D97706]" />
            </div>
            <h2
              className="text-xl text-[#1A3D22]"
              style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
            >
              Analyses récentes
            </h2>
          </div>
          <Link
            href="/resultats"
            className="text-sm font-medium text-[#1A3D22] hover:text-[#2A5C34] flex items-center gap-1 transition-colors"
          >
            Tout voir <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {recentAnalyses.length === 0 ? (
          <div className="text-center py-14">
            <div className="w-16 h-16 bg-[#F7F2E8] rounded-2xl flex items-center justify-center mx-auto mb-4">
              <BarChart2 className="w-8 h-8 text-[#D4F0D8]" />
            </div>
            <p className="font-semibold text-[#374151] mb-1">Aucune analyse pour l&apos;instant</p>
            <p className="text-sm text-[#6B7280] mb-5">
              Uploadez votre premier rapport ESG pour commencer
            </p>
            <Link href="/upload" className="btn-primary">
              <Upload className="w-4 h-4" />
              Premier upload
            </Link>
          </div>
        ) : (
          <>
            {/* En-tête tableau */}
            <div className="hidden md:grid grid-cols-[2fr_1fr_1fr_1fr_auto] gap-4 px-3 mb-2">
              {["Entreprise", "Année", "Score", "CSRD", "Statut"].map((h) => (
                <span
                  key={h}
                  className="text-xs font-bold text-[#9CA3AF] uppercase tracking-wide"
                >
                  {h}
                </span>
              ))}
            </div>

            <div className="space-y-1.5">
              {recentAnalyses.map((a) => {
                const sc = scoreColor(a.score_global);
                return (
                  <Link
                    key={a.id}
                    href={`/resultats?id=${a.id}`}
                    className="grid grid-cols-[2fr_1fr_1fr] md:grid-cols-[2fr_1fr_1fr_1fr_auto] gap-4 items-center px-3 py-3.5 rounded-xl border border-transparent hover:border-[#E5E0D8] hover:bg-[#FAFAFA] transition-all group"
                  >
                    {/* Entreprise */}
                    <div>
                      <p className="font-semibold text-[#111827] text-sm group-hover:text-[#1A3D22] transition-colors">
                        {a.company_name}
                      </p>
                      <p className="text-xs text-[#9CA3AF]">
                        {new Date(a.created_at).toLocaleDateString("fr-FR", {
                          day: "numeric", month: "short", year: "numeric",
                        })}
                      </p>
                    </div>

                    {/* Année */}
                    <span className="text-sm text-[#6B7280]">
                      {a.report_year ?? "–"}
                    </span>

                    {/* Score */}
                    <div className={`hidden md:inline-flex items-baseline gap-0.5 px-2.5 py-1 rounded-lg ${sc.bg} w-fit`}>
                      <span
                        className={`text-lg font-bold ${sc.text}`}
                        style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
                      >
                        {a.score_global != null ? a.score_global.toFixed(0) : "–"}
                      </span>
                      {a.score_global != null && (
                        <span className={`text-xs ${sc.text} opacity-70`}>/100</span>
                      )}
                    </div>

                    {/* CSRD */}
                    <div className="hidden md:block">
                      {a.csrd_ready === true ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#065F46]">
                          <CheckCircle className="w-3.5 h-3.5" /> Ready
                        </span>
                      ) : a.csrd_ready === false ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-[#9CA3AF]">
                          <XCircle className="w-3.5 h-3.5" /> Non prêt
                        </span>
                      ) : (
                        <span className="text-xs text-[#9CA3AF]">–</span>
                      )}
                    </div>

                    {/* Statut */}
                    <div className="hidden md:block">
                      <StatusBadge status={a.status} />
                    </div>
                  </Link>
                );
              })}
            </div>

            {historyAll.length > 5 && (
              <div className="mt-4 pt-4 border-t border-[#F3F4F6] text-center">
                <Link
                  href="/resultats"
                  className="text-sm font-medium text-[#1A3D22] hover:underline"
                >
                  Voir les {historyAll.length - 5} autres analyses →
                </Link>
              </div>
            )}
          </>
        )}
      </div>

      {/* BANNIÈRE UPGRADE (plan gratuit) */}
      {!isPaid && (
        <div className="card bg-gradient-to-r from-[#FFFBEB] to-[#FEF3C7] border-[#FDE68A]">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <p className="font-semibold text-[#92400E] mb-1">
                Débloquez toutes les fonctionnalités
              </p>
              <p className="text-sm text-[#78350F]">
                Delta Report, export PDF complet, benchmark sectoriel et analyses illimitées.
              </p>
            </div>
            <Link
              href="/plans"
              className="inline-flex items-center gap-2 bg-[#D97706] text-white font-semibold px-5 py-2.5 rounded-xl hover:bg-[#B45309] transition-all text-sm flex-shrink-0"
            >
              Voir les plans
              <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
