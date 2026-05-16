import { auth } from "@clerk/nextjs/server";
import Link from "next/link";
import {
  BarChart2,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Download,
  ArrowLeft,
  Clock,
  RefreshCw,
} from "lucide-react";
import { apiClient } from "@/lib/api";

interface PageProps {
  searchParams: { id?: string };
}

interface PillarNote {
  pillar?: string;
  description?: string;
}

interface Recommendation {
  priority?: number;
  pillar?: string;
  action?: string;
  expected_impact?: string;
  esrs_reference?: string;
}

interface Analysis {
  id: number;
  company_name?: string | null;
  report_year?: number | null;
  status: string;
  error_message?: string | null;
  created_at: string;
  score_env?: number | null;
  score_social?: number | null;
  score_gov?: number | null;
  score_global?: number | null;
  csrd_ready?: boolean | null;
  csrd_coverage_pct?: number | null;
  strengths?: PillarNote[] | null;
  weaknesses?: PillarNote[] | null;
  recommendations?: Recommendation[] | null;
  executive_summary?: string | null;
}

interface HistoryItem {
  id: number;
  company_name: string;
  report_year: number | null;
  score_global: number | null;
  status: string;
  created_at: string;
}

function round(value?: number | null): number {
  return value != null ? Math.round(value) : 0;
}

function scorePalette(score: number) {
  if (score >= 70) return { bg: "#D4F0D8", border: "#1A3D22", text: "#1A3D22" };
  if (score >= 40) return { bg: "#FEF3C7", border: "#D97706", text: "#D97706" };
  return { bg: "#FEE2E2", border: "#B53030", text: "#B53030" };
}

