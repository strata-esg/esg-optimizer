"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import Link from "next/link";
import {
  Upload,
  CheckCircle,
  AlertTriangle,
  Clock,
  ArrowRight,
  BarChart2,
  Zap,
  RefreshCw,
  FileDown,
} from "lucide-react";
import { Logo } from "@/components/Logo";
import QuickCheckPdfPreview from "./QuickCheckPdfPreview";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

interface QuickResult {
  token: string;
  status: "pending" | "processing" | "success" | "failed";
  score_global?: number | null;
  csrd_ready?: boolean | null;
  teaser_strengths?: string[];
  teaser_weaknesses?: string[];
  error_message?: string | null;
}

function getCsrdStage(coveragePct: number | null | undefined, csrdReady: boolean | null | undefined) {
  const pct = coveragePct ?? (csrdReady ? 87 : 28);
  if (pct >= 85) return { label: "CSRD Ready", color: "#1A3D22", bg: "#D4F0D8" };
  if (pct >= 70) return { label: "Avancé", color: "#15803D", bg: "#DCFCE7" };
  if (pct >= 50) return { label: "En développement", color: "#92400E", bg: "#FEF3C7" };
  if (pct >= 30) return { label: "Initié", color: "#9A3412", bg: "#FED7AA" };
  return { label: "Non conforme", color: "#991B1B", bg: "#FEE2E2" };
}

function scoreColor(score: number) {
  if (score >= 70) return "#1A3D22";
  if (score >= 40) return "#D97706";
  return "#B53030";
}

