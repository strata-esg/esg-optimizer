"use client";

import { UserProfile } from "@clerk/nextjs";

export default function ParametresPage() {
  return (
    <div className="w-full max-w-4xl">
      <div className="mb-8">
        <h1
          className="text-4xl text-[#1A3D22] mb-2"
          style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
        >
          Paramètres
        </h1>
        <p className="text-[#6B7280]">
          Gérez votre compte, votre sécurité et vos préférences.
        </p>
      </div>

      {/* Profil Clerk : informations, sécurité, sessions. Le conteneur force
          le composant à rester fluide pour éviter tout débordement. */}
      <div className="rounded-xl border border-[#E5E0D8] bg-white shadow-sm overflow-hidden">
        <UserProfile
          routing="hash"
          appearance={{
            elements: {
              rootBox: "w-full",
              cardBox: "w-full max-w-full shadow-none border-0 rounded-none",
              card: "w-full max-w-full shadow-none border-0 rounded-none",
              navbar: "border-r border-[#E5E0D8] bg-[#F7F2E8]",
              navbarButton:
                "text-[#1C1C1C] hover:text-[#1A3D22] hover:bg-white transition-colors",
              navbarButtonActive: "text-[#1A3D22] bg-white font-semibold",
              scrollBox: "w-full",
              pageScrollBox: "w-full",
              header: "text-[#1A3D22]",
              formButtonPrimary:
                "bg-[#1A3D22] hover:bg-[#2A5C34] text-[#D4F0D8] rounded-lg normal-case",
              formFieldInput:
                "border-[#E5E0D8] rounded-lg focus:border-[#1A3D22] focus:ring-[#1A3D22]/10",
              profileSectionPrimaryButton: "text-[#1A3D22]",
              badge: "bg-[#D4F0D8] text-[#1A3D22]",
              footer: "hidden",
            },
            variables: {
              colorPrimary: "#1A3D22",
              colorText: "#1C1C1C",
              colorTextSecondary: "#6B7280",
              borderRadius: "0.625rem",
            },
          }}
        />
      </div>
    </div>
  );
}
