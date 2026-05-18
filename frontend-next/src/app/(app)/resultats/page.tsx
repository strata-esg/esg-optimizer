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
  Share2,
  Linkedin,
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

interface ESRSCoverage {
  E1_climate_change?: boolean;
  E2_pollution?: boolean;
  E3_water_marine?: boolean;
  E4_biodiversity?: boolean;
  E5_circular_economy?: boolean;
  S1_own_workforce?: boolean;
  S2_value_chain_workers?: boolean;
  S3_affected_communities?: boolean;
  S4_consumers?: boolean;
  G1_business_conduct?: boolean;
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
  esrs_coverage?: ESRSCoverage | null;
  share_token?: string | null;
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

interface CsrdStage {
  label: string;
  desc: string;
  bg: string;
  border: string;
  color: string;
  isReady: boolean;
}

function getCsrdStage(coveragePct?: number | null, csrdReady?: boolean | null): CsrdStage {
  const pct = coveragePct ?? (csrdReady ? 87 : 28);
  if (pct >= 85)
    return { label: "CSRD Ready", desc: "Votre rapport répond aux principales exigences de la CSRD.", bg: "#D4F0D8", border: "#1A3D22", color: "#1A3D22", isReady: true };
  if (pct >= 70)
    return { label: "Avancé", desc: "Bonne couverture CSRD. Quelques points restent à finaliser.", bg: "#DCFCE7", border: "#16A34A", color: "#15803D", isReady: false };
  if (pct >= 50)
    return { label: "En développement", desc: "Environ la moitié des exigences est couverte. Des axes importants restent à traiter.", bg: "#FEF3C7", border: "#D97706", color: "#92400E", isReady: false };
  if (pct >= 30)
    return { label: "Initié", desc: "Des bases existent mais des lacunes importantes subsistent. Des efforts significatifs sont requis.", bg: "#FED7AA", border: "#EA580C", color: "#9A3412", isReady: false };
  return { label: "Non conforme", desc: "Lacunes majeures. Une refonte complète de votre approche CSRD est nécessaire.", bg: "#FEE2E2", border: "#DC2626", color: "#991B1B", isReady: false };
}

function ScoreBadge({ score }: { score: number }) {
  const style = scorePalette(score);
  return (
    <div className="inline-flex flex-col items-center rounded-xl px-8 py-5 border-2" style={{ background: style.bg, borderColor: style.border }}>
      <span className="text-5xl leading-none" style={{ fontFamily: "DM Serif Display, Georgia, serif", color: style.text }}>
        {score}
      </span>
      <span className="text-xs mt-1 uppercase tracking-widest font-medium" style={{ color: style.text }}>
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
        <span className="font-semibold" style={{ color }}>{score}/100</span>
      </div>
      <div className="w-full h-2 bg-[#E5E0D8] rounded-full">
        <div className="h-full rounded-full transition-all" style={{ width: `${score}%`, background: color }} />
      </div>
    </div>
  );
}

const ESRS_MAP: { key: keyof ESRSCoverage; code: string; label: string; pillar: "E" | "S" | "G" }[] = [
  { key: "E1_climate_change", code: "E1", label: "Changement climatique", pillar: "E" },
  { key: "E2_pollution", code: "E2", label: "Pollution", pillar: "E" },
  { key: "E3_water_marine", code: "E3", label: "Ressources marines & eau", pillar: "E" },
  { key: "E4_biodiversity", code: "E4", label: "Biodiversité & écosystèmes", pillar: "E" },
  { key: "E5_circular_economy", code: "E5", label: "Économie circulaire", pillar: "E" },
  { key: "S1_own_workforce", code: "S1", label: "Effectifs propres", pillar: "S" },
  { key: "S2_value_chain_workers", code: "S2", label: "Chaîne de valeur", pillar: "S" },
  { key: "S3_affected_communities", code: "S3", label: "Communautés affectées", pillar: "S" },
  { key: "S4_consumers", code: "S4", label: "Consommateurs", pillar: "S" },
  { key: "G1_business_conduct", code: "G1", label: "Conduite des affaires", pillar: "G" },
];

function pillarStyle(pillar: "E" | "S" | "G") {
  if (pillar === "E") return { bg: "#D4F0D8", text: "#1A3D22", border: "#7FC686" };
  if (pillar === "S") return { bg: "#DBEAFE", text: "#1e40af", border: "#93C5FD" };
  return { bg: "#FEF3C7", text: "#92400E", border: "#FCD34D" };
}

function ESRSGrid({ coverage }: { coverage: ESRSCoverage }) {
  const covered = ESRS_MAP.filter((e) => coverage[e.key] === true);
  const missing = ESRS_MAP.filter((e) => !coverage[e.key]);
  return (
    <div className="card mb-8">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl text-[#1A3D22]" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
          Couverture ESRS
        </h3>
        <span className="text-sm font-semibold text-[#6B7280]">{covered.length} / {ESRS_MAP.length} couverts</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {ESRS_MAP.map(({ key, code, label, pillar }) => {
          const isCovered = coverage[key] === true;
          const ps = pillarStyle(pillar);
          return (
            <div key={code} className="flex items-center gap-3 px-3 py-2 rounded-lg border" style={{ background: isCovered ? ps.bg : "#F9FAFB", borderColor: isCovered ? ps.border : "#E5E0D8", opacity: isCovered ? 1 : 0.65 }}>
              <span className="font-mono text-xs font-bold w-7 shrink-0" style={{ color: isCovered ? ps.text : "#9CA3AF" }}>{code}</span>
              <span className="text-sm flex-1" style={{ color: isCovered ? ps.text : "#9CA3AF" }}>{label}</span>
              {isCovered
                ? <CheckCircle className="w-4 h-4 shrink-0" style={{ color: ps.text }} />
                : <span className="text-[#B53030] text-sm font-bold shrink-0">✕</span>
              }
            </div>
          );
        })}
      </div>
      {missing.length > 0 && (
        <p className="text-xs text-[#6B7280] mt-3">
          {missing.length} standard{missing.length > 1 ? "s" : ""} non couvert{missing.length > 1 ? "s" : ""} :{" "}
          <span className="font-medium text-[#B53030]">{missing.map((e) => e.code).join(", ")}</span>
        </p>
      )}
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

  if (!analysisId) {
    let history: HistoryItem[] = [];
    try {
      if (token) {
        const res = await apiClient(token).get<{ analyses?: HistoryItem[] }>("/history?per_page=20");
        history = res.analyses ?? [];
      }
    } catch { history = []; }

    return (
      <div className="w-full">
        <h1 className="text-4xl text-[#1A3D22] mb-2" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
          Historique des analyses
        </h1>
        <p className="text-[#6B7280] mb-8">Cliquez sur une analyse pour voir le détail</p>
        {history.length === 0 ? (
          <div className="card text-center py-16">
            <BarChart2 className="w-12 h-12 mx-auto mb-3 text-[#E5E0D8]" />
            <p className="text-[#6B7280] font-medium">Aucune analyse pour le moment</p>
            <Link href="/upload" className="btn-primary mt-4 inline-flex">Analyser mon premier rapport</Link>
          </div>
        ) : (
          <div className="space-y-3">
            {history.map((a) => {
              const score = round(a.score_global);
              const palette = scorePalette(score);
              const done = a.status === "success";
              return (
                <Link key={a.id} href={`/resultats?id=${a.id}`} className="card flex items-center justify-between hover:shadow-md transition-all">
                  <div>
                    <p className="font-semibold text-[#1C1C1C]">{a.company_name}</p>
                    <p className="text-sm text-[#6B7280]">
                      {a.report_year ?? "Année non précisée"} · {new Date(a.created_at).toLocaleDateString("fr-FR")}
                    </p>
                  </div>
                  {done ? (
                    <span className="px-3 py-1 rounded-full text-sm font-bold" style={{ background: palette.bg, color: palette.text }}>{score}/100</span>
                  ) : (
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-[#F7F2E8] text-[#6B7280] border border-[#E5E0D8]">{STATUS_LABELS[a.status] ?? a.status}</span>
                  )}
                </Link>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  let analysis: Analysis | null = null;
  if (token) {
    try { analysis = await apiClient(token).get<Analysis>(`/analysis/${analysisId}`); }
    catch { analysis = null; }
  }

  if (!analysis) {
    return (
      <div className="w-full">
        <div className="card text-center py-16">
          <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-[#D97706]" />
          <p className="text-[#1C1C1C] font-medium">Analyse introuvable</p>
          <Link href="/resultats" className="btn-secondary mt-4 inline-flex">Retour à l&apos;historique</Link>
        </div>
      </div>
    );
  }

  const backLink = (
    <Link href="/resultats" className="inline-flex items-center gap-2 text-sm text-[#6B7280] hover:text-[#1A3D22] mb-6 transition-colors">
      <ArrowLeft className="w-4 h-4" /> Retour à l&apos;historique
    </Link>
  );

  const header = (
    <div className="mb-8">
      <h1 className="text-4xl text-[#1A3D22] mb-1" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
        {analysis.company_name ?? "Analyse"}
      </h1>
      <p className="text-[#6B7280]">
        {analysis.report_year ? `Rapport ${analysis.report_year} · ` : ""}
        Soumis le {new Date(analysis.created_at).toLocaleDateString("fr-FR")}
      </p>
    </div>
  );

  if (analysis.status === "pending" || analysis.status === "processing") {
    return (
      <div className="w-full">{backLink}{header}
        <div className="card text-center py-16">
          <div className="w-14 h-14 bg-[#D4F0D8] rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Clock className="w-7 h-7 text-[#1A3D22]" />
          </div>
          <p className="text-[#1C1C1C] font-medium mb-1">Analyse en cours</p>
          <p className="text-sm text-[#6B7280] max-w-md mx-auto">Notre moteur examine votre rapport. Cela prend généralement quelques minutes.</p>
          <Link href={`/resultats?id=${analysis.id}`} className="btn-secondary mt-5 inline-flex"><RefreshCw className="w-4 h-4" />Actualiser</Link>
        </div>
      </div>
    );
  }

  if (analysis.status === "failed") {
    return (
      <div className="w-full">{backLink}{header}
        <div className="card text-center py-16">
          <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-[#B53030]" />
          <p className="text-[#1C1C1C] font-medium mb-1">L&apos;analyse a échoué</p>
          <p className="text-sm text-[#6B7280] max-w-md mx-auto">{analysis.error_message ?? "Le rapport n'a pas pu être traité. Vérifiez le fichier et réessayez."}</p>
          <Link href="/upload" className="btn-primary mt-5 inline-flex">Relancer une analyse</Link>
        </div>
      </div>
    );
  }

  const scoreGlobal = round(analysis.score_global);
  const csrdStage = getCsrdStage(analysis.csrd_coverage_pct, analysis.csrd_ready);
  const strengths = analysis.strengths ?? [];
  const weaknesses = analysis.weaknesses ?? [];
  const recommendations = (analysis.recommendations ?? []).slice().sort((a, b) => (a.priority ?? 99) - (b.priority ?? 99));
  const linkedInShareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(`https://esg-optimizer.fr/resultats?id=${analysis.id}`)}`;

  return (
    <div className="w-full">
      {backLink}

      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-4xl text-[#1A3D22] mb-1" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
            {analysis.company_name ?? "Analyse"}
          </h1>
          <p className="text-[#6B7280]">
            {analysis.report_year ? `Rapport ${analysis.report_year} · ` : ""}
            Analysé le {new Date(analysis.created_at).toLocaleDateString("fr-FR")}
          </p>
        </div>
        <a href={`/api/analysis/${analysis.id}/pdf`} className="btn-secondary flex items-center gap-2 self-start">
          <Download className="w-4 h-4" />
          Rapport PDF
        </a>
      </div>

      {/* Badge CSRD multi-niveaux */}
      <div
        className="mb-6 rounded-xl px-5 py-4 flex flex-col sm:flex-row sm:items-center gap-3 border"
        style={{ background: csrdStage.bg, borderColor: csrdStage.border, color: csrdStage.color }}
      >
        <div className="flex items-center gap-3 flex-1">
          {csrdStage.isReady
            ? <CheckCircle className="w-5 h-5 flex-shrink-0" />
            : <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          }
          <div>
            <span className="font-bold text-sm">{csrdStage.label}</span>
            <span className="text-sm ml-2 opacity-80">{csrdStage.desc}</span>
          </div>
        </div>
        {analysis.csrd_coverage_pct != null && (
          <span className="font-bold text-sm shrink-0">Couverture {round(analysis.csrd_coverage_pct)}%</span>
        )}
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <div className="card flex items-center justify-center md:col-span-1">
          <ScoreBadge score={scoreGlobal} />
        </div>
        <div className="card md:col-span-2 space-y-4">
          <h3 className="text-lg text-[#1A3D22] mb-4" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>Scores par pilier</h3>
          <ScoreBar label="Environnement (E)" score={round(analysis.score_env)} />
          <ScoreBar label="Social (S)" score={round(analysis.score_social)} />
          <ScoreBar label="Gouvernance (G)" score={round(analysis.score_gov)} />
        </div>
      </div>

      {analysis.executive_summary && (
        <div className="card mb-8">
          <h3 className="text-xl text-[#1A3D22] mb-3" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>Synthèse</h3>
          <p className="text-sm text-[#1C1C1C] leading-relaxed whitespace-pre-line">{analysis.executive_summary}</p>
        </div>
      )}

      {/* Couverture ESRS */}
      {analysis.esrs_coverage && <ESRSGrid coverage={analysis.esrs_coverage} />}

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div className="card">
          <h3 className="font-semibold text-[#1A3D22] mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-[#7FC686]" />
            Points forts
          </h3>
          <ul className="space-y-2.5">
            {strengths.length > 0
              ? strengths.map((s, i) => (
                  <li key={i} className="text-sm text-[#1C1C1C] flex items-start gap-2">
                    <span className="text-[#7FC686] mt-0.5 font-bold">·</span>
                    <span>
                      {s.pillar && <span className="font-semibold text-[#1A3D22]">{s.pillar} : </span>}
                      {s.description}
                    </span>
                  </li>
                ))
              : <li className="text-sm text-[#6B7280]">Aucun point fort identifié.</li>
            }
          </ul>
        </div>
        <div className="card">
          <h3 className="font-semibold text-[#1A3D22] mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-[#D97706]" />
            Axes d&apos;amélioration
          </h3>
          <ul className="space-y-2.5">
            {weaknesses.length > 0
              ? weaknesses.map((w, i) => (
                  <li key={i} className="text-sm text-[#1C1C1C] flex items-start gap-2">
                    <span className="text-[#D97706] mt-0.5 font-bold">·</span>
                    <span>
                      {w.pillar && <span className="font-semibold text-[#1A3D22]">{w.pillar} : </span>}
                      {w.description}
                    </span>
                  </li>
                ))
              : <li className="text-sm text-[#6B7280]">Aucun axe d&apos;amélioration identifié.</li>
            }
          </ul>
        </div>
      </div>

      {recommendations.length > 0 && (
        <div className="card mb-8">
          <h3 className="text-xl text-[#1A3D22] mb-4" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>Recommandations prioritaires</h3>
          <ol className="space-y-3">
            {recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-3 text-sm border border-[#E5E0D8] rounded-lg px-4 py-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[#1A3D22] text-[#D4F0D8] flex items-center justify-center text-xs font-bold">
                  {rec.priority ?? i + 1}
                </span>
                <div>
                  <p className="text-[#1C1C1C] font-medium">{rec.action}</p>
                  {rec.expected_impact && <p className="text-[#6B7280] mt-0.5">Impact attendu : {rec.expected_impact}</p>}
                  {rec.esrs_reference && <p className="text-[#6B7280] mt-0.5 font-mono text-xs">{rec.esrs_reference}</p>}
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Badge LinkedIn */}
      <div className="card mb-8 border-0" style={{ background: "linear-gradient(135deg, #1A3D22 0%, #2A5C34 100%)" }}>
        <div className="flex flex-col sm:flex-row sm:items-center gap-5">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Share2 className="w-5 h-5 text-[#7FC686]" />
              <h3 className="text-lg text-white" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
                Partagez votre score sur LinkedIn
              </h3>
            </div>
            <p className="text-sm text-white/70 leading-relaxed">
              Téléchargez le badge PNG officiel (1200x630) et partagez-le sur LinkedIn pour valoriser votre engagement ESG.
            </p>
            <div className="mt-2 inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold" style={{ background: csrdStage.bg, color: csrdStage.color }}>
              {scoreGlobal}/100 · {csrdStage.label}
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 shrink-0">
            <a
              href={`/api/analysis/${analysis.id}/badge`}
              download={`badge-esg-${analysis.company_name ?? analysis.id}.png`}
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg font-semibold text-sm bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-all"
            >
              <Download className="w-4 h-4" />
              Télécharger le badge
            </a>
            <a
              href={linkedInShareUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg font-semibold text-sm transition-all text-[#1A3D22] hover:bg-[#D4F0D8]"
              style={{ background: "#7FC686" }}
            >
              <Linkedin className="w-4 h-4" />
              Partager sur LinkedIn
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
