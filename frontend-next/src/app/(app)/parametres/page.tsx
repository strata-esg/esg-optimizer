"use client";

import { useUser } from "@clerk/nextjs";
import { UserProfile } from "@clerk/nextjs";

export default function ParametresPage() {
  const { user, isLoaded } = useUser();

  const nom = user ? `${user.firstName ?? ""} ${user.lastName ?? ""}`.trim() : "—";
  const email = user?.primaryEmailAddress?.emailAddress ?? "—";
  const depuis = user?.createdAt
    ? new Date(user.createdAt).toLocaleDateString("fr-FR")
    : "—";

  return (
    <div className="w-full">
      <div className="mb-8">
        <h1
          className="text-4xl text-[#1A3D22] mb-2"
          style={{ fontFamily: "DM Serif Display, Georgia, serif" }}
        >
          Paramètres
        </h1>
        <p className="text-[#6B7280]">Gérez votre compte et vos préférences</p>
      </div>

      {/* Infos compte */}
      <div className="card mb-6">
        <h3 className="font-semibold text-[#1A3D22] mb-4">Mon compte</h3>
        {!isLoaded ? (
          <div className="h-16 flex items-center text-sm text-[#6B7280]">Chargement…</div>
        ) : (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-[#6B7280] mb-0.5">Nom</p>
              <p className="font-medium text-[#1C1C1C]">{nom}</p>
            </div>
            <div>
              <p className="text-[#6B7280] mb-0.5">Email</p>
              <p className="font-medium text-[#1C1C1C]">{email}</p>
            </div>
            <div>
              <p className="text-[#6B7280] mb-0.5">Membre depuis</p>
              <p className="font-medium text-[#1C1C1C]">{depuis}</p>
            </div>
          </div>
        )}
      </div>

      {/* Clerk UserProfile */}
      <div className="card overflow-hidden p-0 w-full">
        <UserProfile
          appearance={{
            elements: {
              rootBox: "w-full",
              card: "shadow-none border-0 rounded-none",
              navbar: "border-r border-[#E5E0D8]",
              navbarButton: "text-[#1C1C1C] hover:text-[#1A3D22] hover:bg-[#F7F2E8]",
              navbarButtonActive: "text-[#1A3D22] bg-[#D4F0D8]",
              formButtonPrimary: "bg-[#1A3D22] hover:bg-[#2A5C34] text-[#D4F0D8] rounded-lg",
              formFieldInput: "border-[#E5E0D8] rounded-lg focus:border-[#1A3D22]",
            },
          }}
        />
      </div>
    </div>
  );
}
