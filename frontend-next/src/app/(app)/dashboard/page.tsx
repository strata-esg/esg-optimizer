import { auth, currentUser } from "@clerk/nextjs/server";
import Link from "next/link";
import { BarChart2, TrendingUp, FileText, ArrowUpRight, Upload } from "lucide-react";
import { apiClient } from "@/lib/api";

export default async function DashboardPage() {
  const { getToken } = await auth();
  const user = await currentUser();
  const token = await getToken();

  let stats = { total_analyses: 0, avg_score_global: null as number | null };
  let history: Array<{
    id: number;
    company_name: string;
    report_year: number;
    score_global: number;
    created_at: string;
  }> = [];

  try {
    if (token) {
      const [statsRes, histRes] = await Promise.all([
        apiClient(token).get<typeof stats>("/stats"),
        apiClient(token).get<{ analyses?: typeof history }>("/history?limit=5"),
      ]);
      stats = statsRes;
      history = histRes.analyses ?? [];
    }
  } catch {
    // Silently fail
  }

  const firstName = user?.firstName ?? "vous";

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1
          className="text-4xl text-[#1A3D22] mb-1"
          style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
        >
          Bonjour, {firstName}
        </h1>
        <p className="text-[#6B7280]">Vue d'ensemble de vos analyses ESG</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
        {[
          { label: "Analyses total", value: stats.total_analyses, icon: FileText, suffix: "" },
          {
            label: "Score moyen global",
            value: stats.avg_score_global != null ? stats.avg_score_global.toFixed(1) : "N/A",
            icon: BarChart2,
            suffix: stats.avg_score_global != null ? "/100" : "",
          },
          { label: "Ce mois", value: "N/A", icon: TrendingUp, suffix: "" },
          { label: "Ameliorations", value: "N/A", icon: ArrowUpRight, suffix: "" },
        ].map(({ label, value, icon: Icon, suffix }) => (
          <div key={label} className="card">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-[#6B7280] uppercase tracking-wide">
                {label}
              </span>
              <div className="w-8 h-8 bg-[#D4F0D8] rounded-lg flex items-center justify-center">
                <Icon className="w-4 h-4 text-[#1A3D22]" />
              </div>
            </div>
            <div
              className="text-3xl text-[#1A3D22]"
              style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
            >
              {value}
              {suffix && (
                <span className="text-base text-[#6B7280] font-sans ml-0.5">{suffix}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="card bg-gradient-to-r from-[#1A3D22] to-[#2A5C34] border-0 text-white mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-[#D4F0D8] mb-1">
              Analyser un nouveau rapport
            </h3>
            <p className="text-[#D4F0D8]/70 text-sm">
              PDF, DOCX ou XLSX - resultat en 3 minutes
            </p>
          </div>
          <Link
            href="/upload"
            className="flex items-center gap-2 bg-[#7FC686] text-[#1A3D22] font-semibold px-5 py-2.5 rounded-lg hover:bg-[#D4F0D8] transition-all"
          >
            <Upload className="w-4 h-4" />
            Uploader
          </Link>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3
            className="text-xl text-[#1A3D22]"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            Analyses recentes
          </h3>
          <Link
            href="/resultats"
            className="text-sm font-medium text-[#1A3D22] hover:text-[#2A5C34] flex items-center gap-1"
          >
            Tout voir <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {history.length === 0 ? (
          <div className="text-center py-12 text-[#6B7280]">
            <BarChart2 className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="font-medium">Aucune analyse pour l'instant</p>
            <p className="text-sm mt-1">Uploadez votre premier rapport pour commencer</p>
            <Link href="/upload" className="btn-primary mt-4 inline-flex">
              Premier upload
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((a) => {
              const scoreColor =
                a.score_global >= 70
                  ? "text-[#1A3D22] bg-[#D4F0D8]"
                  : a.score_global >= 40
                  ? "text-[#D97706] bg-[#FEF3C7]"
                  : "text-[#DC2626] bg-[#FEE2E2]";
              return (
                <Link
                  key={a.id}
                  href={`/resultats?id=${a.id}`}
                  className="flex items-center justify-between p-4 rounded-lg border border-[#E5E0D8] hover:bg-[#F7F2E8] transition-all"
                >
                  <div>
                    <p className="font-medium text-[#1C1C1C]">{a.company_name}</p>
                    <p className="text-xs text-[#6B7280]">
                      {a.report_year} - {new Date(a.created_at).toLocaleDateString("fr-FR")}
                    </p>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-sm font-semibold ${scoreColor}`}>
                    {a.score_global}/100
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
