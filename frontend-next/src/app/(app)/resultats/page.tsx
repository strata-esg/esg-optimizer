import { auth } from "@clerk/nextjs/server";
import Link from "next/link";
import { BarChart2, TrendingUp, AlertTriangle, CheckCircle, Download, ArrowLeft } from "lucide-react";
import { apiClient } from "@/lib/api";

interface PageProps {
  searchParams: { id?: string };
}

function ScoreBadge({ score }: { score: number }) {
  const isHigh = score >= 70;
  const isMid = score >= 40 && score < 70;
  const style = isHigh
    ? { bg: "#D4F0D8", border: "#1A3D22", text: "#1A3D22" }
    : isMid
    ? { bg: "#FEF3C7", border: "#D97706", text: "#D97706" }
    : { bg: "#FEE2E2", border: "#DC2626", text: "#DC2626" };

  return (
    <div
      className="inline-flex flex-col items-center rounded-xl px-8 py-5 border-2"
      style={{ background: style.bg, borderColor: style.border }}
    >
      <span
        className="text-5xl leading-none"
        style={{ fontFamily: "DM Serif Display, Georgia, serif", color: style.text }}
      >
        {score}
      </span>
      <span
        className="text-xs mt-1 uppercase tracking-widest font-medium"
        style={{ color: style.text }}
      >
        Score global
      </span>
    </div>
  );
}

function ScoreBar({ label, score }: { label: string; score: number }) {
  const color = score >= 70 ? "#1A3D22" : score >= 40 ? "#D97706" : "#DC2626";
  return (
    <div>
      <div className="flex justify-between text-sm mb-1.5">
        <span className="font-medium text-[#1C1C1C]">{label}</span>
        <span className="font-semibold" style={{ color }}>{score}/100</span>
      </div>
      <div className="w-full h-2 bg-[#E5E0D8] rounded-full">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${score}%`, background: color }}
        />
      </div>
    </div>
  );
}

export default async function ResultatsPage({ searchParams }: PageProps) {
  const { getToken } = await auth();
  const token = await getToken();
  const analysisId = searchParams.id;

  let analysis: Record<string, unknown> | null = null;

  if (analysisId && token) {
    try {
      analysis = await apiClient(token).get<Record<string, unknown>>(`/analysis/${analysisId}`);
    } catch {
      analysis = null;
    }
  }

  if (!analysisId) {
    let history: Array<Record<string, unknown>> = [];
    try {
      if (token) {
        const res = await apiClient(token).get<{ analyses?: typeof history }>("/history?limit=20");
        history = res.analyses ?? [];
      }
    } catch {/* */}

    return (
      <div className="w-full">
        <h1
          className="text-4xl text-[#1A3D22] mb-2"
          style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
        >
          Historique des analyses
        </h1>
        <p className="text-[#6B7280] mb-8">Cliquez sur une analyse pour voir le detail</p>

        {history.length === 0 ? (
          <div className="card text-center py-16">
            <BarChart2 className="w-12 h-12 mx-auto mb-3 text-[#E5E0D8]" />
            <p className="text-[#6B7280] font-medium">Aucune analyse</p>
            <Link href="/upload" className="btn-primary mt-4 inline-flex">
              Analyser mon premier rapport
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((a: Record<string, unknown>) => {
              const score = a.score_global as number;
              const scoreColor = score >= 70 ? "#D4F0D8" : score >= 40 ? "#FEF3C7" : "#FEE2E2";
              const textColor = score >= 70 ? "#1A3D22" : score >= 40 ? "#D97706" : "#DC2626";
              return (
                <Link
                  key={a.id as number}
                  href={`/resultats?id=${a.id}`}
                  className="card flex items-center justify-between hover:shadow-md transition-all"
                >
                  <div>
                    <p className="font-semibold text-[#1C1C1C]">{a.company_name as string}</p>
                    <p className="text-sm text-[#6B7280]">
                      {a.report_year as number} - {new Date(a.created_at as string).toLocaleDateString("fr-FR")}
                    </p>
                  </div>
                  <span
                    className="px-3 py-1 rounded-full text-sm font-bold"
                    style={{ background: scoreColor, color: textColor }}
                  >
                    {score}/100
                  </span>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="w-full">
        <div className="card text-center py-16">
          <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-[#D97706]" />
          <p className="text-[#1C1C1C] font-medium">Analyse introuvable</p>
          <Link href="/resultats" className="btn-secondary mt-4 inline-flex">
            Retour a l'historique
          </Link>
        </div>
      </div>
    );
  }

  const scores = (analysis.scores as Record<string, number>) ?? {};

  return (
    <div className="max-w-4xl">
      <Link
        href="/resultats"
        className="inline-flex items-center gap-2 text-sm text-[#6B7280] hover:text-[#1A3D22] mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Retour a l'historique
      </Link>

      <div className="flex items-start justify-between mb-8">
        <div>
          <h1
            className="text-4xl text-[#1A3D22] mb-1"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            {analysis.company_name as string}
          </h1>
          <p className="text-[#6B7280]">
            Rapport {analysis.report_year as number} - Analyse le{" "}
            {new Date(analysis.created_at as string).toLocaleDateString("fr-FR")}
          </p>
        </div>
        <a
          href={`${process.env.NEXT_PUBLIC_API_URL}/analysis/${analysisId}/report`}
          className="btn-secondary flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Export PDF
        </a>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="card flex items-center justify-center md:col-span-1">
          <ScoreBadge score={analysis.score_global as number} />
        </div>
        <div className="card md:col-span-2 space-y-4">
          <h3
            className="text-lg text-[#1A3D22] mb-4"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            Scores par pilier
          </h3>
          <ScoreBar label="Environnement (E)" score={scores.env ?? 0} />
          <ScoreBar label="Social (S)" score={scores.social ?? 0} />
          <ScoreBar label="Gouvernance (G)" score={scores.gov ?? 0} />
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div className="card">
          <h3 className="font-semibold text-[#1A3D22] mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-[#7FC686]" />
            Points forts
          </h3>
          <ul className="space-y-2">
            {((analysis.strengths as string[]) ?? ["—"]).map((s, i) => (
              <li key={i} className="text-sm text-[#1C1C1C] flex items-start gap-2">
                <span className="text-[#7FC686] mt-0.5">ok</span> {s}
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h3 className="font-semibold text-[#1A3D22] mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-[#D97706]" />
            Axes d'amelioration
          </h3>
          <ul className="space-y-2">
            {((analysis.improvements as string[]) ?? ["—"]).map((s, i) => (
              <li key={i} className="text-sm text-[#1C1C1C] flex items-start gap-2">
                <span className="text-[#D97706] mt-0.5">-&gt;</span> {s}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {!!analysis.recommendations && (
        <div className="card">
          <h3
            className="text-xl text-[#1A3D22] mb-4"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            Recommandations prioritaires
          </h3>
          <p className="text-sm text-[#1C1C1C] leading-relaxed whitespace-pre-line">
            {analysis.recommendations as string}
          </p>
        </div>
      )}
    </div>
  );
}
