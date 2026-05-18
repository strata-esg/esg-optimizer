"use client";

import Link from "next/link";
import { SignedIn, SignedOut } from "@clerk/nextjs";
import { Logo } from "@/components/Logo";

export function LandingNavbar() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#F7F2E8]/95 backdrop-blur-sm border-b border-[#E5E0D8]">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" aria-label="ESG Optimizer AI - Accueil">
            <Logo variant="light" size="md" showTagline={false} />
          </Link>
          <a
            href="https://www.strata-esg.fr"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center text-[10px] font-semibold tracking-widest uppercase text-[#1A3D22]/50 hover:text-[#1A3D22] border border-[#1A3D22]/20 hover:border-[#1A3D22]/50 rounded-full px-2.5 py-1 transition-all duration-150"
          >
            A STRATA product
          </a>
        </div>

        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-[#6B7280]">
          <Link href="/quick-check" className="hover:text-[#1A3D22] transition-colors font-semibold text-[#1A3D22]">Quick Check</Link>
          <a href="#comment" className="hover:text-[#1A3D22] transition-colors">Comment ca marche</a>
          <a href="#tarifs" className="hover:text-[#1A3D22] transition-colors">Tarifs</a>
          <Link href="/mentions" className="hover:text-[#1A3D22] transition-colors">Methodo</Link>
        </nav>

        <div className="flex items-center gap-3">
          <SignedOut>
            <Link href="/sign-in" className="text-sm font-medium text-[#1A3D22] hover:text-[#2A5C34]">
              Connexion
            </Link>
            <Link href="/sign-up" className="btn-primary text-sm">
              Essai gratuit
            </Link>
          </SignedOut>
          <SignedIn>
            <Link href="/dashboard" className="btn-primary text-sm">
              Tableau de bord
            </Link>
          </SignedIn>
        </div>
      </div>
    </header>
  );
}
