import type { Metadata } from "next";
import Link from "next/link";
import { CheckCircle, Leaf, ArrowRight, Zap, BarChart2, Upload, FileText, Award } from "lucide-react";
import { LandingNavbar } from "@/components/LandingNavbar";

export const metadata: Metadata = {
  title: "Audit de conformité CSRD / ESRS pour les PME",
  description:
    "ESG Optimizer analyse vos rapports de durabilité, calcule votre score ESG (E/S/G) et identifie vos écarts de conformité CSRD / ESRS. Première analyse offerte.",
  alternates: { canonical: "/" },
};

const PLANS = [
  {
    name: "Découverte",
    price: "Gratuit",
    sub: "",
    badge: null,
    features: [
      "1 analyse incluse",
      "Score ESG global",
      "Rapport PDF 3 pages",
      "Watermark sur le PDF",
    ],
    cta: "Commencer gratuitement",
    href: "/sign-up",
    highlighted: false,
  },
  {
    name: "Essentiel",
    price: "39€",
    sub: "par analyse · paiement unique",
    badge: null,
    features: [
      "Rapport PDF 8+ pages complet",
      "Sans watermark",
      "Delta Report N vs N-1",
      "Historique 12 mois",
      "Scores E / S / G détaillés",
      "10 ESRS couverts",
    ],
    cta: "Payer 39€",
    href: "/sign-up?plan=essential",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "129€",
    sub: "/ mois · ou 990€/an",
    badge: "Le plus populaire",
    features: [
      "Analyses illimitées",
      "Benchmark sectoriel anonymisé",
      "Export Excel",
      "White-label PDF",
      "Toutes les features Essentiel",
    ],
    cta: "Choisir Pro",
    href: "/sign-up?plan=pro",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Sur devis",
    sub: "Contrat sur mesure",
    badge: null,
    features: [
      "SSO + SAML",
      "Multi-utilisateurs RBAC",
      "API REST dédiée",
      "SLA garanti",
      "Onboarding personnalisé",
    ],
    cta: "Nous contacter",
    href: "mailto:contact@esg-optimizer.fr",
    highlighted: false,
  },
];

const HOW = [
  {
    step: "1",
    title: "Uploadez votre rapport",
    desc: "PDF, DOCX ou XLSX - notre extracteur IA gère tous les formats jusqu'à 500 pages.",
    icon: Upload,
  },
  {
    step: "2",
    title: "Analyse GPT-4o en 3 min",
    desc: "Notre moteur d'analyse score les 10 ESRS (E1 à G1), détecte vos non-conformités et génère des recommandations concrètes.",
    icon: BarChart2,
  },
  {
    step: "3",
    title: "Rapport + Badge LinkedIn",
    desc: "Téléchargez votre rapport PDF structuré et partagez votre badge CSRD sur LinkedIn.",
    icon: FileText,
  },
];

const STATS = [
  { value: "3 min", label: "Durée d'une analyse", color: "#16a34a" },
  { value: "10", label: "Standards ESRS couverts", color: "#2563eb" },
  { value: "39€", label: "Prix d'entrée (vs 5 000-30 000€ cabinet)", color: "#1A3D22" },
  { value: "15 000+", label: "Entreprises françaises concernées CSRD 2026", color: "#7c3aed" },
];

const FAQ = [
  {
    q: "C'est quoi la différence avec un cabinet ESG ?",
    a: "Un cabinet facture 5 000 à 30 000€ avec 4 à 6 semaines de délai. ESG Optimizer AI produit un rapport complet en 3 minutes pour 39€. Vous gardez le contrôle, nous automatisons l'analyse.",
  },
  {
    q: "La première analyse est-elle vraiment gratuite ?",
    a: "Oui. À la création de votre compte, vous bénéficiez d'une analyse complète offerte, sans carte bancaire. Vous obtenez votre score ESG global et un aperçu de vos forces et faiblesses. Les rapports détaillés et le suivi dans le temps sont ensuite accessibles via les offres payantes.",
  },
  {
    q: "Quels formats de rapports acceptez-vous ?",
    a: "PDF, DOCX et XLSX. Nos extracteurs gèrent les rapports de 1 à 500 pages.",
  },
  {
    q: "Vos scores sont-ils reconnus officiellement ?",
    a: "Nos scores sont indicatifs et basés sur les ESRS (European Sustainability Reporting Standards). Ils ne remplacent pas un audit officiel par un commissaire aux comptes agréé, mais ils vous donnent une base solide pour préparer votre conformité CSRD.",
  },
  {
    q: "Mes données sont-elles sécurisées ?",
    a: "Vos fichiers sont chiffrés en transit et au repos, hébergés en Europe (Google Cloud europe-west1, Belgique), et supprimés après extraction du texte. Nous sommes RGPD compliant.",
  },
];


