import Link from "next/link";
import { CheckCircle, Leaf } from "lucide-react";

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
    cta: "Commencer gratuitement",
    href: "/sign-up",
    highlighted: false,
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
      "10 ESRS couverts (E1→G1)",
      "Delta Report N vs N-1",
      "Conservation historique 12 mois",
      "Support email",
    ],
    cta: "Payer 39€ — Accès immédiat",
    href: "/sign-up?plan=essential",
    highlighted: false,
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
    cta: "Choisir Pro",
    href: "/sign-up?plan=pro",
    highlighted: true,
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
    href: "mailto:contact@esg-optimizer.fr",
    highlighted: false,
    badge: null,
    color: { bg: "bg-[#FAF5FF]", border: "border-[#7c3aed]", text: "text-[#7c3aed]", price: "text-[#7c3aed]" },
  },
];

const FAQ = [
  {
    q: "C'est quoi la différence avec un cabinet ESG ?",
    a: "Un cabinet facture 5 000 à 30 000€ avec 4 à 6 semaines de délai. ESG Optimizer AI produit un rapport complet en 3 minutes pour 39€. Idéal pour les PME qui ont besoin d'une première lecture de conformité avant d'engager un auditeur officiel.",
  },
  {
    q: "Puis-je annuler mon abonnement Pro à tout moment ?",
    a: "Oui, sans engagement. Votre abonnement reste actif jusqu'à la fin de la période payée, sans renouvellement automatique si vous annulez.",
  },
  {
    q: "Le plan Essentiel est-il vraiment un paiement unique ?",
    a: "Oui. Vous payez 39€ pour une analyse complète. Pas d'abonnement, pas de surprise. Vous rachetez quand vous avez un nouveau rapport à analyser.",
  },
  {
    q: "Vos scores ESRS sont-ils officiellement reconnus ?",
    a: "Nos scores sont basés sur les European Sustainability Reporting Standards (ESRS) définis par l'EFRAG. Ils sont indicatifs et vous donnent une base solide pour préparer votre conformité CSRD, mais ne remplacent pas un audit par un commissaire aux comptes agréé.",
  },
  {
    q: "Mes données sont-elles sécurisées ?",
    a: "Vos fichiers sont chiffrés en transit et au repos, hébergés en Europe (Google Cloud europe-west1, Belgique), et supprimés après extraction du texte. Nous sommes RGPD compliant et ne revendons jamais vos données.",
  },
  {
    q: "Avez-vous des codes promo ou essais gratuits ?",
    a: "Oui, des codes promo sont disponibles ponctuellement (100% off). Contactez-nous à contact@esg-optimizer.fr ou suivez notre LinkedIn pour les opportunités.",
  },
];

const COMPARISON = [
  { item: "Prix", cabinet: "5 000–30 000€", esg: "39€ par analyse" },
  { item: "Délai", cabinet: "4–6 semaines", esg: "3 minutes" },
  { item: "ESRS couverts", cabinet: "10/10", esg: "10/10" },
  { item: "PDF structuré", cabinet: "✓", esg: "✓" },
  { item: "Delta Report N/N-1", cabinet: "✓", esg: "✓ (Essentiel+)" },
  { item: "Badge LinkedIn", cabinet: "✗", esg: "✓" },
  { item: "Disponible 24h/24", cabinet: "✗", esg: "✓" },
  { item: "Mise à jour instantanée", cabinet: "✗", esg: "✓" },
];

export default function TarifsPage() {
  return (
    <div className="min-h-screen bg-[#F7F2E8]">
      <header className="border-b border-[#E5E0D8] bg-[#F7F2E8]">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#1A3D22] rounded-lg flex items-center justify-center">
              <Leaf className="w-4 h-4 text-[#D4F0D8]" />
            </div>
            <span className="text-[#1A3D22] text-xl" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
              ESG Optimizer
            </span>
          </Link>
          <div className="flex gap-3">
            <Link href="/sign-in" className="btn-ghost text-sm">Connexion</Link>
            <Link href="/sign-up" className="btn-primary text-sm">Essai gratuit</Link>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-16">
        {/* Header */}
        <div className="text-center mb-14">
          <h1 className="text-5xl text-[#1A3D22] mb-4" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
            Tarifs simples, sans engagement
          </h1>
          <p className="text-lg text-[#6B7280]">
            Les cabinets facturent 5 000–30 000€ et prennent 4–6 semaines.
          </p>
          <p className="text-lg font-semibold text-[#1A3D22]">
            Nous faisons ça en 3 minutes pour 39€.
          </p>
        </div>

        {/* Plans */}
        <div className="grid md:grid-cols-4 gap-5 mb-16 items-stretch">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`relative flex flex-col rounded-xl border-2 p-6 ${
                plan.highlighted
                  ? "bg-[#1A3D22] border-[#1A3D22] shadow-xl scale-[1.03]"
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

              <Link
                href={plan.href}
                className={`block text-center py-2.5 rounded-lg font-semibold text-sm transition-all ${
                  plan.highlighted
                    ? "bg-[#7FC686] text-[#1A3D22] hover:bg-[#D4F0D8]"
                    : "bg-[#1A3D22] text-[#D4F0D8] hover:bg-[#2A5C34]"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        {/* Comparatif */}
        <div className="mb-16">
          <h2 className="text-3xl text-center text-[#1A3D22] mb-8" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
            ESG Optimizer vs Cabinet traditionnel
          </h2>
          <div className="card overflow-hidden p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#1A3D22] text-white">
                  <th className="text-left px-6 py-3 font-medium">Critère</th>
                  <th className="text-center px-6 py-3 font-medium text-[#6B7280]">Cabinet traditionnel</th>
                  <th className="text-center px-6 py-3 font-medium text-[#7FC686]">ESG Optimizer ✓</th>
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
        </div>

        {/* FAQ */}
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl text-center text-[#1A3D22] mb-8" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
            Questions fréquentes
          </h2>
          <div className="space-y-4">
            {FAQ.map(({ q, a }) => (
              <div key={q} className="card">
                <p className="font-semibold text-[#1A3D22] mb-2">{q}</p>
                <p className="text-sm text-[#6B7280] leading-relaxed">{a}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
