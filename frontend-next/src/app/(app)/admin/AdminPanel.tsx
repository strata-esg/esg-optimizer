"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { API_BASE } from "@/lib/api";
import { Users, BarChart2, CheckCircle, Clock, RefreshCw, AlertTriangle, Shield } from "lucide-react";
import type { AdminUser, AdminAnalysis } from "./page";

interface Props {
  dash: { total_users: number; total_analyses: number; success_analyses: number; pending_analyses: number };
  users: AdminUser[];
  analyses: AdminAnalysis[];
}

const PLAN_COLORS: Record<string, string> = {
  discovery: "bg-gray-100 text-gray-600",
  free: "bg-gray-100 text-gray-600",
  essential: "bg-blue-100 text-blue-700",
  pro: "bg-green-100 text-[#1A3D22]",
  enterprise: "bg-purple-100 text-purple-700",
};

export default function AdminPanel({ dash, users, analyses }: Props) {
  const { getToken } = useAuth();
  const [tab, setTab] = useState<"dash" | "users" | "analyses">("dash");
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  // Reassign analysis
  const [reassignId, setReassignId] = useState("");
  const [reassignEmail, setReassignEmail] = useState("");

  // Fix email
  const [fixOld, setFixOld] = useState("");
  const [fixNew, setFixNew] = useState("");

  // Set plan by ID
  const [planUserId, setPlanUserId] = useState("");
  const [planValue, setPlanValue] = useState("pro");

  // Set plan by email
  const [planEmail, setPlanEmail] = useState("");
  const [planEmailValue, setPlanEmailValue] = useState("pro");
  const [planEmailResetQuota, setPlanEmailResetQuota] = useState(true);

  async function apiAction(method: string, path: string, params?: Record<string, string>) {
    setLoading(true);
    setMsg("");
    try {
      const token = await getToken();
      const url = new URL(`${API_BASE}${path}`);
      if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
      const res = await fetch(url.toString(), {
        method,
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? JSON.stringify(data));
      setMsg("OK : " + JSON.stringify(data));
    } catch (e) {
      setMsg("Erreur : " + (e instanceof Error ? e.message : String(e)));
    }
    setLoading(false);
  }

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-[#1A3D22] rounded-xl flex items-center justify-center">
          <Shield className="w-5 h-5 text-[#D4F0D8]" />
        </div>
        <div>
          <h1
            className="text-3xl text-[#1A3D22]"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            Administration
          </h1>
          <p className="text-[#6B7280] text-sm">Gestion des comptes et des analyses</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-[#E5E0D8]">
        {(["dash", "users", "analyses"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize border-b-2 -mb-px transition-colors ${
              tab === t
                ? "border-[#1A3D22] text-[#1A3D22]"
                : "border-transparent text-[#6B7280] hover:text-[#1A3D22]"
            }`}
          >
            {t === "dash" ? "Vue d'ensemble" : t === "users" ? "Utilisateurs" : "Analyses"}
          </button>
        ))}
      </div>

      {/* Vue d'ensemble */}
      {tab === "dash" && (
        <div className="space-y-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Utilisateurs", value: dash.total_users, icon: Users, color: "bg-blue-50" },
              { label: "Analyses totales", value: dash.total_analyses, icon: BarChart2, color: "bg-green-50" },
              { label: "Reussies", value: dash.success_analyses, icon: CheckCircle, color: "bg-[#D4F0D8]" },
              { label: "En cours", value: dash.pending_analyses, icon: Clock, color: "bg-amber-50" },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className={`card ${color}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-[#6B7280] font-medium uppercase tracking-wide">{label}</span>
                  <Icon className="w-4 h-4 text-[#1A3D22]" />
                </div>
                <div
                  className="text-3xl text-[#1A3D22]"
                  style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
                >
                  {value}
                </div>
              </div>
            ))}
          </div>

          {/* Actions admin */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Changer plan par email */}
            <div className="card md:col-span-2">
              <h3 className="font-semibold text-[#1A3D22] mb-1">Changer plan par email</h3>
              <p className="text-xs text-[#6B7280] mb-3">Plus simple : pas besoin de l&apos;ID utilisateur.</p>
              <div className="flex flex-wrap gap-3 items-end">
                <input
                  className="input flex-1 min-w-[200px]"
                  placeholder="Email (ex: diadamflow@gmail.com)"
                  value={planEmail}
                  onChange={(e) => setPlanEmail(e.target.value)}
                />
                <select
                  className="input w-40"
                  value={planEmailValue}
                  onChange={(e) => setPlanEmailValue(e.target.value)}
                >
                  <option value="discovery">Discovery</option>
                  <option value="essential">Essential</option>
                  <option value="pro">Pro</option>
                  <option value="enterprise">Enterprise</option>
                </select>
                <label className="flex items-center gap-1.5 text-sm text-[#1A3D22] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={planEmailResetQuota}
                    onChange={(e) => setPlanEmailResetQuota(e.target.checked)}
                    className="rounded"
                  />
                  Reset quota
                </label>
                <button
                  onClick={() =>
                    apiAction("POST", `/admin/set-plan-by-email`, {
                      email: planEmail,
                      plan: planEmailValue,
                      reset_quota: planEmailResetQuota ? "true" : "false",
                    })
                  }
                  disabled={!planEmail || loading}
                  className="btn-primary justify-center"
                >
                  Appliquer
                </button>
              </div>
            </div>

            {/* Reassigner une analyse */}
            <div className="card">
              <h3 className="font-semibold text-[#1A3D22] mb-4">Reassigner une analyse</h3>
              <p className="text-xs text-[#6B7280] mb-3">
                Utile si une analyse appartient a l&apos;ancien compte Streamlit au lieu du compte Clerk.
              </p>
              <div className="space-y-3">
                <input
                  className="input"
                  placeholder="ID de l'analyse (ex: 2)"
                  value={reassignId}
                  onChange={(e) => setReassignId(e.target.value)}
                />
                <input
                  className="input"
                  placeholder="Email du compte cible"
                  value={reassignEmail}
                  onChange={(e) => setReassignEmail(e.target.value)}
                />
                <button
                  onClick={() =>
                    apiAction("POST", `/admin/reassign-analysis/${reassignId}`, {
                      target_email: reassignEmail,
                    })
                  }
                  disabled={!reassignId || !reassignEmail || loading}
                  className="btn-primary w-full justify-center"
                >
                  <RefreshCw className="w-4 h-4" />
                  Reassigner
                </button>
              </div>
            </div>

            {/* Corriger un email */}
            <div className="card">
              <h3 className="font-semibold text-[#1A3D22] mb-4">Corriger un email</h3>
              <p className="text-xs text-[#6B7280] mb-3">
                Corrige les emails de type <code className="text-xs bg-gray-100 px-1 rounded">clerk_id@clerk.local</code>.
              </p>
              <div className="space-y-3">
                <input
                  className="input"
                  placeholder="Ancien email (ex: xyz@clerk.local)"
                  value={fixOld}
                  onChange={(e) => setFixOld(e.target.value)}
                />
                <input
                  className="input"
                  placeholder="Nouvel email (ex: diadamflow@gmail.com)"
                  value={fixNew}
                  onChange={(e) => setFixNew(e.target.value)}
                />
                <button
                  onClick={() =>
                    apiAction("PATCH", `/admin/fix-email`, {
                      old_email: fixOld,
                      new_email: fixNew,
                    })
                  }
                  disabled={!fixOld || !fixNew || loading}
                  className="btn-primary w-full justify-center"
                >
                  Corriger l&apos;email
                </button>
              </div>
            </div>

            {/* Changer plan par ID */}
            <div className="card">
              <h3 className="font-semibold text-[#1A3D22] mb-4">Changer le plan (par ID)</h3>
              <div className="space-y-3">
                <input
                  className="input"
                  placeholder="ID utilisateur (nombre)"
                  value={planUserId}
                  onChange={(e) => setPlanUserId(e.target.value)}
                />
                <select
                  className="input"
                  value={planValue}
                  onChange={(e) => setPlanValue(e.target.value)}
                >
                  <option value="discovery">Discovery (gratuit)</option>
                  <option value="essential">Essential</option>
                  <option value="pro">Pro</option>
                  <option value="enterprise">Enterprise</option>
                </select>
                <button
                  onClick={() =>
                    apiAction("POST", `/admin/set-plan/${planUserId}`, { plan: planValue })
                  }
                  disabled={!planUserId || loading}
                  className="btn-primary w-full justify-center"
                >
                  Appliquer le plan
                </button>
              </div>
            </div>

            {/* Reset quota */}
            <div className="card">
              <h3 className="font-semibold text-[#1A3D22] mb-4">Remettre quota a zero</h3>
              <div className="space-y-3">
                <input
                  className="input"
                  placeholder="ID utilisateur (nombre)"
                  id="quota-user-id"
                />
                <button
                  onClick={() => {
                    const el = document.getElementById("quota-user-id") as HTMLInputElement;
                    apiAction("POST", `/admin/reset-quota-admin/${el.value}`);
                  }}
                  disabled={loading}
                  className="btn-secondary w-full justify-center"
                >
                  Remettre a zero
                </button>
              </div>
            </div>
          </div>

          {/* Message resultat */}
          {msg && (
            <div
              className={`rounded-lg px-4 py-3 text-sm flex items-start gap-2 ${
                msg.startsWith("OK")
                  ? "bg-[#D4F0D8] text-[#1A3D22]"
                  : "bg-[#FEE2E2] text-[#B53030]"
              }`}
            >
              {msg.startsWith("OK") ? (
                <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              )}
              <code className="text-xs break-all">{msg}</code>
            </div>
          )}
        </div>
      )}

      {/* Utilisateurs */}
      {tab === "users" && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#E5E0D8]">
                {["ID", "Email", "Nom", "Plan", "Analyses", "Clerk ID", "Cree le"].map((h) => (
                  <th key={h} className="text-left py-2 px-3 text-xs text-[#6B7280] font-semibold uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-[#F3F4F6] hover:bg-[#F7F2E8] transition-colors">
                  <td className="py-2.5 px-3 font-mono text-xs text-[#6B7280]">{u.id}</td>
                  <td className="py-2.5 px-3 font-medium text-[#1C1C1C]">{u.email}</td>
                  <td className="py-2.5 px-3 text-[#6B7280]">{u.full_name ?? "-"}</td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${PLAN_COLORS[u.plan] ?? "bg-gray-100"}`}>
                      {u.plan}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-center">{u.analyses_this_month}</td>
                  <td className="py-2.5 px-3 font-mono text-xs text-[#6B7280] max-w-[120px] truncate">
                    {u.clerk_id ? u.clerk_id.slice(0, 16) + "..." : <span className="text-[#D97706]">absent</span>}
                  </td>
                  <td className="py-2.5 px-3 text-xs text-[#6B7280]">
                    {new Date(u.created_at).toLocaleDateString("fr-FR")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-[#6B7280] mt-3">{users.length} utilisateurs affiches</p>
        </div>
      )}

      {/* Analyses */}
      {tab === "analyses" && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#E5E0D8]">
                {["ID", "Entreprise", "Utilisateur", "Annee", "Score", "Statut", "Date"].map((h) => (
                  <th key={h} className="text-left py-2 px-3 text-xs text-[#6B7280] font-semibold uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {analyses.map((a) => (
                <tr key={a.id} className="border-b border-[#F3F4F6] hover:bg-[#F7F2E8] transition-colors">
                  <td className="py-2.5 px-3 font-mono text-xs text-[#6B7280]">{a.id}</td>
                  <td className="py-2.5 px-3 font-medium text-[#1C1C1C]">{a.company_name}</td>
                  <td className="py-2.5 px-3 text-xs text-[#6B7280]">{a.user_email}</td>
                  <td className="py-2.5 px-3 text-center">{a.report_year ?? "-"}</td>
                  <td className="py-2.5 px-3 text-center font-semibold">
                    {a.score_global != null ? `${Math.round(a.score_global)}/100` : "-"}
                  </td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                        a.status === "success"
                          ? "bg-[#D4F0D8] text-[#1A3D22]"
                          : a.status === "failed"
                          ? "bg-[#FEE2E2] text-[#B53030]"
                          : "bg-amber-100 text-amber-700"
                      }`}
                    >
                      {a.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-xs text-[#6B7280]">
                    {new Date(a.created_at).toLocaleDateString("fr-FR")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-[#6B7280] mt-3">{analyses.length} analyses affichees</p>
        </div>
      )}
    </div>
  );
}
