"use client";

import { useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Sparkles,
  Loader2,
  ArrowRight,
  Info,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

interface AnalysisSummary {
  id: number;
  company_name: string;
  report_year: number | null;
  score_global: number | null;
  csrd_ready: boolean | null;
  status: string;
  created_at: string;
}

interface FullAnalysis {
  id: number;
  company_name?: string | null;
  report_year?: number | null;
  score_env?: number | null;
  score_social?: number | null;
  score_gov?: number | null;
  score_global?: number | null;
  delta_env?: number | null;
  delta_social?: number | null;
  delta_gov?: number | null;
  delta_global?: number | null;
  delta_narrative?: string | null;
}

interface DeltaNarrative {
  delta_summary?: string;
  key_improvements?: Array<{ pillar: string; description: string }>;
  key_regressions?: Array<{ pillar: string; description: string }>;
  priority_actions?: Array<{ priority: number; pillar: string; action: string; rationale?: string }>;
  esrs_evolution?: {
    gained?: string[];
    lost?: string[];
    coverage_previous?: number;
    coverage_current?: number;
  };
}

interface Props {
  analysesByCompany: Record<string, AnalysisSummary[]>;
  userPlan: string;
}

function deltaIcon(delta: number | null | undefined) {
  if (delta == null) return null;
  if (delta > 2) return <TrendingUp className="w-4 h-4" />;
  if (delta < -2) return <TrendingDown className="w-4 h-4" />;
  return <Minus className="w-4 h-4" />;
}

function deltaColor(delta: number | null | undefined): string {
  if (delta == null) return "text-[#9CA3AF]";
  if (delta > 5) return "text-[#1A3D22]";
  if (delta > 0) return "text-[#059669]";
  if (delta === 0) return "text-[#6B7280]";
  if (delta > -5) return "text-[#D97706]";
  return "text-[#DC2626]";
}

function deltaBg(delta: number | null | undefined): string {
  if (delta == null) return "bg-[#F9FAFB] border-[#E5E7EB]";
  if (delta > 5) return "bg-[#F0FDF4] border-[#86EFAC]";
  if (delta > 0) return "bg-[#F0FDF4] border-[#A7F3D0]";
  if (delta === 0) return "bg-[#F9FAFB] border-[#E5E7EB]";
  if (delta > -5) return "bg-[#FFFBEB] border-[#FDE68A]";
  return "bg-[#FEF2F2] border-[#FECACA]";
}

function deltaTrend(delta: number | null | undefined): string {
  if (delta == null) return "Non calculé";
  if (delta > 5) return "Forte amélioration";
  if (delta > 0) return "Amélioration";
  if (delta === 0) return "Stable";
  if (delta > -5) return "Légère dégradation";
  return "Dégradation";
}

function ScoreBar({ label, scoreN, scoreN1 }: { label: string; scoreN: number; scoreN1: number }) {
  const max = 100;
  const pctN = (scoreN / max) * 100;
  const pctN1 = (scoreN1 / max) * 100;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-[#6B7280] mb-0.5">
        <span className="font-medium">{label}</span>
        <span>{scoreN1} → <strong className="text-[#1A3D22]">{scoreN}</strong></span>
      </div>
      <div className="relative h-2 rounded-full bg-[#F3F4F6] overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-[#D1D5DB]"
          style={{ width: `${pctN1}%` }}
        />
      </div>
      <div className="relative h-2 rounded-full bg-[#F3F4F6] overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-[#1A3D22]"
          style={{ width: `${pctN}%` }}
        />
      </div>
    </div>
  );
}

export default function DeltaReport({ analysesByCompany, userPlan }: Props) {
  const { getToken } = useAuth();
  const isPaid = !["discovery", "free"].includes(userPlan);

  const companies = Object.keys(analysesByCompany);
  const companiesMultiple = companies.filter(
    (c) => analysesByCompany[c].filter((a) => a.status === "success").length >= 2
  );
  const companiesSingle = companies.filter(
    (c) => analysesByCompany[c].filter((a) => a.status === "success").length === 1
  );

  const [selected, setSelected] = useState<string>(companiesMultiple[0] ?? companiesSingle[0] ?? "");
  const [loading, setLoading] = useState(false);
  const [fullAnalysis, setFullAnalysis] = useState<FullAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [computed, setComputed] = useState(false);

  const successAnalyses = (analysesByCompany[selected] ?? [])
    .filter((a) => a.status === "success")
    .sort((a, b) => {
      const yr = (b.report_year ?? 0) - (a.report_year ?? 0);
      if (yr !== 0) return yr;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

  const analysisN = successAnalyses[0] ?? null;
  const analysisN1 = successAnalyses[1] ?? null;
  const hasMultiple = analysisN !== null && analysisN1 !== null;
  const isSingleOnly = !hasMultiple && successAnalyses.length === 1;

  const handleComputeDelta = useCallback(async () => {
    if (!analysisN) return;
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/analysis/${analysisN.id}/recompute-delta`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? `Erreur ${res.status}`);
      }
      // Recharger l'analyse complète
      const full = await fetch(`${API_BASE}/analysis/${analysisN.id}`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      if (full.ok) {
        const data: FullAnalysis = await full.json();
        setFullAnalysis(data);
        setComputed(true);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }, [analysisN, getToken]);

  const handleViewDelta = useCallback(async () => {
    if (!analysisN) return;
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/analysis/${analysisN.id}`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      if (res.ok) {
        const data: FullAnalysis = await res.json();
        setFullAnalysis(data);
      }
    } catch {
      //
    } finally {
      setLoading(false);
    }
  }, [analysisN, getToken]);

  const hasDelta = fullAnalysis &&
    [fullAnalysis.delta_env, fullAnalysis.delta_social, fullAnalysis.delta_gov, fullAnalysis.delta_global]
      .some((v) => v != null);

  let narrative: DeltaNarrative | null = null;
  if (fullAnalysis?.delta_narrative) {
    try {
      narrative = typeof fullAnalysis.delta_narrative === "string"
        ? JSON.parse(fullAnalysis.delta_narrative)
        : fullAnalysis.delta_narrative;
    } catch { /* */ }
  }

  if (companies.length === 0) return null;

  return (
    <section>
      {/* Titre section */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#3B82F6] to-[#6366F1] flex items-center justify-center">
          <TrendingUp className="w-4 h-4 text-white" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-[#1A3D22] leading-none">
            Delta Report
          </h2>
          <p className="text-xs text-[#6B7280] mt-0.5">Comparaison N vs N-1 par entreprise</p>
        </div>
        {!isPaid && (
          <span className="ml-auto text-xs font-semibold text-[#D97706] bg-[#FEF3C7] px-2.5 py-1 rounded-full border border-[#FDE68A]">
            Plan Essentiel requis
          </span>
        )}
      </div>

      <div className="card">
        {/* Sélecteur entreprise */}
        <div className="flex flex-wrap items-center gap-3 mb-5">
          <label className="text-sm font-medium text-[#374151]">Entreprise :</label>
          <div className="flex flex-wrap gap-2">
            {companies.map((c) => {
              const cnt = (analysesByCompany[c] ?? []).filter((a) => a.status === "success").length;
              const isMulti = cnt >= 2;
              return (
                <button
                  key={c}
                  onClick={() => {
                    setSelected(c);
                    setFullAnalysis(null);
                    setError(null);
                    setComputed(false);
                  }}
                  className={[
                    "px-3 py-1.5 rounded-lg text-sm font-medium border transition-all",
                    selected === c
                      ? "bg-[#1A3D22] text-white border-[#1A3D22]"
                      : "bg-white text-[#374151] border-[#E5E0D8] hover:border-[#1A3D22] hover:text-[#1A3D22]",
                  ].join(" ")}
                >
                  {c}
                  <span
                    className={[
                      "ml-1.5 text-xs px-1.5 py-0.5 rounded-full",
                      isMulti
                        ? selected === c ? "bg-[#7FC686]/40 text-white" : "bg-[#D4F0D8] text-[#1A3D22]"
                        : selected === c ? "bg-white/20 text-white" : "bg-[#F3F4F6] text-[#9CA3AF]",
                    ].join(" ")}
                  >
                    {cnt}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Notification : analyse unique */}
        {isSingleOnly && (
          <div className="flex items-start gap-3 p-4 rounded-xl bg-[#FFFBEB] border border-[#FDE68A]">
            <AlertTriangle className="w-5 h-5 text-[#D97706] flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-[#92400E] text-sm">
                Analyse unique pour <span className="italic">{selected}</span>
              </p>
              <p className="text-xs text-[#78350F] mt-1">
                Le Delta Report nécessite au moins deux analyses de la même entreprise.
                Importez le rapport de l&apos;année précédente pour comparer N vs N-1.
              </p>
            </div>
          </div>
        )}

        {/* Delta disponible */}
        {hasMultiple && (
          <>
            {/* Header comparaison */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-gradient-to-r from-[#EFF6FF] to-[#F0FDF4] border border-[#BFDBFE] mb-5">
              <div>
                <p className="text-xs font-semibold text-[#1E40AF] uppercase tracking-wide mb-1">
                  Comparaison active
                </p>
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-[#374151]">
                    {analysisN1.report_year ?? "N-1"} &nbsp;
                    <span className="text-[#9CA3AF] text-xs">
                      ({analysisN1.score_global != null ? `${analysisN1.score_global}/100` : "?"})
                    </span>
                  </span>
                  <ArrowRight className="w-4 h-4 text-[#6366F1]" />
                  <span className="font-semibold text-[#1A3D22]">
                    {analysisN.report_year ?? "N"} &nbsp;
                    <span className="text-[#9CA3AF] text-xs">
                      ({analysisN.score_global != null ? `${analysisN.score_global}/100` : "?"})
                    </span>
                  </span>
                </div>
                <p className="text-xs text-[#6B7280] mt-1 truncate max-w-sm">
                  {analysisN1.report_year ?? "N-1"}: {(analysisN1 as unknown as { source_filename?: string }).source_filename ?? `Analyse #${analysisN1.id}`}
                </p>
              </div>

              {/* Boutons action */}
              <div className="flex items-center gap-2 flex-shrink-0">
                {!isPaid ? (
                  <div className="flex items-center gap-1.5 text-xs text-[#9CA3AF]">
                    <Info className="w-3.5 h-3.5" />
                    Disponible dès le plan Essentiel
                  </div>
                ) : (
                  <>
                    {!fullAnalysis && (
                      <button
                        onClick={handleViewDelta}
                        disabled={loading}
                        className="btn-secondary text-sm px-4 py-2"
                      >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Voir le delta"}
                      </button>
                    )}
                    <button
                      onClick={handleComputeDelta}
                      disabled={loading}
                      className="btn-primary text-sm px-4 py-2 gap-1.5"
                    >
                      {loading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Sparkles className="w-4 h-4" />
                      )}
                      {computed ? "Recalculer le delta" : "Calculer le delta"}
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Erreur */}
            {error && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-[#FEF2F2] border border-[#FECACA] text-[#991B1B] text-sm mb-4">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            {/* Comparaison score global simple (toujours visible) */}
            {!fullAnalysis && analysisN.score_global != null && analysisN1.score_global != null && (
              <div className="grid grid-cols-2 gap-4 mb-2">
                <div className="text-center p-4 rounded-xl bg-[#F9FAFB] border border-[#E5E7EB]">
                  <p className="text-xs font-semibold text-[#9CA3AF] uppercase tracking-wide mb-2">
                    {analysisN1.report_year ?? "N-1"} — Score global
                  </p>
                  <p
                    className="text-4xl text-[#6B7280]"
                    style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
                  >
                    {analysisN1.score_global}
                    <span className="text-base text-[#9CA3AF]">/100</span>
                  </p>
                </div>
                <div className="text-center p-4 rounded-xl bg-[#F0FDF4] border border-[#86EFAC]">
                  <p className="text-xs font-semibold text-[#059669] uppercase tracking-wide mb-2">
                    {analysisN.report_year ?? "N"} — Score global
                  </p>
                  <p
                    className="text-4xl text-[#1A3D22]"
                    style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
                  >
                    {analysisN.score_global}
                    <span className="text-base text-[#6B7280]">/100</span>
                  </p>
                  {(() => {
                    const d = (analysisN.score_global ?? 0) - (analysisN1.score_global ?? 0);
                    const sign = d >= 0 ? "+" : "";
                    const col = d >= 0 ? "text-[#059669]" : "text-[#DC2626]";
                    return (
                      <p className={`text-sm font-semibold mt-1 ${col}`}>
                        {sign}{d.toFixed(1)} pts
                      </p>
                    );
                  })()}
                </div>
              </div>
            )}

            {/* Cartes delta détaillées (après calcul) */}
            {hasDelta && fullAnalysis && (
              <div className="mt-5 space-y-5">
                {/* 4 cartes piliers */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { label: "Environnement", delta: fullAnalysis.delta_env, score: fullAnalysis.score_env },
                    { label: "Social", delta: fullAnalysis.delta_social, score: fullAnalysis.score_social },
                    { label: "Gouvernance", delta: fullAnalysis.delta_gov, score: fullAnalysis.score_gov },
                    { label: "Global", delta: fullAnalysis.delta_global, score: fullAnalysis.score_global },
                  ].map(({ label, delta, score }) => (
                    <div
                      key={label}
                      className={`rounded-xl border-2 p-4 text-center ${deltaBg(delta)}`}
                    >
                      <p className="text-[0.65rem] font-bold text-[#6B7280] uppercase tracking-widest mb-2">
                        {label}
                      </p>
                      <div className={`flex items-center justify-center gap-1 text-2xl font-bold ${deltaColor(delta)}`}
                        style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
                      >
                        {deltaIcon(delta)}
                        <span>
                          {delta != null ? `${delta > 0 ? "+" : ""}${delta.toFixed(1)}` : "—"}
                        </span>
                      </div>
                      <p className={`text-xs font-medium mt-1.5 ${deltaColor(delta)}`}>
                        {deltaTrend(delta)}
                      </p>
                      {score != null && (
                        <p className="text-[0.68rem] text-[#9CA3AF] mt-1">
                          Score actuel : <span className="font-semibold text-[#374151]">{score.toFixed(0)}</span>/100
                        </p>
                      )}
                    </div>
                  ))}
                </div>

                {/* Barres de comparaison */}
                {fullAnalysis.score_env != null && analysisN1.score_global != null && (
                  <div className="p-4 rounded-xl bg-[#F9FAFB] border border-[#E5E7EB]">
                    <p className="text-xs font-semibold text-[#6B7280] uppercase tracking-wide mb-3">
                      Évolution par pilier
                    </p>
                    <div className="space-y-3">
                      {[
                        {
                          label: "Env.",
                          n: fullAnalysis.score_env ?? 0,
                          n1: (fullAnalysis.score_env ?? 0) - (fullAnalysis.delta_env ?? 0),
                        },
                        {
                          label: "Social",
                          n: fullAnalysis.score_social ?? 0,
                          n1: (fullAnalysis.score_social ?? 0) - (fullAnalysis.delta_social ?? 0),
                        },
                        {
                          label: "Gov.",
                          n: fullAnalysis.score_gov ?? 0,
                          n1: (fullAnalysis.score_gov ?? 0) - (fullAnalysis.delta_gov ?? 0),
                        },
                      ].map(({ label, n, n1 }) => (
                        <ScoreBar key={label} label={label} scoreN={Math.round(n)} scoreN1={Math.round(n1)} />
                      ))}
                    </div>
                    <div className="flex items-center gap-4 mt-3 text-xs text-[#6B7280]">
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-1.5 rounded bg-[#D1D5DB] inline-block" />
                        {analysisN1.report_year ?? "N-1"}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-1.5 rounded bg-[#1A3D22] inline-block" />
                        {analysisN.report_year ?? "N"}
                      </span>
                    </div>
                  </div>
                )}

                {/* Synthèse IA */}
                {narrative?.delta_summary && (
                  <div className="p-4 rounded-xl bg-[#F0FDF4] border border-[#86EFAC]">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="w-4 h-4 text-[#059669]" />
                      <p className="text-xs font-bold text-[#059669] uppercase tracking-wide">
                        Synthèse IA
                      </p>
                    </div>
                    <p className="text-sm text-[#14532D] leading-relaxed">{narrative.delta_summary}</p>
                  </div>
                )}

                {/* Améliorations & régressions */}
                {(narrative?.key_improvements?.length || narrative?.key_regressions?.length) ? (
                  <div className="grid md:grid-cols-2 gap-3">
                    {narrative.key_improvements && narrative.key_improvements.length > 0 && (
                      <div className="p-4 rounded-xl bg-[#F0FDF4] border border-[#A7F3D0]">
                        <p className="text-xs font-bold text-[#065F46] mb-2 uppercase tracking-wide">
                          ↑ Améliorations clés
                        </p>
                        <div className="space-y-1.5">
                          {narrative.key_improvements.map((item, i) => (
                            <div key={i} className="flex items-start gap-2 text-sm text-[#374151]">
                              <span className="px-1.5 py-0.5 rounded bg-[#D1FAE5] text-[#065F46] text-[0.6rem] font-bold flex-shrink-0 mt-0.5">
                                {item.pillar}
                              </span>
                              {item.description}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {narrative.key_regressions && narrative.key_regressions.length > 0 && (
                      <div className="p-4 rounded-xl bg-[#FEF2F2] border border-[#FECACA]">
                        <p className="text-xs font-bold text-[#991B1B] mb-2 uppercase tracking-wide">
                          ↓ Points de régression
                        </p>
                        <div className="space-y-1.5">
                          {narrative.key_regressions.map((item, i) => (
                            <div key={i} className="flex items-start gap-2 text-sm text-[#374151]">
                              <span className="px-1.5 py-0.5 rounded bg-[#FEE2E2] text-[#991B1B] text-[0.6rem] font-bold flex-shrink-0 mt-0.5">
                                {item.pillar}
                              </span>
                              {item.description}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : null}

                {/* Actions prioritaires */}
                {narrative?.priority_actions && narrative.priority_actions.length > 0 && (
                  <div>
                    <p className="text-xs font-bold text-[#6B7280] uppercase tracking-wide mb-2">
                      Actions prioritaires
                    </p>
                    <div className="space-y-2">
                      {[...narrative.priority_actions]
                        .sort((a, b) => a.priority - b.priority)
                        .slice(0, 3)
                        .map((act, i) => {
                          const prioColors: Record<number, string> = {
                            1: "bg-[#FEE2E2] text-[#991B1B]",
                            2: "bg-[#FEF3C7] text-[#92400E]",
                            3: "bg-[#DBEAFE] text-[#1E40AF]",
                          };
                          const cls = prioColors[act.priority] ?? "bg-[#F3F4F6] text-[#374151]";
                          return (
                            <div key={i} className="flex items-start gap-3 p-3 rounded-lg border border-[#E5E7EB] bg-white">
                              <span className={`text-[0.65rem] font-bold px-1.5 py-0.5 rounded flex-shrink-0 ${cls}`}>
                                P{act.priority}
                              </span>
                              <div>
                                <span className="text-xs font-semibold text-[#1A3D22] mr-1.5">[{act.pillar}]</span>
                                <span className="text-sm text-[#374151]">{act.action}</span>
                                {act.rationale && (
                                  <p className="text-xs text-[#9CA3AF] mt-0.5">{act.rationale}</p>
                                )}
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Si pas encore calculé / chargé */}
            {!fullAnalysis && !loading && isPaid && (
              <p className="text-center text-xs text-[#9CA3AF] mt-2 pb-1">
                Cliquez sur &quot;Calculer le delta&quot; pour lancer l&apos;analyse comparative IA.
              </p>
            )}
          </>
        )}

        {/* Notification pour les entreprises sans données success */}
        {selected && !isSingleOnly && !hasMultiple && successAnalyses.length === 0 && (
          <div className="flex items-start gap-3 p-4 rounded-xl bg-[#F9FAFB] border border-[#E5E7EB]">
            <Info className="w-5 h-5 text-[#9CA3AF] flex-shrink-0 mt-0.5" />
            <p className="text-sm text-[#6B7280]">
              Aucune analyse terminée pour <span className="font-medium">{selected}</span>.
            </p>
          </div>
        )}
      </div>

      {/* Rappel entreprises analyse unique */}
      {companiesSingle.length > 0 && companiesMultiple.length > 0 && (
        <p className="text-xs text-[#9CA3AF] mt-2 px-1">
          <span className="font-medium text-[#D97706]">⚠</span>{" "}
          {companiesSingle.join(", ")} — analyse unique, un second rapport est nécessaire pour le Delta.
        </p>
      )}
    </section>
  );
}
