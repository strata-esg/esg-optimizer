"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { API_BASE } from "@/lib/api";

const STORAGE_KEY = "esg_onboarding_done";

const ROLES = [
  { id: "dirigeant", label: "Dirigeant / CEO", icon: "🏢" },
  { id: "rse", label: "Responsable RSE", icon: "🌿" },
  { id: "consultant", label: "Consultant ESG", icon: "📊" },
  { id: "finance", label: "DAF / Finance", icon: "💼" },
  { id: "investisseur", label: "Investisseur", icon: "📈" },
  { id: "autre", label: "Autre", icon: "✦" },
];

const SECTORS = [
  "Industrie & Manufacture",
  "Services financiers",
  "Immobilier & Construction",
  "Énergie & Utilities",
  "Distribution & Commerce",
  "Transport & Logistique",
  "Agroalimentaire",
  "Santé & Pharmaceutique",
  "Technologie & Numérique",
  "Autre",
];

const SIZES = [
  { id: "tpe", label: "TPE", sub: "< 10 salariés" },
  { id: "pme", label: "PME", sub: "10 – 250 salariés" },
  { id: "eti", label: "ETI", sub: "250 – 5 000 salariés" },
  { id: "ge", label: "Grande entreprise", sub: "> 5 000 salariés" },
];

const OBJECTIVES = [
  { id: "csrd", label: "Conformité CSRD", desc: "Préparer mon rapport de durabilité obligatoire", icon: "📋" },
  { id: "score", label: "Améliorer mon score", desc: "Identifier les axes de progrès ESG", icon: "🎯" },
  { id: "audit", label: "Préparer un audit", desc: "Me préparer à une certification ou vérification", icon: "✅" },
  { id: "investisseurs", label: "Convaincre des investisseurs", desc: "Valoriser ma démarche auprès des financeurs", icon: "🤝" },
  { id: "benchmark", label: "Me comparer", desc: "Benchmarker mes performances sectorielles", icon: "📊" },
];

const MATURITIES = [
  { id: "debutant", label: "Débutant", desc: "Je commence tout juste à explorer l'ESG", color: "#FEF3C7", border: "#FCD34D", text: "#92400E" },
  { id: "en-dev", label: "En développement", desc: "J'ai quelques pratiques en place", color: "#DBEAFE", border: "#93C5FD", text: "#1e40af" },
  { id: "avance", label: "Avancé", desc: "Stratégie ESG formalisée et suivie", color: "#D4F0D8", border: "#7FC686", text: "#1A3D22" },
  { id: "expert", label: "Expert", desc: "Reporting intégré, certifications obtenues", color: "#EDE9FE", border: "#A78BFA", text: "#5B21B6" },
];

interface OnboardingData {
  role: string;
  companyName: string;
  sector: string;
  size: string;
  objective: string;
  maturity: string;
}

