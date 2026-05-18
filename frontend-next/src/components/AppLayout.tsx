import Sidebar from "./Sidebar";
import OnboardingModal from "./OnboardingModal";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#F7F2E8]">
      <Sidebar />
      {/* Contenu principal : decale de la largeur de la sidebar sur desktop,
          pleine largeur sur mobile (avec marge haute pour le bouton menu). */}
      <main className="md:ml-64 min-h-screen px-4 pt-16 pb-10 md:px-10 md:py-8">
        {children}
      </main>
      <OnboardingModal />
    </div>
  );
}