function ScoreBadge({ score }: { score: number }) {
  const style = scorePalette(score);
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
  const color = score >= 70 ? "#1A3D22" : score >= 40 ? "#D97706" : "#B53030";
  return (
    <div>
      <div className="flex justify-between text-sm mb-1.5">
        <span className="font-medium text-[#1C1C1C]">{label}</span>
        <span className="font-semibold" style={{ color }}>
          {score}/100
        </span>
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

const STATUS_LABELS: Record<string, string> = {
  pending: "En file d'attente",
  processing: "Analyse en cours",
  success: "Terminée",
  failed: "Échec",
};

export default async function ResultatsPage({ searchParams }: PageProps) {
  const { getToken } = await auth();
  const token = await getToken();
  const analysisId = searchParams.id;

  // ---- Vue liste : historique des analyses ----------------------------------
  if (!analysisId) {
    let history: HistoryItem[] = [];
    try {
      if (token) {
        const res = await apiClient(token).get<{ analyses?: HistoryItem[] }>(
          "/history?per_page=20",
        );
        history = res.analyses ?? [];
      }
    } catch {
      history = [];
    }

    return (
      <div className="w-full">
        <h1
          className="text-4xl text-[#1A3D22] mb-2"
          style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
        >
          Historique des analyses
        </h1>
        <p className="text-[#6B7280] mb-8">Cliquez sur une analyse pour voir le détail</p>

        {history.length === 0 ? (
          <div className="card text-center py-16">
            <BarChart2 className="w-12 h-12 mx-auto mb-3 text-[#E5E0D8]" />
            <p className="text-[#6B7280] font-medium">Aucune analyse pour le moment</p>
            <Link href="/upload" className="btn-primary mt-4 inline-flex">
              Analyser mon premier rapport
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((a) => {
              const score = round(a.score_global);
              const palette = scorePalette(score);
              const done = a.status === "success";
              return (
                <Link
                  key={a.id}
                  href={`/resultats?id=${a.id}`}
                  className="card flex items-center justify-between hover:shadow-md transition-all"
                >
                  <div>
                    <p className="font-semibold text-[#1C1C1C]">{a.company_name}</p>
                    <p className="text-sm text-[#6B7280]">
                      {a.report_year ?? "Année non précisée"} ·{" "}
                      {new Date(a.created_at).toLocaleDateString("fr-FR")}
                    </p>
                  </div>
                  {done ? (
                    <span
                      className="px-3 py-1 rounded-full text-sm font-bold"
                      style={{ background: palette.bg, color: palette.text }}
                    >
                      {score}/100
                    </span>
                  ) : (
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-[#F7F2E8] text-[#6B7280] border border-[#E5E0D8]">
                      {STATUS_LABELS[a.status] ?? a.status}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // ---- Vue détail : une analyse ---------------------------------------------
  let analysis: Analysis | null = null;
  if (token) {
    try {
      analysis = await apiClient(token).get<Analysis>(`/analysis/${analysisId}`);
    } catch {
      analysis = null;
    }
  }

  if (!analysis) {
    return (
      <div className="w-full">
        <div className="card text-center py-16">
          <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-[#D97706]" />
          <p className="text-[#1C1C1C] font-medium">Analyse introuvable</p>
          <Link href="/resultats" className="btn-secondary mt-4 inline-flex">
            Retour à l&apos;historique
          </Link>
        </div>
      </div>
    );
  }

  const backLink = (
    <Link
      href="/resultats"
      className="inline-flex items-center gap-2 text-sm text-[#6B7280] hover:text-[#1A3D22] mb-6 transition-colors"
    >
      <ArrowLeft className="w-4 h-4" /> Retour à l&apos;historique
    </Link>
  );

  const header = (
    <div className="mb-8">
      <h1
        className="text-4xl text-[#1A3D22] mb-1"
        style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
      >
        {analysis.company_name ?? "Analyse"}
      </h1>
      <p className="text-[#6B7280]">
        {analysis.report_year ? `Rapport ${analysis.report_year} · ` : ""}
        Soumis le {new Date(analysis.created_at).toLocaleDateString("fr-FR")}
      </p>
    </div>
  );

  // Analyse encore en traitement
  if (analysis.status === "pending" || analysis.status === "processing") {
    return (
      <div className="w-full">
        {backLink}
        {header}
        <div className="card text-center py-16">
          <div className="w-14 h-14 bg-[#D4F0D8] rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Clock className="w-7 h-7 text-[#1A3D22]" />
          </div>
          <p className="text-[#1C1C1C] font-medium mb-1">Analyse en cours</p>
          <p className="text-sm text-[#6B7280] max-w-md mx-auto">
            Notre moteur examine votre rapport. Cela prend généralement quelques
            minutes selon la taille du document.
          </p>
          <Link
            href={`/resultats?id=${analysis.id}`}
            className="btn-secondary mt-5 inline-flex"
          >
            <RefreshCw className="w-4 h-4" />
            Actualiser
          </Link>
        </div>
      </div>
    );
  }

  // Analyse en échec
  if (analysis.status === "failed") {
    return (
      <div className="w-full">
        {backLink}
        {header}
        <div className="card text-center py-16">
          <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-[#B53030]" />
          <p className="text-[#1C1C1C] font-medium mb-1">L&apos;analyse a échoué</p>
          <p className="text-sm text-[#6B7280] max-w-md mx-auto">
            {analysis.error_message ??
              "Le rapport n'a pas pu être traité. Vérifiez le fichier et réessayez."}
          </p>
          <Link href="/upload" className="btn-primary mt-5 inline-flex">
            Relancer une analyse
          </Link>
        </div>
      </div>
    );
  }

  // Analyse terminée
  const scoreGlobal = round(analysis.score_global);
  const strengths = analysis.strengths ?? [];
  const weaknesses = analysis.weaknesses ?? [];
  const recommendations = (analysis.recommendations ?? [])
    .slice()
    .sort((a, b) => (a.priority ?? 99) - (b.priority ?? 99));

  return (
    <div className="w-full">
      {backLink}

      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
        <div>
          <h1
            className="text-4xl text-[#1A3D22] mb-1"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            {analysis.company_name ?? "Analyse"}
          </h1>
          <p className="text-[#6B7280]">
            {analysis.report_year ? `Rapport ${analysis.report_year} · ` : ""}
            Analysé le {new Date(analysis.created_at).toLocaleDateString("fr-FR")}
          </p>
        </div>
        <a
          href={`/api/analysis/${analysis.id}/pdf`}
          className="btn-secondary flex items-center gap-2 self-start"
        >
          <Download className="w-4 h-4" />
          Rapport PDF
        </a>
      </div>

      {analysis.csrd_ready != null && (
        <div
          className="mb-6 rounded-xl px-5 py-4 text-sm font-medium flex items-center gap-3"
          style={{
            background: analysis.csrd_ready ? "#D4F0D8" : "#FEF3C7",
            color: analysis.csrd_ready ? "#1A3D22" : "#92400E",
          }}
        >
          {analysis.csrd_ready ? (
            <CheckCircle className="w-5 h-5 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          )}
          {analysis.csrd_ready
            ? "Ce rapport présente une couverture CSRD solide."
            : "Ce rapport n'est pas encore prêt pour la CSRD."}
          {analysis.csrd_coverage_pct != null && (
            <span className="ml-auto font-semibold">
              Couverture {round(analysis.csrd_coverage_pct)}%
            </span>
          )}
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="card flex items-center justify-center md:col-span-1">
          <ScoreBadge score={scoreGlobal} />
        </div>
        <div className="card md:col-span-2 space-y-4">
          <h3
            className="text-lg text-[#1A3D22] mb-4"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            Scores par pilier
          </h3>
          <ScoreBar label="Environnement (E)" score={round(analysis.score_env)} />
          <ScoreBar label="Social (S)" score={round(analysis.score_social)} />
          <ScoreBar label="Gouvernance (G)" score={round(analysis.score_gov)} />
        </div>
      </div>

      {analysis.executive_summary && (
        <div className="card mb-8">
          <h3
            className="text-xl text-[#1A3D22] mb-3"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            Synthèse
          </h3>
          <p className="text-sm text-[#1C1C1C] leading-relaxed whitespace-pre-line">
            {analysis.executive_summary}
          </p>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div className="card">
          <h3 className="font-semibold text-[#1A3D22] mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-[#7FC686]" />
            Points forts
          </h3>
          <ul className="space-y-2.5">
            {strengths.length > 0 ? (
              strengths.map((s, i) => (
                <li key={i} className="text-sm text-[#1C1C1C] flex items-start gap-2">
                  <span className="text-[#7FC686] mt-0.5 font-bold">·</span>
                  <span>
                    {s.pillar && (
                      <span className="font-semibold text-[#1A3D22]">{s.pillar} : </span>
                    )}
                    {s.description}
                  </span>
                </li>
              ))
            ) : (
              <li className="text-sm text-[#6B7280]">Aucun point fort identifié.</li>
            )}
          </ul>
        </div>
        <div className="card">
          <h3 className="font-semibold text-[#1A3D22] mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-[#D97706]" />
            Axes d&apos;amélioration
          </h3>
          <ul className="space-y-2.5">
            {weaknesses.length > 0 ? (
              weaknesses.map((w, i) => (
                <li key={i} className="text-sm text-[#1C1C1C] flex items-start gap-2">
                  <span className="text-[#D97706] mt-0.5 font-bold">·</span>
                  <span>
                    {w.pillar && (
                      <span className="font-semibold text-[#1A3D22]">{w.pillar} : </span>
                    )}
                    {w.description}
                  </span>
                </li>
              ))
            ) : (
              <li className="text-sm text-[#6B7280]">Aucun axe d&apos;amélioration identifié.</li>
            )}
          </ul>
        </div>
      </div>

      {recommendations.length > 0 && (
        <div className="card">
          <h3
            className="text-xl text-[#1A3D22] mb-4"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            Recommandations prioritaires
          </h3>
          <ol className="space-y-3">
            {recommendations.map((rec, i) => (
              <li
                key={i}
                className="flex items-start gap-3 text-sm border border-[#E5E0D8] rounded-lg px-4 py-3"
              >
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[#1A3D22] text-[#D4F0D8] flex items-center justify-center text-xs font-bold">
                  {rec.priority ?? i + 1}
                </span>
                <div>
                  <p className="text-[#1C1C1C] font-medium">{rec.action}</p>
                  {rec.expected_impact && (
                    <p className="text-[#6B7280] mt-0.5">Impact attendu : {rec.expected_impact}</p>
                  )}
                  {rec.esrs_reference && (
                    <p className="text-[#6B7280] mt-0.5 font-mono text-xs">{rec.esrs_reference}</p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
