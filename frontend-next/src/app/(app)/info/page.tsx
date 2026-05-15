"use client";

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

export default function MentionsAppPage() {
  return (
    <div className="w-full">
      <div className="mb-10">
        <h1
          className="text-4xl text-[#1A3D22] mb-2"
          style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
        >
          Mentions légales & Méthodologie
        </h1>
        <p className="text-[#6B7280]">Transparence sur notre approche d'analyse ESG et nos obligations légales.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Qui sommes-nous */}
        <section className="card">
          <h2 className="text-xl text-[#1A3D22] mb-4 font-semibold">Qui sommes-nous</h2>
          <p className="text-sm text-[#1C1C1C] leading-relaxed mb-3">
            ESG Optimizer AI est un SaaS d'audit de conformité CSRD/ESRS, développé par{" "}
            <strong>Adama Diallo</strong>, étudiant en Master 2 RSE à l'UPEC (Université Paris-Est Créteil).
          </p>
          <p className="text-sm text-[#1C1C1C] leading-relaxed mb-4">
            Le projet répond à un problème réel : les cabinets ESG facturent 5 000 à 30 000€
            pour un audit CSRD avec 4 à 6 semaines de délai. La plupart des PME françaises
            (15 000+ concernées par la CSRD en 2026) n'ont ni les moyens ni le temps.
          </p>
          <div className="flex gap-3 flex-wrap">
            <a
              href="https://www.linkedin.com/in/adama-diallo-rse"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary text-sm"
            >
              LinkedIn
            </a>
            <a href="mailto:contact@esg-optimizer.fr" className="btn-ghost text-sm">
              contact@esg-optimizer.fr
            </a>
          </div>
        </section>

        {/* Mentions légales */}
        <section className="card">
          <h2 className="text-xl text-[#1A3D22] mb-4 font-semibold">Mentions légales</h2>
          <div className="text-sm text-[#6B7280] space-y-2 leading-relaxed">
            <p><strong className="text-[#1C1C1C]">Éditeur :</strong> Adama Diallo - ESG Optimizer AI</p>
            <p><strong className="text-[#1C1C1C]">Site :</strong> esg-optimizer.fr</p>
            <p><strong className="text-[#1C1C1C]">Contact :</strong> contact@esg-optimizer.fr</p>
            <p><strong className="text-[#1C1C1C]">Hébergeur :</strong> Railway (backend) · Vercel (frontend)</p>
            <p className="mt-3">
              Les scores ESG produits par ESG Optimizer AI sont fournis à titre indicatif.
              L'éditeur ne peut être tenu responsable de décisions prises sur la seule base
              de ces résultats. Pour une certification CSRD officielle, consultez un commissaire
              aux comptes agréé.
            </p>
          </div>
        </section>

        {/* Méthodologie */}
        <section className="card md:col-span-2">
          <h2 className="text-xl text-[#1A3D22] mb-4 font-semibold">Méthodologie d'analyse</h2>
          <p className="text-sm text-[#6B7280] leading-relaxed mb-4">
            Notre moteur IA (GPT-4o, temperature 0.2) analyse vos rapports de durabilité en s'appuyant sur les{" "}
            <strong className="text-[#1C1C1C]">ESRS - European Sustainability Reporting Standards</strong> définis par l'EFRAG
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

        {/* RGPD */}
        <section className="card md:col-span-2">
          <h2 className="text-xl text-[#1A3D22] mb-4 font-semibold">Protection des données (RGPD)</h2>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-[#1C1C1C] leading-relaxed">
            <p><strong>Responsable :</strong> Adama Diallo - contact@esg-optimizer.fr</p>
            <p><strong>Données collectées :</strong> Email, nom, fichiers uploadés pour analyse.</p>
            <p><strong>Conservation :</strong> Fichiers supprimés immédiatement après extraction. Seuls les résultats sont conservés.</p>
            <p><strong>Hébergement :</strong> Railway / Google Cloud europe-west1 (Belgique) - conforme RGPD.</p>
            <p><strong>Vos droits :</strong> Accès, rectification, suppression via Paramètres ou par email. Réponse sous 72h.</p>
            <p><strong>Cookies :</strong> Uniquement fonctionnels (sessions, Clerk et PostHog). Aucun cookie publicitaire.</p>
          </div>
        </section>
      </div>
    </div>
  );
}