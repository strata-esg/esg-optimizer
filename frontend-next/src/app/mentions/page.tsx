import type { Metadata } from "next";
import Link from "next/link";
import { Leaf } from "lucide-react";

export const metadata: Metadata = {
  title: "Mentions légales & Méthodologie",
  description:
    "Mentions légales, méthodologie d'analyse ESRS et politique de protection des données (RGPD) d'ESG Optimizer.",
  alternates: { canonical: "/mentions" },
};

const ESRS_TOPICS = [
  { code: "E1", label: "Changement climatique", pilier: "E" },
  { code: "E2", label: "Pollution", pilier: "E" },
  { code: "E3", label: "Ressources marines & eau", pilier: "E" },
  { code: "E4", label: "Biodiversité & écosystèmes", pilier: "E" },
  { code: "E5", label: "Utilisation des ressources & économie circulaire", pilier: "E" },
  { code: "S1", label: "Effectifs propres", pilier: "S" },
  { code: "S2", label: "Chaîne de valeur", pilier: "S" },
  { code: "S3", label: "Communautés affectées", pilier: "S" },
  { code: "S4", label: "Consommateurs & utilisateurs finaux", pilier: "S" },
  { code: "G1", label: "Conduite des affaires", pilier: "G" },
];

export default function MentionsPage() {
  return (
    <div className="min-h-screen bg-[#F7F2E8]">
      <header className="border-b border-[#E5E0D8] bg-[#F7F2E8]">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#1A3D22] rounded-lg flex items-center justify-center">
              <Leaf className="w-4 h-4 text-[#D4F0D8]" />
            </div>
            <span className="text-[#1A3D22] text-xl" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
              ESG Optimizer
            </span>
          </Link>
          <Link href="/" className="text-sm text-[#6B7280] hover:text-[#1A3D22]">← Accueil</Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12 space-y-8">
        <div>
          <h1 className="text-4xl text-[#1A3D22] mb-2" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
            Mentions légales & Méthodologie
          </h1>
          <p className="text-[#6B7280]">Transparence sur notre approche d'analyse ESG et nos obligations légales.</p>
        </div>

        {/* Qui sommes-nous */}
        <section className="card">
          <h2 className="text-2xl text-[#1A3D22] mb-4" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
            Qui sommes-nous
          </h2>
          <p className="text-sm text-[#1C1C1C] leading-relaxed mb-3">
            ESG Optimizer AI est un SaaS d'audit de conformité CSRD/ESRS, développé par{" "}
            <strong>Adama Diallo</strong>, étudiant en Master 2 RSE à l'UPEC (Université Paris-Est Créteil).
          </p>
          <p className="text-sm text-[#1C1C1C] leading-relaxed mb-3">
            Le projet répond à un problème réel : les cabinets ESG facturent 5 000 à 30 000€
            pour un audit CSRD avec 4 à 6 semaines de délai. La plupart des PME françaises
            (15 000+ concernées par la CSRD en 2026) n'ont ni les moyens ni le temps.
          </p>
          <div className="flex gap-3 flex-wrap mt-4">
            <a
              href="https://www.linkedin.com/in/adama-diallo-rse"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary text-sm"
            >
              LinkedIn - Adama Diallo RSE
            </a>
            <a href="mailto:contact@esg-optimizer.fr" className="btn-ghost text-sm">
              contact@esg-optimizer.fr
            </a>
          </div>
        </section>

        {/* Méthodologie */}
        <section className="card">
          <h2 className="text-2xl text-[#1A3D22] mb-4" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
            Méthodologie d'analyse
          </h2>
          <p className="text-sm text-[#6B7280] leading-relaxed mb-4">
            Notre moteur IA (GPT-4o, temperature 0.2 pour des résultats reproductibles) analyse
            vos rapports de durabilité en s'appuyant sur les{" "}
            <strong>ESRS - European Sustainability Reporting Standards</strong> définis par l'EFRAG
            dans le cadre de la directive CSRD. Nous couvrons les 10 thématiques suivantes :
          </p>
          <div className="grid md:grid-cols-2 gap-3 mb-4">
            {ESRS_TOPICS.map(({ code, label, pilier }) => {
              const style =
                pilier === "E"
                  ? "bg-[#D4F0D8] text-[#1A3D22] border-[#7FC686]"
                  : pilier === "S"
                  ? "bg-[#DBEAFE] text-[#1e40af] border-[#93C5FD]"
                  : "bg-[#FEF3C7] text-[#92400E] border-[#FCD34D]";
              return (
                <div key={code} className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border ${style}`}>
                  <span className="font-mono text-xs font-bold w-8">{code}</span>
                  <span className="text-sm">{label}</span>
                </div>
              );
            })}
          </div>
          <div className="bg-[#FEF3C7] border border-[#FCD34D] rounded-lg px-4 py-3 text-sm text-[#92400E]">
            <strong>Important :</strong> Nos scores sont indicatifs et basés sur une analyse IA.
            Ils ne constituent pas un audit officiel et ne remplacent pas l'intervention d'un
            commissaire aux comptes agréé pour votre certification CSRD.
          </div>
        </section>

        {/* Stack technique */}
        <section className="card">
          <h2 className="text-2xl text-[#1A3D22] mb-4" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
            Stack technique
          </h2>
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="font-semibold text-[#1A3D22] mb-2">Backend</p>
              <ul className="space-y-1 text-[#6B7280]">
                <li>Python 3.11+ / FastAPI / Uvicorn</li>
                <li>PostgreSQL (Railway)</li>
                <li>OpenAI GPT-4o</li>
                <li>PyMuPDF · python-docx · openpyxl</li>
                <li>Stripe (paiements)</li>
                <li>Resend (emails transactionnels)</li>
                <li>Cloudflare R2 (stockage)</li>
                <li>Sentry (monitoring)</li>
              </ul>
            </div>
            <div>
              <p className="font-semibold text-[#1A3D22] mb-2">Frontend (V2 en cours)</p>
              <ul className="space-y-1 text-[#6B7280]">
                <li>Next.js 14 (App Router)</li>
                <li>Tailwind CSS</li>
                <li>Clerk (authentification)</li>
                <li>Supabase (base de données)</li>
                <li>Vercel (hébergement)</li>
              </ul>
            </div>
            <div>
              <p className="font-semibold text-[#1A3D22] mb-2">Infra</p>
              <ul className="space-y-1 text-[#6B7280]">
                <li>Railway (backend)</li>
                <li>Docker multi-stage</li>
                <li>Google Cloud europe-west1</li>
                <li>RGPD compliant</li>
                <li>esg-optimizer.fr</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Protection des données */}
        <section className="card">
          <h2 className="text-2xl text-[#1A3D22] mb-4" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
            Protection des données (RGPD)
          </h2>
          <div className="space-y-3 text-sm text-[#1C1C1C] leading-relaxed">
            <p><strong>Responsable du traitement :</strong> Adama Diallo - contact@esg-optimizer.fr</p>
            <p><strong>Données collectées :</strong> Email, nom, fichiers uploadés pour analyse.</p>
            <p>
              <strong>Durée de conservation des fichiers :</strong> Vos fichiers sont supprimés
              immédiatement après extraction du texte. Seuls les résultats d'analyse sont conservés.
            </p>
            <p>
              <strong>Hébergement :</strong> Railway / Google Cloud europe-west1 (Belgique) - conforme RGPD.
              Les adresses IP ne sont jamais stockées en clair (hachage SHA-256).
            </p>
            <p>
              <strong>Vos droits :</strong> Accès, rectification, suppression via votre espace
              Paramètres ou par email à contact@esg-optimizer.fr. Réponse sous 72h.
            </p>
            <p>
              <strong>Cookies :</strong> Uniquement fonctionnels (session) et analytiques anonymisés
              (Umami, sans tracking cross-site).
            </p>
          </div>
        </section>

        {/* Mentions légales */}
        <section className="card">
          <h2 className="text-2xl text-[#1A3D22] mb-4" style={{ fontFamily: "DM Serif Display, Georgia, serif" }}>
            Mentions légales
          </h2>
          <div className="text-sm text-[#6B7280] space-y-2 leading-relaxed">
            <p><strong className="text-[#1C1C1C]">Éditeur :</strong> Adama Diallo - ESG Optimizer AI</p>
            <p><strong className="text-[#1C1C1C]">Site :</strong> esg-optimizer.fr</p>
            <p><strong className="text-[#1C1C1C]">Contact :</strong> contact@esg-optimizer.fr</p>
            <p><strong className="text-[#1C1C1C]">Hébergeur :</strong> Railway (hébergement principal) · Vercel (frontend)</p>
            <p>
              Les scores ESG produits par ESG Optimizer AI sont fournis à titre indicatif.
              L'éditeur ne peut être tenu responsable de décisions prises sur la seule base
              de ces résultats. Pour une certification CSRD officielle, consultez un commissaire
              aux comptes agréé.
            </p>
            <p>
              Toute reproduction, même partielle, du contenu de ce site est interdite
              sans autorisation écrite préalable de l&apos;éditeur.
            </p>
          </div>
        </section>

        <div className="text-center pt-4">
          <Link href="/" className="btn-secondary text-sm">
            Retour à l&apos;accueil
          </Link>
        </div>
      </main>
    </div>
  );
}