export default function OnboardingModal() {
  const { getToken } = useAuth();
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [data, setData] = useState<OnboardingData>({
    role: "",
    companyName: "",
    sector: "",
    size: "",
    objective: "",
    maturity: "",
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (localStorage.getItem(STORAGE_KEY)) return;

    // Vérifier si l'utilisateur a déjà des analyses (utilisateur existant)
    const checkNewUser = async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const res = await fetch(`${API_BASE}/history/stats`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const stats = await res.json();
        // N'afficher le questionnaire que si aucune analyse (vrai nouvel utilisateur)
        if ((stats.total_analyses ?? 0) === 0) {
          setVisible(true);
        } else {
          // Utilisateur existant : marquer comme fait pour ne plus afficher
          localStorage.setItem(STORAGE_KEY, "1");
        }
      } catch {
        // En cas d'erreur réseau, ne pas afficher
      }
    };
    checkNewUser();
  }, [getToken]);

  const dismiss = () => {
    localStorage.setItem(STORAGE_KEY, "1");
    setVisible(false);
  };

  const next = () => setStep((s) => Math.min(s + 1, 4));
  const prev = () => setStep((s) => Math.max(s - 1, 1));

  const canNext = () => {
    if (step === 1) return data.role !== "";
    if (step === 2) return data.companyName.trim() !== "" && data.sector !== "" && data.size !== "";
    if (step === 3) return data.objective !== "";
    return true;
  };

  const finish = async () => {
    setSaving(true);
    try {
      const token = await getToken();
      if (token && (data.companyName || data.role)) {
        await fetch(
          `${API_BASE}/auth/profile?full_name=${encodeURIComponent(data.role)}&company_name=${encodeURIComponent(data.companyName)}`,
          { method: "PATCH", headers: { Authorization: `Bearer ${token}` } }
        );
      }
    } catch {
      // Silent fail — onboarding data is optional
    } finally {
      setSaving(false);
      dismiss();
    }
  };

  if (!visible) return null;

  const totalSteps = 4;
  const progress = ((step - 1) / (totalSteps - 1)) * 100;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: "rgba(26, 61, 34, 0.55)", backdropFilter: "blur(4px)" }}
    >
      <div
        className="relative w-full max-w-xl mx-4 rounded-2xl shadow-2xl overflow-hidden"
        style={{ backgroundColor: "#F7F2E8", border: "1px solid #E5E0D8" }}
      >
        {/* Header */}
        <div
          className="px-8 pt-8 pb-6"
          style={{ background: "linear-gradient(135deg, #1A3D22 0%, #2D5A35 100%)" }}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium tracking-widest uppercase" style={{ color: "#7FC686" }}>
              Étape {step} / {totalSteps}
            </span>
            <button
              onClick={dismiss}
              className="text-xs opacity-50 hover:opacity-80 transition-opacity"
              style={{ color: "#D4F0D8" }}
            >
              Passer
            </button>
          </div>
          {/* Progress bar */}
          <div className="h-1 rounded-full mb-4" style={{ backgroundColor: "rgba(255,255,255,0.15)" }}>
            <div
              className="h-1 rounded-full transition-all duration-500"
              style={{ width: `${progress}%`, backgroundColor: "#7FC686" }}
            />
          </div>
          <h2
            className="text-2xl text-white"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            {step === 1 && "Bienvenue sur ESG Optimizer"}
            {step === 2 && "Votre entreprise"}
            {step === 3 && "Votre objectif principal"}
            {step === 4 && "Votre maturité ESG"}
          </h2>
          <p className="text-sm mt-1" style={{ color: "#A8D5B0" }}>
            {step === 1 && "Quelques questions pour personnaliser votre expérience."}
            {step === 2 && "Ces informations nous aident à contextualiser vos analyses."}
            {step === 3 && "Nous adapterons les recommandations à votre priorité."}
            {step === 4 && "Dernière étape — évaluez honnêtement votre niveau actuel."}
          </p>
        </div>

        {/* Body */}
        <div className="px-8 py-6">
          {/* Step 1 — Rôle */}
          {step === 1 && (
            <div className="grid grid-cols-3 gap-3">
              {ROLES.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setData((d) => ({ ...d, role: r.id }))}
                  className="flex flex-col items-center gap-2 px-3 py-4 rounded-xl border-2 transition-all text-center"
                  style={{
                    borderColor: data.role === r.id ? "#1A3D22" : "#E5E0D8",
                    backgroundColor: data.role === r.id ? "#D4F0D8" : "white",
                    color: data.role === r.id ? "#1A3D22" : "#6B7280",
                  }}
                >
                  <span className="text-2xl">{r.icon}</span>
                  <span className="text-xs font-medium leading-tight">{r.label}</span>
                </button>
              ))}
            </div>
          )}

          {/* Step 2 — Entreprise */}
          {step === 2 && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#1A3D22] mb-1.5 uppercase tracking-wide">
                  Nom de l'entreprise
                </label>
                <input
                  type="text"
                  value={data.companyName}
                  onChange={(e) => setData((d) => ({ ...d, companyName: e.target.value }))}
                  placeholder="Ex: Acme Industries SAS"
                  className="w-full px-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2"
                  style={{
                    borderColor: "#E5E0D8",
                    backgroundColor: "white",
                    color: "#1C1C1C",
                  }}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#1A3D22] mb-1.5 uppercase tracking-wide">
                  Secteur d'activité
                </label>
                <select
                  value={data.sector}
                  onChange={(e) => setData((d) => ({ ...d, sector: e.target.value }))}
                  className="w-full px-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2"
                  style={{ borderColor: "#E5E0D8", backgroundColor: "white", color: "#1C1C1C" }}
                >
                  <option value="">Sélectionnez votre secteur</option>
                  {SECTORS.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-[#1A3D22] mb-1.5 uppercase tracking-wide">
                  Taille de l'entreprise
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {SIZES.map((sz) => (
                    <button
                      key={sz.id}
                      onClick={() => setData((d) => ({ ...d, size: sz.id }))}
                      className="flex flex-col px-4 py-3 rounded-xl border-2 text-left transition-all"
                      style={{
                        borderColor: data.size === sz.id ? "#1A3D22" : "#E5E0D8",
                        backgroundColor: data.size === sz.id ? "#D4F0D8" : "white",
                      }}
                    >
                      <span className="text-sm font-semibold" style={{ color: "#1A3D22" }}>{sz.label}</span>
                      <span className="text-xs" style={{ color: "#6B7280" }}>{sz.sub}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 3 — Objectif */}
          {step === 3 && (
            <div className="space-y-2">
              {OBJECTIVES.map((obj) => (
                <button
                  key={obj.id}
                  onClick={() => setData((d) => ({ ...d, objective: obj.id }))}
                  className="w-full flex items-center gap-4 px-4 py-3 rounded-xl border-2 text-left transition-all"
                  style={{
                    borderColor: data.objective === obj.id ? "#1A3D22" : "#E5E0D8",
                    backgroundColor: data.objective === obj.id ? "#D4F0D8" : "white",
                  }}
                >
                  <span className="text-xl flex-shrink-0">{obj.icon}</span>
                  <div>
                    <p className="text-sm font-semibold" style={{ color: "#1A3D22" }}>{obj.label}</p>
                    <p className="text-xs" style={{ color: "#6B7280" }}>{obj.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Step 4 — Maturité */}
          {step === 4 && (
            <div className="space-y-3">
              {MATURITIES.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setData((d) => ({ ...d, maturity: m.id }))}
                  className="w-full flex items-center justify-between px-5 py-4 rounded-xl border-2 text-left transition-all"
                  style={{
                    borderColor: data.maturity === m.id ? m.border : "#E5E0D8",
                    backgroundColor: data.maturity === m.id ? m.color : "white",
                  }}
                >
                  <div>
                    <p className="text-sm font-bold" style={{ color: data.maturity === m.id ? m.text : "#1A3D22" }}>
                      {m.label}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: "#6B7280" }}>{m.desc}</p>
                  </div>
                  {data.maturity === m.id && (
                    <span className="text-lg flex-shrink-0" style={{ color: m.text }}>✓</span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          className="px-8 py-5 flex items-center justify-between"
          style={{ borderTop: "1px solid #E5E0D8" }}
        >
          {step > 1 ? (
            <button
              onClick={prev}
              className="text-sm font-medium transition-colors"
              style={{ color: "#6B7280" }}
            >
              ← Retour
            </button>
          ) : (
            <div />
          )}

          {step < totalSteps ? (
            <button
              onClick={next}
              disabled={!canNext()}
              className="px-6 py-2.5 rounded-lg text-sm font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              style={{
                backgroundColor: canNext() ? "#1A3D22" : "#9CA3AF",
                color: "white",
              }}
            >
              Continuer →
            </button>
          ) : (
            <button
              onClick={finish}
              disabled={saving}
              className="px-6 py-2.5 rounded-lg text-sm font-semibold transition-all"
              style={{ backgroundColor: "#1A3D22", color: "white" }}
            >
              {saving ? "Enregistrement..." : "Commencer mon analyse ✦"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