const JSON_LD = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://esg-optimizer.fr/#organization",
      name: "ESG Optimizer",
      url: "https://esg-optimizer.fr",
      logo: "https://esg-optimizer.fr/icon-512x512.png",
      description:
        "Plateforme d'audit de conformité CSRD / ESRS pour les PME françaises.",
      email: "contact@esg-optimizer.fr",
    },
    {
      "@type": "WebSite",
      "@id": "https://esg-optimizer.fr/#website",
      url: "https://esg-optimizer.fr",
      name: "ESG Optimizer",
      inLanguage: "fr-FR",
      publisher: { "@id": "https://esg-optimizer.fr/#organization" },
    },
    {
      "@type": "SoftwareApplication",
      name: "ESG Optimizer",
      applicationCategory: "BusinessApplication",
      operatingSystem: "Web",
      url: "https://esg-optimizer.fr",
      description:
        "Analyse automatisée de rapports de durabilité : scoring ESG (E/S/G), couverture ESRS et recommandations de conformité CSRD.",
      offers: [
        { "@type": "Offer", name: "Découverte", price: "0", priceCurrency: "EUR" },
        { "@type": "Offer", name: "Essentiel", price: "39", priceCurrency: "EUR" },
        { "@type": "Offer", name: "Pro", price: "129", priceCurrency: "EUR" },
      ],
    },
    {
      "@type": "FAQPage",
      mainEntity: FAQ.map(({ q, a }) => ({
        "@type": "Question",
        name: q,
        acceptedAnswer: { "@type": "Answer", text: a },
      })),
    },
  ],
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F7F2E8]">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }}
      />
      <LandingNavbar />

      {/* -- Hero --------------------------------------- */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#D4F0D8] text-[#1A3D22] text-sm font-medium mb-6">
            <Zap className="w-3.5 h-3.5" />
            CSRD 2026 - Deadline imminente pour 15 000+ entreprises françaises
          </div>
          <h1
            className="text-5xl md:text-6xl text-[#1A3D22] mb-6 leading-tight"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            Votre audit CSRD en 3 minutes pour 39€
          </h1>
          <p className="text-lg text-[#6B7280] mb-4 max-w-xl mx-auto leading-relaxed">
            Les cabinets facturent 5 000 à 30 000€ avec 4 à 6 semaines de délai.
            Notre IA analyse votre rapport de durabilité et produit un rapport structuré
            avec scores ESRS, non-conformités et recommandations.
          </p>
          <p className="text-sm text-[#1A3D22] font-medium mb-10">
            Construit par un étudiant en Master 2 RSE à l'UPEC
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/sign-up" className="btn-primary text-base px-8 py-3">
              Analyser mon rapport gratuitement
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a href="#tarifs" className="btn-secondary text-base px-8 py-3">
              Voir les tarifs
            </a>
          </div>
          <p className="mt-4 text-sm text-[#6B7280]">
            1 analyse offerte à l&apos;inscription · Sans carte bancaire · Résultat en quelques minutes
          </p>
        </div>
      </section>

      {/* -- Stats -------------------------------------- */}
      <section className="py-12 px-6 bg-[#1A3D22]">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6">
          {STATS.map(({ value, label }) => (
            <div key={label} className="text-center">
              <div
                className="text-3xl font-bold text-[#7FC686] mb-1"
                style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
              >
                {value}
              </div>
              <div className="text-xs text-[#D4F0D8]/70 leading-snug">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* -- Première analyse offerte ------------------- */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FEF3C7] text-[#D97706] text-sm font-medium mb-4">
            <Zap className="w-3.5 h-3.5" /> Première analyse offerte, sans carte bancaire
          </div>
          <h2
            className="text-3xl text-[#1A3D22] mb-4"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            Commencez gratuitement
          </h2>
          <p className="text-[#6B7280] mb-6 leading-relaxed">
            Créez votre compte en moins d&apos;une minute, déposez votre rapport de
            durabilité et obtenez votre score ESG ainsi que vos premières
            recommandations. Aucun engagement, aucune carte bancaire demandée.
          </p>
          <Link
            href="/sign-up"
            className="btn-primary text-base px-8 py-3 inline-flex"
          >
            Créer mon compte et lancer l&apos;analyse
          </Link>
          <p className="mt-3 text-xs text-[#6B7280]">
            Vos fichiers restent confidentiels et sont supprimés après extraction.
          </p>
        </div>
      </section>

      {/* -- Comment ça marche -------------------------- */}
      <section id="comment" className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <h2
            className="text-3xl text-center text-[#1A3D22] mb-12"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
            Comment ça marche
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {HOW.map(({ step, title, desc, icon: Icon }) => (
              <div key={step} className="text-center">
                <div className="w-12 h-12 bg-[#D4F0D8] rounded-xl flex items-center justify-center mx-auto mb-4">
                  <Icon className="w-6 h-6 text-[#1A3D22]" />
                </div>
                <div className="text-xs font-mono text-[#6B7280] mb-2">Étape {step}</div>
                <h3 className="text-lg font-semibold text-[#1A3D22] mb-2">{title}</h3>
                <p className="text-sm text-[#6B7280] leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          {/* Badge LinkedIn */}
          <div className="mt-16 card bg-gradient-to-r from-[#1A3D22] to-[#2A5C34] border-0 text-center py-10">
            <div className="w-12 h-12 bg-[#D4F0D8]/20 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Award className="w-6 h-6 text-[#7FC686]" />
            </div>
            <h3
              className="text-2xl text-[#D4F0D8] mb-3"
              style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
            >
              Badge LinkedIn partageable
            </h3>
            <p className="text-[#D4F0D8]/70 text-sm max-w-lg mx-auto leading-relaxed">
              Après chaque analyse, générez votre badge CSRD (PNG 1200×630) avec votre score,
              le nom de votre entreprise et votre statut "CSRD Ready". Partagez-le sur LinkedIn
              et créez un effet viral - vos fournisseurs voudront aussi se conformer.
            </p>
          </div>
        </div>
      </section>

      {/* -- Pricing ------------------------------------ */}
      <section id="tarifs" className="py-20 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2
              className="text-4xl text-[#1A3D22] mb-3"
              style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
            >
              Tarifs simples, sans engagement
            </h2>
            <p className="text-[#6B7280]">
              vs. 5 000-30 000€ et 4-6 semaines de délai en cabinet traditionnel
            </p>
          </div>
          <div className="grid md:grid-cols-4 gap-6 items-stretch">
            {PLANS.map((plan) => (
              <div
                key={plan.name}
                className={`relative flex flex-col rounded-xl border p-6 ${
                  plan.highlighted
                    ? "border-[#1A3D22] bg-[#1A3D22] text-white shadow-xl scale-[1.03]"
                    : "border-[#E5E0D8] bg-white shadow-sm"
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[#7FC686] text-[#1A3D22] text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap">
                    {plan.badge}
                  </div>
                )}
                <div className="mb-5">
                  <p className={`text-sm font-semibold mb-1 ${plan.highlighted ? "text-[#D4F0D8]" : "text-[#6B7280]"}`}>
                    {plan.name}
                  </p>
                  <p
                    className={`text-3xl font-bold ${plan.highlighted ? "text-white" : "text-[#1A3D22]"}`}
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
                      <CheckCircle className={`w-4 h-4 flex-shrink-0 mt-0.5 ${plan.highlighted ? "text-[#7FC686]" : "text-[#1A3D22]"}`} />
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
        </div>
      </section>

      {/* -- FAQ ---------------------------------------- */}
      <section className="py-20 px-6">
        <div className="max-w-2xl mx-auto">
          <h2
            className="text-3xl text-center text-[#1A3D22] mb-10"
            style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
          >
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
      </section>

      {/* -- Footer ------------------------------------- */}
      <footer className="py-12 px-6 border-t border-[#E5E0D8] bg-white">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Logo variant="light" size="sm" showTagline={false} />
            <span className="text-xs text-[#6B7280]">· esg-optimizer.fr</span>
          </div>
          <div className="flex gap-6 text-sm text-[#6B7280]">
            <Link href="/mentions" className="hover:text-[#1A3D22]">Mentions légales & Méthodo</Link>
            <a href="#tarifs" className="hover:text-[#1A3D22]">Tarifs</a>
            <a
              href="https://www.linkedin.com/in/adama-diallo-rse"
              target="_blank"
              rel="