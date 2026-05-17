import type { Metadata } from "next";
import { SignUp } from "@clerk/nextjs";
import { Logo } from "@/components/Logo";

export const metadata: Metadata = {
  title: "Créer un compte",
  description: "Créez votre compte ESG Optimizer et lancez votre première analyse CSRD / ESRS gratuitement.",
  robots: { index: false, follow: true },
};

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F7F2E8] px-4 py-12">
      <div className="w-full max-w-md">
        {/* En-tête */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Logo variant="light" size="lg" />
          </div>
          <p className="text-[#6B7280] text-sm">
            Créez votre compte et lancez votre première analyse, offerte.
          </p>
        </div>

        {/* Inscription Clerk, habillée aux couleurs de la marque */}
        <SignUp
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
              socialButtonsBlockButton:
                "border-[#E5E0D8] hover:bg-[#F7F2E8] transition-all rounded-lg",
            },
            variables: {
              colorPrimary: "#1A3D22",
              colorText: "#1C1C1C",
              borderRadius: "0.625rem",
            },
          }}
          fallbackRedirectUrl="/dashboard"
          signInUrl="/sign-in"
        />
      </div>
    </div>
  );
}
