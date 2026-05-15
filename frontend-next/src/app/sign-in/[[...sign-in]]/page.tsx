import type { Metadata } from "next";
import { SignIn } from "@clerk/nextjs";
import { Logo } from "@/components/Logo";

export const metadata: Metadata = {
  title: "Connexion",
  description: "Connectez-vous à votre espace ESG Optimizer pour accéder à vos analyses CSRD / ESRS.",
  robots: { index: false, follow: true },
};

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F7F2E8] px-4 py-12">
      <div className="w-full max-w-md">
        {/* En-tête */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Logo variant="light" size="lg" />
          </div>
          <p className="text-[#6B7280] text-sm">
            Connectez-vous pour accéder à vos analyses
          </p>
        </div>

        {/* Connexion Clerk, habillée aux couleurs de la marque */}
        <SignIn
          appearance={{
            elements: {
              rootBox: "w-full",
              card: "shadow-md border border-[#E5E0D8] rounded-xl bg-white p-8",
              headerTitle: "font-serif text-[#1A3D22] text-xl",
              headerSubtitle: "text-[#6B7280] text-sm",
              formButtonPrimary:
                "bg-[#1A3D22] hover:bg-[#2A5C34] text-[#D4F0D8] font-medium rounded-lg transition-all normal-case",
              formFieldInput:
                "border-[#E5E0D8] rounded-lg focus:border-[#1A3D22] focus:ring-[#1A3D22]/10",
              footerActionLink: "text-[#1A3D22] hover:text-[#2A5C34] font-medium",
              identityPreviewEditButton: "text-[#1A3D22]",
              socialButtonsBlockButton:
                "border-[#E5E0D8] hover:bg-[#F7F2E8] transition-all rounded-lg",
            },
            variables: {
              colorPrimary: "#1A3D22",
              colorText: "#1C1C1C",
              borderRadius: "0.625rem",
            },
          }}
          forceRedirectUrl="/dashboard"
          signUpUrl="/sign-up"
        />
      </div>
    </div>
  );
}
