import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F7F2E8]">
      <div className="w-full max-w-md">
        {/* Logo / Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 bg-[#1A3D22] rounded-lg flex items-center justify-center">
              <span className="text-[#D4F0D8] font-bold text-lg">E</span>
            </div>
            <span
              className="text-2xl text-[#1A3D22]"
              style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
            >
              ESG Optimizer
            </span>
          </div>
          <p className="text-[#6B7280] text-sm">
            Connectez-vous pour accéder à vos analyses
          </p>
        </div>

        {/* Clerk SignIn — apparence personnalisée */}
        <SignIn
          appearance={{
            elements: {
              rootBox: "w-full",
              card: "shadow-md border border-[#E5E0D8] rounded-xl bg-white p-8",
              headerTitle: "font-serif text-[#1A3D22] text-xl",
              headerSubtitle: "text-[#6B7280] text-sm",
              formButtonPrimary:
                "bg-[#1A3D22] hover:bg-[#2A5C34] text-[#D4F0D8] font-medium rounded-lg transition-all",
              formFieldInput:
                "border-[#E5E0D8] rounded-lg focus:border-[#1A3D22] focus:ring-[#1A3D22]/10",
              footerActionLink: "text-[#1A3D22] hover:text-[#2A5C34] font-medium",
              identityPreviewEditButton: "text-[#1A3D22]",
              socialButtonsBlockButton:
                "border-[#E5E0D8] hover:bg-[#F7F2E8] transition-all rounded-lg",
            },
          }}
          forceRedirectUrl="/dashboard"
        />
      </div>
    </div>
  );
}
