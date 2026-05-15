"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { Upload, FileText, X, CheckCircle, AlertCircle, Lock, Zap, Globe } from "lucide-react";
import { API_BASE } from "@/lib/api";

const ACCEPTED = [".pdf", ".docx", ".xlsx"];
const MAX_MB = 20;
const CURRENT_YEAR = new Date().getFullYear();

type Status = "idle" | "uploading" | "success" | "error";

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
  const [errorMsg, setErrorMsg] = useState("");
  const [drag, setDrag] = useState(false);

  function handleFile(f: File) {
    setErrorMsg("");
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setErrorMsg("Format non supporté. Acceptés : PDF, DOCX, XLSX.");
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
    status !== "success";

  async function handleSubmit() {
    if (!file) return;
    if (!companyName.trim()) {
      setErrorMsg("Indiquez le nom de l'entreprise concernée par le rapport.");
      return;
    }
    setErrorMsg("");
    setStatus("uploading");
    setProgress(10);

    const interval = setInterval(() => {
      setProgress((p) => Math.min(p + 10, 85));
    }, 700);

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
      setProgress(100);

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? data.error ?? "Le serveur n'a pas pu traiter le fichier.");
      }

      const data = await res.json();
      setStatus("success");
      setTimeout(() => router.push(`/resultats?id=${data.analysis_id}`), 1400);
    } catch (e) {
      clearInterval(interval);
      setStatus("error");
      setErrorMsg(e instanceof Error ? e.message : "Une erreur inattendue est survenue.");
    }
  }

  return (
    <div className="w-full max-w-3xl">
      <div className="mb-8">
        <h1
          className="text-4xl text-[#1A3D22] mb-2"
          style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
        >
          Analyser un rapport
        </h1>
        <p className="text-[#6B7280]">
          PDF, DOCX ou XLSX · Taille max {MAX_MB} Mo · Résultat en quelques minutes
        </p>
      </div>

      {/* Informations sur le rapport */}
      <div className="card mb-6">
        <h3 className="font-semibold text-[#1A3D22] mb-4">Informations sur le rapport</h3>
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="sm:col-span-2">
            <label className="label" htmlFor="company_name">
              Entreprise concernée <span className="text-[#B53030]">*</span>
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
              Année du rapport <span className="text-[#B53030]">*</span>
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
              Secteur d&apos;activité <span className="text-[#6B7280] font-normal">(facultatif)</span>
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

      {/* Zone de dépôt */}
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          const f = e.dataTransfer.files[0];
          if (f) handleFile(f);
        }}
        className={`relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
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
              Glissez-déposez votre rapport ici
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
          </div>
        )}
      </div>

      {/* Erreur */}
      {errorMsg && (
        <div className="mt-4 flex items-center gap-2 text-[#B53030] bg-[#FEE2E2] rounded-lg px-4 py-3 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {errorMsg}
        </div>
      )}

      {/* Progression */}
      {status === "uploading" && (
        <div className="mt-6">
          <div className="flex justify-between text-sm text-[#6B7280] mb-2">
            <span>Envoi et lancement de l&apos;analyse…</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full h-2 bg-[#E5E0D8] rounded-full overflow-hidden">
            <div
              className="h-full bg-[#1A3D22] rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Succès */}
      {status === "success" && (
        <div className="mt-4 flex items-center gap-2 text-[#1A3D22] bg-[#D4F0D8] rounded-lg px-4 py-3 text-sm font-medium">
          <CheckCircle className="w-4 h-4" />
          Analyse lancée. Redirection vers le suivi des résultats…
        </div>
      )}

      {/* Action */}
      {status !== "success" && (
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="btn-primary w-full mt-6 py-3 text-base justify-center disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-none"
        >
          <Upload className="w-5 h-5" />
          {status === "uploading" ? "Analyse en cours…" : "Lancer l'analyse"}
        </button>
      )}

      {/* Réassurance */}
      <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { icon: Lock, label: "Données privées", sub: "Fichiers supprimés après extraction" },
          { icon: Zap, label: "Analyse rapide", sub: "Résultat en quelques minutes" },
          { icon: Globe, label: "Conforme RGPD", sub: "Hébergement en Europe" },
        ].map(({ icon: Icon, label, sub }) => (
          <div key={label} className="text-center">
            <div className="w-10 h-10 bg-[#D4F0D8] rounded-xl flex items-center justify-center mx-auto mb-2">
              <Icon className="w-5 h-5 text-[#1A3D22]" />
            </div>
            <p className="text-xs font-medium text-[#1C1C1C]">{label}</p>
            <p className="text-xs text-[#6B7280]">{sub}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
