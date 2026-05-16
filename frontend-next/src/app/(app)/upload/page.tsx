"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import {
  Upload,
  FileText,
  X,
  CheckCircle,
  AlertCircle,
  Lock,
  Zap,
  Globe,
  Clock,
  Leaf,
  Users,
  Building2,
} from "lucide-react";
import { API_BASE } from "@/lib/api";

const ACCEPTED = [".pdf", ".docx", ".xlsx"];
const MAX_MB = 20;
const CURRENT_YEAR = new Date().getFullYear();

type Status = "idle" | "uploading" | "polling" | "success" | "error";

const STEPS = [
  "Extraction du texte",
  "Identification des indicateurs ESG",
  "Evaluation CSRD / ESRS",
  "Calcul des scores",
];

export default function UploadPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const inputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [reportYear, setReportYear] = useState<number>(CURRENT_YEAR - 1);
  const [sector, setSector] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [progress, setProgress] = useState(0);
  const [stepIdx, setStepIdx] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");
  const [drag, setDrag] = useState(false);
  const [analysisId, setAnalysisId] = useState<number | null>(null);

  function handleFile(f: File) {
    setErrorMsg("");
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setErrorMsg("Format non supporte. Acceptes : PDF, DOCX, XLSX.");
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setErrorMsg(`Fichier trop lourd (max ${MAX_MB} Mo).`);
      return;
    }
    setFile(f);
    setStatus("idle");
  }

  const canSubmit =
    !!file &&
    companyName.trim().length > 0 &&
    reportYear >= 2000 &&
    reportYear <= 2100 &&
    status !== "uploading" &&
    status !== "polling" &&
    status !== "success";

  async function handleSubmit() {
    if (!file) return;
    if (!companyName.trim()) {
      setErrorMsg("Indiquez le nom de l'entreprise concernee par le rapport.");
      return;
    }
    setErrorMsg("");
    setStatus("uploading");
    setProgress(10);

    const interval = setInterval(() => {
      setProgress((p) => Math.min(p + 8, 40));
    }, 600);

    try {
      const token = await getToken();
      const form = new FormData();
      form.append("file", file);
      form.append("company_name", companyName.trim());
      form.append("report_year", String(reportYear));
      if (sector.trim()) form.append("sector", sector.trim());

      const res = await fetch(`${API_BASE}/analysis/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });

      clearInterval(interval);

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? data.error ?? "Le serveur n'a pas pu traiter le fichier.");
      }

      const data = await res.json();
      setAnalysisId(data.analysis_id);
      setProgress(50);
      setStatus("polling");
    } catch (e) {
      clearInterval(interval);
      setStatus("error");
      setErrorMsg(e instanceof Error ? e.message : "Une erreur inattendue est survenue.");
    }
  }

  useEffect(() => {
    if (status !== "polling" || !analysisId) return;

    let attempts = 0;
    const maxAttempts = 80;

    const poll = async () => {
      if (attempts >= maxAttempts) {
        setStatus("error");
        setErrorMsg("L'analyse prend trop de temps. Verifiez les resultats dans Historique.");
        return;
      }

      attempts++;
      setStepIdx(Math.min(Math.floor(attempts / 8), 3));
      setProgress(Math.min(50 + attempts, 95));

      try {
        const token = await getToken();
        const res = await fetch(`${API_BASE}/analysis/${analysisId}`, {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
        });
        if (!res.ok) return;
        const data = await res.json();

        if (data.status === "success") {
          setProgress(100);
          setStepIdx(4);
          setStatus("success");
          setTimeout(() => router.push(`/resultats?id=${analysisId}`), 1200);
          return;
        }
        if (data.status === "failed") {
          setStatus("error");
          setErrorMsg(data.error_message ?? "L'analyse a echoue. Verifiez le fichier et reessayez.");
          return;
        }
      } catch {
        // reseau temporairement indisponible
      }

      setTimeout(poll, 3000);
    };

    const t = setTimeout(poll, 3000);
    return () => clearTimeout(t);
  }, [status, analysisId, getToken, router]);

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1
          className="text-4xl text-[#1A3D22] mb-2"
          style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
        >
          Analyser un rapport
        </h1>
        <p className="text-[#6B7280]">
          PDF, DOCX ou XLSX · Taille max {MAX_MB} Mo · Resultat en quelques minutes
        </p>
      </div>

      <div className="grid lg:grid-cols-5 gap-8 items-start">
        <div className="lg:col-span-3 space-y-6">
          <div className="card">
            <h3 className="font-semibold text-[#1A3D22] mb-4">Informations sur le rapport</h3>
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className="label" htmlFor="company_name">
                  Entreprise concernee <span className="text-[#B53030]">*</span>
                </label>
                <input
                  id="company_name"
                  type="text"
                  className="input"
                  placeholder="Ex. Boulangerie Martin SAS"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  maxLength={255}
                />
              </div>
              <div>
                <label className="label" htmlFor="report_year">
                  Annee du rapport <span className="text-[#B53030]">*</span>
                </label>
                <input
                  id="report_year"
                  type="number"
                  className="input"
                  min={2000}
                  max={2100}
                  value={reportYear}
                  onChange={(e) => setReportYear(Number(e.target.value))}
                />
              </div>
              <div>
                <label className="label" htmlFor="sector">
                  Secteur d&apos;activite{" "}
                  <span className="text-[#6B7280] font-normal">(facultatif)</span>
                </label>
                <input
                  id="sector"
                  type="text"
                  className="input"
                  placeholder="Ex. Agroalimentaire"
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                  maxLength={255}
                />
              </div>
            </div>
          </div>

          <div
            onClick={() => status === "idle" && inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              const f = e.dataTransfer.files[0];
              if (f) handleFile(f);
            }}
            className={`relative border-2 border-dashed rounded-xl p-10 text-center transition-all ${
              status !== "idle" ? "cursor-default" : "cursor-pointer"
            } ${
              drag
                ? "border-[#1A3D22] bg-[#D4F0D8]/30"
                : file
                ? "border-[#7FC686] bg-[#D4F0D8]/10"
                : "border-[#E5E0D8] bg-white hover:border-[#1A3D22] hover:bg-[#F7F2E8]"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED.join(",")}
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />

            {!file ? (
              <>
                <div className="w-16 h-16 bg-[#D4F0D8] rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Upload className="w-8 h-8 text-[#1A3D22]" />
                </div>
                <p className="text-[#1C1C1C] font-medium mb-1">
                  Glissez-deposez votre rapport ici
                </p>
                <p className="text-sm text-[#6B7280]">
                  ou <span className="text-[#1A3D22] font-medium">cliquez pour parcourir</span>
                </p>
                <p className="text-xs text-[#6B7280] mt-3">PDF · DOCX · XLSX · Max {MAX_MB} Mo</p>
              </>
            ) : (
              <div className="flex items-center gap-4 justify-center">
                <FileText className="w-10 h-10 text-[#1A3D22] flex-shrink-0" />
                <div className="text-left">
                  <p className="font-medium text-[#1C1C1C]">{file.name}</p>
                  <p className="text-sm text-[#6B7280]">
                    {(file.size / 1024 / 1024).toFixed(2)} Mo
                  </p>
                </div>
                {status === "idle" && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                      setStatus("idle");
                    }}
                    className="ml-4 p-1.5 rounded-full hover:bg-[#FEE2E2] text-[#6B7280] hover:text-[#B53030] transition-all"
                    aria-label="Retirer le fichier"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            )}
          </div>

          {errorMsg && (
            <div className="flex items-center gap-2 text-[#B53030] bg-[#FEE2E2] rounded-lg px-4 py-3 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {errorMsg}
            </div>
          )}

          {(status === "uploading" || status === "polling") && (
            <div className="card">
              <div className="flex justify-between text-sm text-[#6B7280] mb-2">
                <span>
                  {status === "uploading" ? "Envoi du fichier..." : "Analyse en cours..."}
                </span>
                <span>{progress}%</span>
              </div>
              <div className="w-full h-2 bg-[#E5E0D8] rounded-full overflow-hidden mb-4">
                <div
                  className="h-full bg-[#1A3D22] rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>

              {status === "polling" && (
                <div className="space-y-2 mt-2">
                  {STEPS.map((step, i) => (
                    <div key={step} className="flex items-center gap-2.5 text-sm">
                      {i < stepIdx ? (
                        <CheckCircle className="w-4 h-4 text-[#1A3D22] flex-shrink-0" />
                      ) : i === stepIdx ? (
                        <div className="w-4 h-4 rounded-full border-2 border-[#1A3D22] border-t-transparent animate-spin flex-shrink-0" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border-2 border-[#E5E0D8] flex-shrink-0" />
                      )}
                      <span
                        className={i <= stepIdx ? "text-[#1A3D22] font-medium" : "text-[#9CA3AF]"}
                      >
                        {step}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {status === "success" && (
            <div className="flex items-center gap-2 text-[#1A3D22] bg-[#D4F0D8] rounded-lg px-4 py-3 text-sm font-medium">
              <CheckCircle className="w-4 h-4" />
              Analyse terminee. Redirection vers les resultats...
            </div>
          )}

          {status !== "success" && (
            <button
              onClick={handleSubmit}
              disabled={!canSubmit}
              className="btn-primary w-full py-3 text-base justify-center disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-none"
            >
              <Upload className="w-5 h-5" />
              {status === "uploading"
                ? "Envoi..."
                : status === "polling"
                ? "Analyse en cours..."
                : "Lancer l'analyse"}
            </button>
          )}
        </div>

        <div className="lg:col-span-2 space-y-5">
          <div className="card">
            <h3 className="font-semibold text-[#1A3D22] mb-4 text-sm uppercase tracking-wide">
              Pourquoi ESG Optimizer AI ?
            </h3>
            <div className="space-y-4">
              {[
                {
                  icon: Zap,
                  title: "Analyse en 3 minutes",
                  desc: "GPT-4o analyse votre rapport selon les standards ESRS et CSRD automatiquement.",
                },
                {
                  icon: Lock,
                  title: "Donnees privees",
                  desc: "Vos fichiers sont supprimes apres extraction. Aucune donnee revendue.",
                },
                {
                  icon: Globe,
                  title: "Conforme RGPD",
                  desc: "Hebergement en Europe. Infrastructure securisee et auditee.",
                },
              ].map(({ icon: Icon, title, desc }) => (
                <div key={title} className="flex gap-3">
                  <div className="w-9 h-9 bg-[#D4F0D8] rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Icon className="w-4 h-4 text-[#1A3D22]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-[#1A3D22]">{title}</p>
                    <p className="text-xs text-[#6B7280] mt-0.5 leading-relaxed">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 className="font-semibold text-[#1A3D22] mb-4 text-sm uppercase tracking-wide">
              Ce que vous obtenez
            </h3>
            <ul className="space-y-2.5">
              {[
                { icon: Leaf, text: "Score E/S/G et score global /100" },
                { icon: Building2, text: "Couverture CSRD et indicateurs manquants" },
                { icon: Users, text: "Forces, lacunes et recommandations prioritaires" },
                { icon: FileText, text: "Rapport PDF pret a partager" },
              ].map(({ icon: Icon, text }) => (
                <li key={text} className="flex items-start gap-2.5 text-sm text-[#1C1C1C]">
                  <Icon className="w-4 h-4 text-[#7FC686] flex-shrink-0 mt-0.5" />
                  {text}
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h3 className="font-semibold text-[#1A3D22] mb-4 text-sm uppercase tracking-wide">
              Comment ca marche
            </h3>
            <ol className="space-y-3">
              {[
                "Uploadez votre rapport (PDF, Word ou Excel)",
                "L'IA extrait et analyse le contenu",
                "Scores, conformite CSRD et recommandations generes",
                "Telechargez votre rapport PDF professionnel",
              ].map((step, i) => (
                <li key={step} className="flex gap-3 text-sm">
                  <span className="w-5 h-5 rounded-full bg-[#1A3D22] text-[#D4F0D8] text-xs flex items-center justify-center flex-shrink-0 font-bold mt-0.5">
                    {i + 1}
                  </span>
                  <span className="text-[#1C1C1C] leading-relaxed">{step}</span>
                </li>
              ))}
            </ol>
          </div>

          {status === "polling" && (
            <div
              className="rounded-xl px-4 py-3 text-sm flex items-center gap-2"
              style={{ background: "#EFF6FF", color: "#1E40AF" }}
            >
              <Clock className="w-4 h-4 flex-shrink-0" />
              Analyse en cours. Ne fermez pas la page.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