export default function QuickCheckPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<QuickResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showPdf, setShowPdf] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  }, []);

  useEffect(() => () => stopPolling(), [stopPolling]);

  const pollResult = useCallback((token: string) => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/public/quick-check/${token}`);
        if (!res.ok) { stopPolling(); return; }
        const data: QuickResult = await res.json();
        setResult(data);
        if (data.status === "success" || data.status === "failed") stopPolling();
      } catch { stopPolling(); }
    }, 3000);
  }, [stopPolling]);

  const handleFile = useCallback((f: File) => {
    const allowed = ["pdf", "docx", "xlsx", "doc", "xls"];
    const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
    if (!allowed.includes(ext)) { setError(`Format non supporté (.${ext}). Acceptés : PDF, DOCX, XLSX.`); return; }
    if (f.size > 20 * 1024 * 1024) { setError("Fichier trop volumineux (max 20 Mo)."); return; }
    setError(null);
    setFile(f);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const handleSubmit = useCallback(async () => {
    if (!file) return;
    setUploading(true); setError(null); setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/public/quick-check`, { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Erreur serveur" }));
        throw new Error(err.detail ?? "Erreur lors de l'envoi");
      }
      const data = await res.json();
      setResult({ token: data.token, status: "processing" });
      pollResult(data.token);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Erreur inattendue");
    } finally { setUploading(false); }
  }, [file, pollResult]);

  const reset = () => { setFile(null); setResult(null); setError(null); setShowPdf(false); stopPolling(); };

  const isProcessing = result?.status === "pending" || result?.status === "processing";
  const isDone = result?.status === "success";

  return (
    <div className="min-h-screen bg-[#F7F2E8]">
      <header className="border-b border-[#E5E0D8] bg-[#F7F2E8]">
        <div className="max-w-3xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" aria-label="ESG Optimizer - Accueil">
            <Logo variant="light" size="md" showTagline={false} />
          </Link>
          <Link href="/" className="text-sm text-[#6B7280] hover:text-[#1A3D22]">Accueil</Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#D4F0D8] text-[#1A3D22] text-sm font-medium mb-4">
            <Zap className="w-3.5 h-3.5" />
            Sans inscription requise
          </div>
          <h1 className="text-4xl text-[#1A3D22] mb-3" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
            Quick Check ESG
          </h1>
          <p className="text-[#6B7280] max-w-xl mx-auto leading-relaxed">
            Obtenez un diagnostic rapide de votre rapport de durabilité en quelques minutes.
            Aucun compte requis. Pour l'analyse complète avec rapport PDF et ESRS détaillés,{" "}
            <Link href="/sign-up" className="text-[#1A3D22] font-medium hover:underline">créez un compte gratuit</Link>.
          </p>
        </div>

        {!result ? (
          <div className="bg-white rounded-2xl border border-[#E5E0D8] shadow-sm p-8">
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
              className="border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all"
              style={{ borderColor: dragOver ? "#1A3D22" : file ? "#7FC686" : "#E5E0D8", background: dragOver ? "#F7FFF8" : file ? "#F0FDF4" : "#FAFAF9" }}
            >
              <input ref={fileRef} type="file" className="hidden" accept=".pdf,.docx,.doc,.xlsx,.xls" onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }} />
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4" style={{ background: file ? "#D4F0D8" : "#F3F4F6" }}>
                {file ? <CheckCircle className="w-7 h-7 text-[#1A3D22]" /> : <Upload className="w-7 h-7 text-[#9CA3AF]" />}
              </div>
              {file ? (
                <>
                  <p className="font-semibold text-[#1A3D22] mb-1">{file.name}</p>
                  <p className="text-sm text-[#6B7280]">{(file.size / 1024 / 1024).toFixed(1)} Mo · Cliquez pour changer</p>
                </>
              ) : (
                <>
                  <p className="font-semibold text-[#1C1C1C] mb-1">Glissez votre rapport ici</p>
                  <p className="text-sm text-[#6B7280]">PDF, DOCX ou XLSX · Max 20 Mo</p>
                </>
              )}
            </div>

            {error && (
              <div className="mt-4 flex items-center gap-2 bg-[#FEE2E2] text-[#991B1B] rounded-lg px-4 py-3 text-sm">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={!file || uploading}
              className="mt-6 w-full py-3 rounded-xl font-bold text-base transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ background: "#1A3D22", color: "#D4F0D8" }}
            >
              {uploading ? <><RefreshCw className="w-5 h-5 animate-spin" />Envoi en cours...</> : <><BarChart2 className="w-5 h-5" />Lancer le diagnostic</>}
            </button>

            <div className="mt-6 grid grid-cols-3 gap-4 text-center">
              {[
                { val: "3 min", label: "Durée d'analyse" },
                { val: "10", label: "ESRS analysés" },
                { val: "Gratuit", label: "Sans inscription" },
              ].map(({ val, label }) => (
                <div key={label} className="bg-[#F7F2E8] rounded-xl py-3 px-2">
                  <p className="font-bold text-[#1A3D22] text-lg">{val}</p>
                  <p className="text-xs text-[#6B7280] mt-0.5">{label}</p>
                </div>
              ))}
            </div>
          </div>
        ) : isProcessing ? (
          <div className="bg-white rounded-2xl border border-[#E5E0D8] shadow-sm p-12 text-center">
            <div className="w-16 h-16 bg-[#D4F0D8] rounded-2xl flex items-center justify-center mx-auto mb-5">
              <Clock className="w-8 h-8 text-[#1A3D22] animate-pulse" />
            </div>
            <h2 className="text-xl font-semibold text-[#1A3D22] mb-2" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
              Analyse en cours...
            </h2>
            <p className="text-[#6B7280] text-sm max-w-sm mx-auto">
              Notre moteur IA analyse votre rapport. Résultat disponible en 2 à 5 minutes selon la taille du document.
            </p>
            <div className="mt-6 w-full bg-[#E5E0D8] rounded-full h-1.5 overflow-hidden">
              <div className="h-full rounded-full bg-[#1A3D22] animate-pulse" style={{ width: "60%" }} />
            </div>
          </div>
        ) : result?.status === "failed" ? (
          <div className="bg-white rounded-2xl border border-[#E5E0D8] shadow-sm p-10 text-center">
            <AlertTriangle className="w-12 h-12 text-[#B53030] mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-[#1C1C1C] mb-2">L'analyse a échoué</h2>
            <p className="text-sm text-[#6B7280] mb-6">{result.error_message ?? "Le document n'a pas pu être traité. Vérifiez qu'il contient du texte exploitable."}</p>
            <button onClick={reset} className="btn-secondary">Réessayer avec un autre fichier</button>
          </div>
        ) : isDone ? (
          <div className="space-y-5">
            {/* Bouton aperçu PDF */}
            <div className="flex justify-end">
              <button
                onClick={() => setShowPdf(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-xl border border-[#E5E0D8] bg-white text-[#1A3D22] font-semibold text-sm hover:bg-[#F7F2E8] hover:border-[#1A3D22] transition-all shadow-sm"
              >
                <FileDown className="w-4 h-4" />
                Aperçu PDF — 3 pages
              </button>
            </div>

            {/* Score card */}
            <div className="bg-white rounded-2xl border border-[#E5E0D8] shadow-sm p-8">
              <div className="flex flex-col sm:flex-row items-center gap-6">
                <div
                  className="flex-shrink-0 w-32 h-32 rounded-2xl flex flex-col items-center justify-center border-2"
                  style={{ borderColor: scoreColor(result.score_global ?? 0), background: "#F9FAFB" }}
                >
                  <span className="text-4xl font-bold" style={{ color: scoreColor(result.score_global ?? 0), fontFamily: "DM Serif Display, Georgia, serif" }}>
                    {Math.round(result.score_global ?? 0)}
                  </span>
                  <span className="text-xs text-[#6B7280] mt-1">/100</span>
                </div>
                <div className="flex-1 text-center sm:text-left">
                  <h2 className="text-2xl text-[#1A3D22] mb-2" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
                    Diagnostic terminé
                  </h2>
                  {(() => {
                    const stage = getCsrdStage(null, result.csrd_ready);
                    return (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-bold" style={{ background: stage.bg, color: stage.color }}>
                        {result.csrd_ready ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                        {stage.label}
                      </span>
                    );
                  })()}
                  <p className="text-sm text-[#6B7280] mt-3">
                    Il s'agit d'un aperçu limité.{" "}
                    <Link href="/sign-up" className="text-[#1A3D22] font-medium hover:underline">
                      Créez un compte gratuit
                    </Link>{" "}
                    pour obtenir le rapport complet avec scores E/S/G détaillés, couverture ESRS, recommandations et PDF.
                  </p>
                </div>
              </div>
            </div>

            {/* Points forts & axes */}
            <div className="grid sm:grid-cols-2 gap-5">
              {(result.teaser_strengths?.length ?? 0) > 0 && (
                <div className="bg-white rounded-2xl border border-[#E5E0D8] shadow-sm p-6">
                  <h3 className="font-semibold text-[#1A3D22] flex items-center gap-2 mb-4">
                    <CheckCircle className="w-5 h-5 text-[#7FC686]" />
                    Points forts
                  </h3>
                  <ul className="space-y-2">
                    {result.teaser_strengths!.map((s, i) => (
                      <li key={i} className="text-sm text-[#1C1C1C] flex items-start gap-2">
                        <span className="text-[#7FC686] font-bold mt-0.5">·</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {(result.teaser_weaknesses?.length ?? 0) > 0 && (
                <div className="bg-white rounded-2xl border border-[#E5E0D8] shadow-sm p-6">
                  <h3 className="font-semibold text-[#1A3D22] flex items-center gap-2 mb-4">
                    <AlertTriangle className="w-5 h-5 text-[#D97706]" />
                    Axes d'amélioration
                  </h3>
                  <ul className="space-y-2">
                    {result.teaser_weaknesses!.map((w, i) => (
                      <li key={i} className="text-sm text-[#1C1C1C] flex items-start gap-2">
                        <span className="text-[#D97706] font-bold mt-0.5">·</span>
                        {w}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* CTA */}
            <div
              className="rounded-2xl p-7 text-center border-0"
              style={{ background: "linear-gradient(135deg, #1A3D22 0%, #2A5C34 100%)" }}
            >
              <h3 className="text-xl text-white mb-2" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
                Obtenez l'analyse complète
              </h3>
              <p className="text-white/70 text-sm mb-5 max-w-md mx-auto">
                Rapport PDF 8+ pages, scores E/S/G détaillés, couverture ESRS complète, recommandations priorisées et badge LinkedIn.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Link
                  href="/sign-up"
                  className="flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl font-bold text-[#1A3D22] transition-all hover:bg-[#D4F0D8]"
                  style={{ background: "#7FC686" }}
                >
                  Créer un compte gratuit
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <button
                  onClick={reset}
                  className="flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl font-semibold text-white/80 hover:text-white border border-white/20 hover:bg-white/10 transition-all text-sm"
                >
                  Analyser un autre rapport
                </button>
              </div>
            </div>
          </div>
        ) : null}

        {/* Limites */}
        <div className="mt-8 bg-[#FEF3C7] border border-[#FCD34D] rounded-xl px-5 py-4 text-sm text-[#92400E]">
          <strong>Mode Quick Check :</strong> diagnostic limité à 3 analyses / jour par IP. Scores E/S/G, recommandations détaillées et rapport PDF uniquement disponibles avec un compte.
        </div>
      </main>

      {/* PDF Preview */}
      {showPdf && result?.status === "success" && (
        <QuickCheckPdfPreview
          filename={file?.name ?? "rapport.pdf"}
          scoreGlobal={result.score_global ?? 0}
          csrdReady={result.csrd_ready ?? null}
          strengths={result.teaser_strengths ?? []}
          weaknesses={result.teaser_weaknesses ?? []}
          onClose={() => setShowPdf(false)}
        />
      )}
    </div>
  );
}
