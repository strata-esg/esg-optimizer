"use client";

import { CheckCircle, ExternalLink } from "lucide-react";

const PLANS = [
  {
    name: "Découverte",
    price: "Gratuit",
    sub: "",
    features: [
      "1 analyse incluse",
      "Score ESG global uniquement",
      "Rapport PDF 3 pages",
      "Watermark sur le PDF",
      "Support communauté",
    ],
    cta: "Plan actuel",
    href: "/dashboard",
    highlighted: false,
    current: true,
    badge: null,
    color: { bg: "bg-gray-50", border: "border-[#E5E0D8]", text: "text-[#374151]", price: "text-[#1A3D22]" },
  },
  {
    name: "Essentiel",
    price: "39€",
    sub: "par analyse · paiement unique",
    features: [
      "Rapport PDF 8+ pages complet",
      "Sans watermark",
      "Scores E / S / G / Global détaillés",
      "10 ESRS couverts (E1->G1)",
      "Delta Report N vs N-1",
      "Conservation historique 12 mois",
      "Support email",
    ],
    cta: "Payer 39€",
    href: "mailto:contact@esg-optimizer.fr?subject=Plan Essentiel",
    highlighted: false,
    current: false,
    badge: null,
    color: { bg: "bg-[#EFF6FF]", border: "border-[#3b82f6]", text: "text-[#1e40af]", price: "text-[#1e40af]" },
  },
  {
    name: "Pro",
    price: "129€",
    sub: "/ mois · ou 990€/an",
    features: [
      "Analyses illimitées",
      "Benchmark sectoriel anonymisé",
      "Export Excel",
      "White-label PDF",
      "Toutes les features Essentiel",
      "Support prioritaire",
    ],
    cta: "Passer Pro",
    href: "mailto:contact@esg-optimizer.fr?subject=Plan Pro",
    highlighted: true,
    current: false,
    badge: "Le plus populaire",
    color: { bg: "bg-[#F0FDF4]", border: "border-[#16a34a]", text: "text-[#166534]", price: "text-[#166534]" },
  },
  {
    name: "Enterprise",
    price: "Sur devis",
    sub: "Contrat sur mesure",
    features: [
      "SSO + SAML",
      "Multi-utilisateurs RBAC",
      "API REST dédiée",
      "SLA garanti",
      "Onboarding personnalisé",
      "Hébergement dédié RGPD",
    ],
    cta: "Nous contacter",
    href: "mailto:contact@esg-optimizer.fr?subject=Enterprise",
    highlighted: false,
    current: false,
    badge: null,
    color: { bg: "bg-[#FAF5FF]", border: "border-[#7c3aed]", text: "text-[#7c3aed]", price: "text-[#7c3aed]" },
  },
];

const COMPARISON = [
  { item: "Prix", cabinet: "5 000-30 000€", esg: "39€ par analyse" },
  { item: "Délai", cabinet: "4-6 semaines", esg: "3 minutes" },
  { item: "ESRS couverts", cabinet: "10/10", esg: "10/10" },
  { item: "PDF structuré", cabinet: "✓", esg: "✓" },
  { item: "Delta Report N/N-1", cabinet: "✓", esg: "✓ (Essentiel+)" },
  { item: "Badge LinkedIn", cabinet: "✗", esg: "✓" },
  { item: "Disponible 24h/24", cabinet: "✗", esg: "✓" },
];

export default function TarifsAppPage() {
  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-10">
        <h1
          className="text-4xl text-[#1A3D22] mb-2"
          style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
        >
          Tarifs
        </h1>
        <p className="text-[#6B7280]">
          Les cabinets facturent 5 000-30 000€ avec 4-6 semaines de délai.
          Nous faisons ça en 3 minutes pour 39€.
        </p>
      </div>

      {/* Plans */}
      <div className="grid md:grid-cols-4 gap-5 mb-12 items-stretch">
        {PLANS.map((plan) => (
          <div
            key={plan.name}
            className={`relative flex flex-col rounded-xl border-2 p-6 ${
              plan.highlighted
                ? "bg-[#1A3D22] border-[#1A3D22] shadow-xl"
                : `${plan.color.bg} ${plan.color.border} shadow-sm`
            }`}
          >
            {plan.badge && (
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-[#7FC686] text-[#1A3D22] text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap">
                {plan.badge}
              </div>
            )}

            <div className="mb-5">
              <p className={`text-xs font-bold uppercase tracking-wider mb-2 ${plan.highlighted ? "text-[#D4F0D8]" : plan.color.text}`}>
                {plan.name}
              </p>
              <p
                className={`text-3xl font-bold ${plan.highlighted ? "text-white" : plan.color.price}`}
                style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
              >
                {plan.price}
              </p>
              {plan.sub && (
                <p className={`text-xs mt-0.5 ${plan.highlighted ? "text-[#D4F0D8]/60" : "text-[#6B7280]"}`}>
                  {plan.sub}
                </p>
              )}
            </div>

            <ul className="space-y-2.5 flex-1 mb-6">
              {plan.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm">
                  <CheckCircle className={`w-4 h-4 flex-shrink-0 mt-0.5 ${plan.highlighted ? "text-[#7FC686]" : plan.color.text}`} />
                  <span className={plan.highlighted ? "text-white/85" : "text-[#1C1C1C]"}>{f}</span>
                </li>
              ))}
            </ul>

            <a
              href={plan.href}
              className={`block text-center py-2.5 rounded-lg font-semibold text-sm transition-all ${
                plan.current
                  ? "bg-[#E5E0D8] text-[#6B7280] cursor-default"
                  : plan.highlighted
                  ? "bg-[#7FC686] text-[#1A3D22] hover:bg-[#D4F0D8]"
                  : "bg-[#1A3D22] text-[#D4F0D8] hover:bg-[#2A5C34]"
              }`}
            >
              {plan.cta}
            </a>
          </div>
        ))}
      </div>

      {/* Comparatif */}
      <div className="card overflow-hidden p-0 mb-8">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[#1A3D22] text-white">
              <th className="text-left px-6 py-3 font-medium">Critère</th>
              <th className="text-center px-6 py-3 font-medium text-[#6B7280]">Cabinet traditionnel</th>
              <th className="text-center px-6 py-3 font-medium text-[#7FC686]">ESG Optimizer</th>
            </tr>
          </thead>
          <tbody>
            {COMPARISON.map(({ item, cabinet, esg }, i) => (
              <tr key={item} className={i % 2 === 0 ? "bg-white" : "bg-[#F7F2E8]"}>
                <td className="px-6 py-3 font-medium text-[#1C1C1C]">{item}</td>
                <td className="px-6 py-3 text-center text-[#6B7280]">{cabinet}</td>
                <td className="px-6 py-3 text-center font-semibold text-[#1A3D22]">{esg}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-center">
        <a
          href="mailto:contact@esg-optimizer.fr"
          className="inline-flex items-center gap-2 text-sm font-semibold bg-[#1A3D22] text-[#D4F0D8] hover:bg-[#2A5C34] px-6 py-3 rounded-lg transition-colors"
        >
          <ExternalLink className="w-4 h-4" />
          Nous contacter
        </a>
      </div>
    </div>
  );
}