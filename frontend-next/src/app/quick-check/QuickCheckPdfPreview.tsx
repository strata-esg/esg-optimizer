"use client";

import { useEffect } from "react";

interface Props {
  filename: string;
  scoreGlobal: number;
  csrdReady: boolean | null;
  strengths: string[];
  weaknesses: string[];
  onClose: () => void;
}

function scoreColor(score: number) {
  if (score >= 70) return { text: "#1A3D22", bg: "#D4F0D8", border: "#1A3D22" };
  if (score >= 40) return { text: "#D97706", bg: "#FEF3C7", border: "#D97706" };
  return { text: "#DC2626", bg: "#FEE2E2", border: "#DC2626" };
}

function csrdStage(csrdReady: boolean | null) {
  if (csrdReady === true) return { label: "CSRD Ready", color: "#1A3D22", bg: "#D4F0D8" };
  return { label: "Non conforme CSRD", color: "#DC2626", bg: "#FEE2E2" };
}

export default function QuickCheckPdfPreview({ filename, scoreGlobal, csrdReady, strengths, weaknesses, onClose }: Props) {
  const sc = scoreColor(scoreGlobal);
  const stage = csrdStage(csrdReady);
  const date = new Date().toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });

  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, []);

  const handlePrint = () => window.print();

  return (
    <>
      {/* Styles d'impression */}
      <style>{`
        @media print {
          body > *:not(#pdf-preview-root) { display: none !important; }
          #pdf-preview-root { position: static !important; }
          .no-print { display: none !important; }
          .pdf-page {
            page-break-after: always;
            page-break-inside: avoid;
            margin: 0;
            padding: 0;
          }
          .pdf-page:last-child { page-break-after: auto; }
          @page { size: A4; margin: 0; }
        }
      `}</style>

      {/* Overlay */}
      <div
        id="pdf-preview-root"
        className="fixed inset-0 z-50 bg-black/60 flex flex-col overflow-y-auto"
        style={{ fontFamily: "DM Sans, system-ui, sans-serif" }}
      >
        {/* Barre d'action */}
        <div className="no-print sticky top-0 z-10 bg-[#1A3D22] text-white px-6 py-3 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold">Aperçu PDF — 3 pages</span>
            <span className="text-xs text-white/60">Rapport préliminaire Quick Check</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handlePrint}
              className="flex items-center gap-2 bg-[#7FC686] text-[#1A3D22] font-bold px-4 py-1.5 rounded-lg text-sm hover:bg-[#D4F0D8] transition-all"
            >
              Enregistrer en PDF
            </button>
            <button
              onClick={onClose}
              className="text-white/70 hover:text-white text-sm px-3 py-1.5 rounded-lg hover:bg-white/10 transition-all"
            >
              Fermer ✕
            </button>
          </div>
        </div>

        {/* Pages */}
        <div className="flex flex-col items-center gap-6 py-8 px-4">

          {/* PAGE 1 — Couverture */}
          <div
            className="pdf-page bg-white w-[794px] max-w-full"
            style={{ minHeight: "1123px", position: "relative", overflow: "hidden" }}
          >
            {/* Watermark */}
            <div style={{
              position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
              pointerEvents: "none", zIndex: 1,
            }}>
              <span style={{
                fontSize: "5rem", fontWeight: 900, color: "rgba(26,61,34,0.04)",
                transform: "rotate(-35deg)", letterSpacing: "0.1em", textTransform: "uppercase",
                whiteSpace: "nowrap", userSelect: "none",
              }}>
                APERÇU GRATUIT
              </span>
            </div>

            {/* Header vert */}
            <div style={{
              background: "linear-gradient(135deg, #1A3D22 0%, #2A5C34 100%)",
              padding: "40px 48px 36px",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "24px" }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 8,
                  background: "#7FC686", display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  <span style={{ color: "#1A3D22", fontWeight: 900, fontSize: "1rem" }}>E</span>
                </div>
                <div>
                  <p style={{ color: "#D4F0D8", fontWeight: 700, fontSize: "1rem", margin: 0 }}>ESG Optimizer</p>
                  <p style={{ color: "#7FC686", fontSize: "0.7rem", margin: 0 }}>A STRATA PRODUCT</p>
                </div>
              </div>

              <h1 style={{
                fontFamily: "DM Serif Display, Georgia, serif",
                fontSize: "2.2rem", color: "white", margin: "0 0 8px", lineHeight: 1.2,
              }}>
                Rapport d&apos;Aperçu ESG
              </h1>
              <p style={{ color: "rgba(255,255,255,0.6)", fontSize: "0.85rem", margin: 0 }}>
                Diagnostic préliminaire — Version non certifiée
              </p>
            </div>

            {/* Corps page 1 */}
            <div style={{ padding: "40px 48px", position: "relative", zIndex: 2 }}>
              {/* Infos document */}
              <div style={{
                background: "#F7F2E8", borderRadius: 12, padding: "20px 24px", marginBottom: 32,
                border: "1px solid #E5E0D8",
              }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                  {[
                    { label: "Document analysé", value: filename },
                    { label: "Date du diagnostic", value: date },
                    { label: "Type d'analyse", value: "Quick Check ESG" },
                    { label: "Référentiel", value: "CSRD / ESRS (EFRAG)" },
                  ].map(({ label, value }) => (
                    <div key={label}>
                      <p style={{ fontSize: "0.68rem", color: "#6B7280", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 2px" }}>{label}</p>
                      <p style={{ fontSize: "0.88rem", fontWeight: 600, color: "#1C1C1C", margin: 0 }}>{value}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Score */}
              <div style={{ display: "flex", alignItems: "center", gap: 32, marginBottom: 32 }}>
                <div style={{
                  width: 140, height: 140, borderRadius: 20,
                  background: sc.bg, border: `3px solid ${sc.border}`,
                  display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                  flexShrink: 0,
                }}>
                  <span style={{
                    fontFamily: "DM Serif Display, Georgia, serif",
                    fontSize: "3.5rem", color: sc.text, lineHeight: 1,
                  }}>
                    {Math.round(scoreGlobal)}
                  </span>
                  <span style={{ fontSize: "0.78rem", color: sc.text, opacity: 0.7 }}>/100</span>
                </div>

                <div>
                  <p style={{ fontSize: "0.72rem", color: "#6B7280", textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 6px" }}>
                    Score ESG Global
                  </p>
                  <p style={{
                    fontFamily: "DM Serif Display, Georgia, serif",
                    fontSize: "1.6rem", color: sc.text, margin: "0 0 12px",
                  }}>
                    {scoreGlobal >= 70 ? "Niveau avancé" : scoreGlobal >= 40 ? "Niveau intermédiaire" : "Niveau initial"}
                  </p>
                  <span style={{
                    display: "inline-flex", alignItems: "center", gap: 6,
                    background: stage.bg, color: stage.color,
                    fontWeight: 700, fontSize: "0.82rem",
                    padding: "6px 14px", borderRadius: 20,
                  }}>
                    {stage.label}
                  </span>
                </div>
              </div>

              {/* Note bas de page */}
              <div style={{
                borderTop: "1px solid #E5E0D8", paddingTop: 20,
                display: "flex", alignItems: "center", gap: 12,
              }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8,
                  background: "#FEF3C7", display: "flex", alignItems: "center", justifyContent: "center",
                  flexShrink: 0,
                }}>
                  <span style={{ fontSize: "1rem" }}>⚠</span>
                </div>
                <p style={{ fontSize: "0.78rem", color: "#6B7280", margin: 0, lineHeight: 1.5 }}>
                  Ce rapport est un <strong style={{ color: "#1C1C1C" }}>aperçu préliminaire non certifié</strong>.
                  Il est généré automatiquement à partir d&apos;une analyse partielle du document.
                  Pour une analyse complète avec scores E/S/G détaillés, couverture ESRS et recommandations,{" "}
                  <strong style={{ color: "#1A3D22" }}>créez un compte gratuit sur esg-optimizer.fr</strong>.
                </p>
              </div>
            </div>

            {/* Footer page 1 */}
            <div style={{
              position: "absolute", bottom: 0, left: 0, right: 0,
              borderTop: "1px solid #E5E0D8",
              padding: "12px 48px",
              display: "flex", justifyContent: "space-between", alignItems: "center",
              background: "white",
            }}>
              <span style={{ fontSize: "0.72rem", color: "#9CA3AF" }}>esg-optimizer.fr — A STRATA Product</span>
              <span style={{ fontSize: "0.72rem", color: "#9CA3AF" }}>Page 1 / 3</span>
            </div>
          </div>

          {/* PAGE 2 — Résultats préliminaires */}
          <div
            className="pdf-page bg-white w-[794px] max-w-full"
            style={{ minHeight: "1123px", position: "relative", overflow: "hidden" }}
          >
            <div style={{
              position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
              pointerEvents: "none", zIndex: 1,
            }}>
              <span style={{
                fontSize: "5rem", fontWeight: 900, color: "rgba(26,61,34,0.04)",
                transform: "rotate(-35deg)", letterSpacing: "0.1em", textTransform: "uppercase",
                whiteSpace: "nowrap",
              }}>
                APERÇU GRATUIT
              </span>
            </div>

            {/* Header page 2 */}
            <div style={{
              background: "#F7F2E8", borderBottom: "1px solid #E5E0D8",
              padding: "20px 48px", display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <div>
                <p style={{ fontWeight: 700, color: "#1A3D22", margin: "0 0 2px", fontSize: "0.9rem" }}>ESG Optimizer</p>
                <p style={{ color: "#6B7280", fontSize: "0.75rem", margin: 0 }}>Résultats préliminaires</p>
              </div>
              <span style={{
                background: sc.bg, color: sc.text,
                fontWeight: 700, fontSize: "0.82rem",
                padding: "4px 12px", borderRadius: 20,
              }}>
                Score {Math.round(scoreGlobal)}/100
              </span>
            </div>

            <div style={{ padding: "36px 48px", position: "relative", zIndex: 2 }}>
              <h2 style={{
                fontFamily: "DM Serif Display, Georgia, serif",
                fontSize: "1.5rem", color: "#1A3D22", margin: "0 0 24px",
              }}>
                Analyse préliminaire
              </h2>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 32 }}>
                {/* Points forts */}
                <div style={{
                  background: "#F0FDF4", border: "1.5px solid #86EFAC",
                  borderRadius: 12, padding: "20px 20px",
                }}>
                  <p style={{
                    fontSize: "0.72rem", fontWeight: 700, color: "#065F46",
                    textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 12px",
                  }}>
                    Points forts identifiés
                  </p>
                  {strengths.length > 0 ? (
                    <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
                      {strengths.map((s, i) => (
                        <li key={i} style={{
                          display: "flex", alignItems: "flex-start", gap: 8,
                          marginBottom: 10, fontSize: "0.83rem", color: "#1C1C1C", lineHeight: 1.4,
                        }}>
                          <span style={{ color: "#1A3D22", fontWeight: 700, flexShrink: 0, marginTop: 1 }}>✓</span>
                          {s}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p style={{ color: "#9CA3AF", fontSize: "0.82rem", margin: 0 }}>Analyse en cours</p>
                  )}
                </div>

                {/* Axes d'amélioration */}
                <div style={{
                  background: "#FFFBEB", border: "1.5px solid #FDE68A",
                  borderRadius: 12, padding: "20px 20px",
                }}>
                  <p style={{
                    fontSize: "0.72rem", fontWeight: 700, color: "#92400E",
                    textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 12px",
                  }}>
                    Axes d&apos;amélioration
                  </p>
                  {weaknesses.length > 0 ? (
                    <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
                      {weaknesses.map((w, i) => (
                        <li key={i} style={{
                          display: "flex", alignItems: "flex-start", gap: 8,
                          marginBottom: 10, fontSize: "0.83rem", color: "#1C1C1C", lineHeight: 1.4,
                        }}>
                          <span style={{ color: "#D97706", fontWeight: 700, flexShrink: 0, marginTop: 1 }}>→</span>
                          {w}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p style={{ color: "#9CA3AF", fontSize: "0.82rem", margin: 0 }}>Analyse en cours</p>
                  )}
                </div>
              </div>

              {/* Section verrouillée — scores E/S/G */}
              <div style={{ marginBottom: 24, position: "relative" }}>
                <p style={{
                  fontSize: "0.72rem", fontWeight: 700, color: "#6B7280",
                  textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 12px",
                }}>
                  Scores détaillés par pilier (E/S/G)
                </p>
                <div style={{ position: "relative", borderRadius: 12, overflow: "hidden" }}>
                  {/* Contenu flou */}
                  <div style={{ filter: "blur(6px)", opacity: 0.4, padding: "16px", background: "#F9FAFB", border: "1px solid #E5E7EB", borderRadius: 12 }}>
                    {["Environnement (E)", "Social (S)", "Gouvernance (G)"].map((label) => (
                      <div key={label} style={{ marginBottom: 12 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                          <span style={{ fontSize: "0.82rem", color: "#374151" }}>{label}</span>
                          <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#1A3D22" }}>??/100</span>
                        </div>
                        <div style={{ height: 8, background: "#E5E7EB", borderRadius: 4 }}>
                          <div style={{ height: "100%", width: "65%", background: "#1A3D22", borderRadius: 4 }} />
                        </div>
                      </div>
                    ))}
                  </div>
                  {/* Overlay lock */}
                  <div style={{
                    position: "absolute", inset: 0,
                    display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                    background: "rgba(255,255,255,0.75)", borderRadius: 12,
                  }}>
                    <span style={{ fontSize: "1.5rem", marginBottom: 6 }}>🔒</span>
                    <p style={{ fontWeight: 700, color: "#1A3D22", fontSize: "0.85rem", margin: "0 0 2px" }}>
                      Disponible avec un compte
                    </p>
                    <p style={{ color: "#6B7280", fontSize: "0.75rem", margin: 0 }}>
                      Gratuit — esg-optimizer.fr
                    </p>
                  </div>
                </div>
              </div>

              {/* Section verrouillée — couverture ESRS */}
              <div style={{ position: "relative" }}>
                <p style={{
                  fontSize: "0.72rem", fontWeight: 700, color: "#6B7280",
                  textTransform: "uppercase", letterSpacing: "0.07em", margin: "0 0 12px",
                }}>
                  Couverture ESRS — 10 standards analysés
                </p>
                <div style={{ position: "relative", borderRadius: 12, overflow: "hidden" }}>
                  <div style={{ filter: "blur(5px)", opacity: 0.35, padding: "16px", background: "#F9FAFB", border: "1px solid #E5E7EB", borderRadius: 12 }}>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                      {["E1 Climat", "E2 Pollution", "E3 Eau", "E4 Biodiversité", "E5 Économie circulaire", "S1 Effectifs", "S2 Chaîne valeur", "S3 Communautés", "S4 Consommateurs", "G1 Gouvernance"].map((label) => (
                        <div key={label} style={{
                          display: "flex", alignItems: "center", gap: 8,
                          padding: "8px 10px", background: "white", borderRadius: 8,
                          border: "1px solid #E5E7EB", fontSize: "0.78rem", color: "#374151",
                        }}>
                          <span style={{ color: "#7FC686" }}>●</span>
                          {label}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div style={{
                    position: "absolute", inset: 0,
                    display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                    background: "rgba(255,255,255,0.75)", borderRadius: 12,
                  }}>
                    <span style={{ fontSize: "1.5rem", marginBottom: 6 }}>🔒</span>
                    <p style={{ fontWeight: 700, color: "#1A3D22", fontSize: "0.85rem", margin: "0 0 2px" }}>
                      Disponible avec un compte
                    </p>
                    <p style={{ color: "#6B7280", fontSize: "0.75rem", margin: 0 }}>
                      Gratuit — esg-optimizer.fr
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div style={{
              position: "absolute", bottom: 0, left: 0, right: 0,
              borderTop: "1px solid #E5E0D8", padding: "12px 48px",
              display: "flex", justifyContent: "space-between", alignItems: "center",
              background: "white",
            }}>
              <span style={{ fontSize: "0.72rem", color: "#9CA3AF" }}>esg-optimizer.fr — A STRATA Product</span>
              <span style={{ fontSize: "0.72rem", color: "#9CA3AF" }}>Page 2 / 3</span>
            </div>
          </div>

          {/* PAGE 3 — Recommandations & CTA */}
          <div
            className="pdf-page bg-white w-[794px] max-w-full"
            style={{ minHeight: "1123px", position: "relative", overflow: "hidden" }}
          >
            <div style={{
              position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
              pointerEvents: "none", zIndex: 1,
            }}>
              <span style={{
                fontSize: "5rem", fontWeight: 900, color: "rgba(26,61,34,0.04)",
                transform: "rotate(-35deg)", letterSpacing: "0.1em", textTransform: "uppercase",
                whiteSpace: "nowrap",
              }}>
                APERÇU GRATUIT
              </span>
            </div>

            <div style={{
              background: "#F7F2E8", borderBottom: "1px solid #E5E0D8",
              padding: "20px 48px", display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <div>
                <p style={{ fontWeight: 700, color: "#1A3D22", margin: "0 0 2px", fontSize: "0.9rem" }}>ESG Optimizer</p>
                <p style={{ color: "#6B7280", fontSize: "0.75rem", margin: 0 }}>Recommandations & prochaines étapes</p>
              </div>
            </div>

            <div style={{ padding: "36px 48px", position: "relative", zIndex: 2 }}>
              <h2 style={{
                fontFamily: "DM Serif Display, Georgia, serif",
                fontSize: "1.5rem", color: "#1A3D22", margin: "0 0 8px",
              }}>
                Recommandations prioritaires
              </h2>
              <p style={{ color: "#6B7280", fontSize: "0.85rem", margin: "0 0 24px", lineHeight: 1.5 }}>
                Basées sur l&apos;analyse de votre rapport et les exigences CSRD/ESRS.
              </p>

              {/* Recommandations verrouillées */}
              <div style={{ position: "relative", marginBottom: 32 }}>
                <div style={{ filter: "blur(6px)", opacity: 0.35 }}>
                  {[
                    { prio: 1, pillar: "E", color: "#DC2626", bg: "#FEE2E2", text: "Mettre en place un système de mesure des émissions GES scope 1, 2 et 3 conforme GHG Protocol." },
                    { prio: 2, pillar: "S", color: "#D97706", bg: "#FEF3C7", text: "Définir et publier une politique de diversité et inclusion avec des indicateurs mesurables." },
                    { prio: 3, pillar: "G", color: "#2563EB", bg: "#DBEAFE", text: "Renforcer les mécanismes de contrôle interne et créer un comité d'audit indépendant." },
                  ].map(({ prio, pillar, color, bg, text }) => (
                    <div key={prio} style={{
                      display: "flex", gap: 12, padding: "14px 16px",
                      background: "white", border: "1px solid #E5E7EB", borderRadius: 10, marginBottom: 10,
                    }}>
                      <span style={{
                        background: bg, color, fontSize: "0.7rem", fontWeight: 700,
                        padding: "3px 8px", borderRadius: 6, flexShrink: 0, height: "fit-content",
                      }}>
                        P{prio} · {pillar}
                      </span>
                      <p style={{ fontSize: "0.83rem", color: "#374151", margin: 0, lineHeight: 1.4 }}>{text}</p>
                    </div>
                  ))}
                </div>
                <div style={{
                  position: "absolute", inset: 0,
                  display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                  background: "rgba(255,255,255,0.8)", borderRadius: 12,
                }}>
                  <span style={{ fontSize: "2rem", marginBottom: 8 }}>🔒</span>
                  <p style={{ fontWeight: 700, color: "#1A3D22", fontSize: "0.95rem", margin: "0 0 4px", textAlign: "center" }}>
                    Recommandations complètes disponibles
                  </p>
                  <p style={{ color: "#6B7280", fontSize: "0.82rem", margin: "0 0 16px", textAlign: "center" }}>
                    Créez un compte gratuit pour débloquer l&apos;analyse complète
                  </p>
                  <div style={{
                    background: "#1A3D22", color: "#D4F0D8",
                    padding: "10px 24px", borderRadius: 10,
                    fontWeight: 700, fontSize: "0.88rem",
                  }}>
                    esg-optimizer.fr/sign-up
                  </div>
                </div>
              </div>

              {/* CTA box */}
              <div style={{
                background: "linear-gradient(135deg, #1A3D22 0%, #2A5C34 100%)",
                borderRadius: 16, padding: "32px 36px", textAlign: "center",
              }}>
                <h3 style={{
                  fontFamily: "DM Serif Display, Georgia, serif",
                  fontSize: "1.4rem", color: "white", margin: "0 0 10px",
                }}>
                  Obtenez l&apos;analyse complète
                </h3>
                <p style={{ color: "rgba(255,255,255,0.75)", fontSize: "0.85rem", margin: "0 0 20px", lineHeight: 1.5 }}>
                  Rapport PDF 8+ pages · Scores E/S/G détaillés · Couverture ESRS complète<br />
                  Recommandations priorisées · Badge LinkedIn · Delta Report N/N-1
                </p>
                <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
                  <div style={{
                    background: "#7FC686", color: "#1A3D22",
                    padding: "12px 28px", borderRadius: 10, fontWeight: 700, fontSize: "0.9rem",
                  }}>
                    Créer un compte gratuit →
                  </div>
                  <div style={{
                    border: "1.5px solid rgba(255,255,255,0.3)", color: "rgba(255,255,255,0.8)",
                    padding: "12px 20px", borderRadius: 10, fontWeight: 600, fontSize: "0.85rem",
                  }}>
                    esg-optimizer.fr
                  </div>
                </div>
              </div>
            </div>

            <div style={{
              position: "absolute", bottom: 0, left: 0, right: 0,
              borderTop: "1px solid #E5E0D8", padding: "12px 48px",
              display: "flex", justifyContent: "space-between", alignItems: "center",
              background: "white",
            }}>
              <span style={{ fontSize: "0.72rem", color: "#9CA3AF" }}>esg-optimizer.fr — A STRATA Product</span>
              <span style={{ fontSize: "0.72rem", color: "#9CA3AF" }}>Page 3 / 3</span>
            </div>
          </div>

        </div>
      </div>
    </>
  );
}
