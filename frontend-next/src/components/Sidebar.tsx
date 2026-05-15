"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";
import {
  LayoutDashboard,
  Upload,
  BarChart2,
  Settings,
  CreditCard,
  FileText,
  Home,
  Menu,
  X,
} from "lucide-react";
import { LogoSidebar } from "@/components/Logo";

const navItems = [
  { href: "/dashboard", label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/upload", label: "Analyser un rapport", icon: Upload },
  { href: "/resultats", label: "Résultats", icon: BarChart2 },
  { href: "/parametres", label: "Paramètres", icon: Settings },
  { href: "/plans", label: "Tarifs", icon: CreditCard },
  { href: "/info", label: "Mentions & Méthodo", icon: FileText },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Bouton menu (mobile uniquement) */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Ouvrir le menu"
        className="fixed top-3 left-3 z-50 md:hidden flex items-center justify-center w-10 h-10 rounded-lg bg-[#1A3D22] text-[#D4F0D8] shadow-md"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Voile sombre derrière la sidebar (mobile) */}
      {open && (
        <div
          onClick={() => setOpen(false)}
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed left-0 top-0 h-full w-64 flex flex-col z-50 transition-transform duration-200 ${
          open ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0`}
        style={{ background: "#1A3D22" }}
      >
        {/* Logo + fermeture mobile */}
        <div className="border-b border-white/10 flex items-center justify-between pr-2">
          <Link
            href="/"
            aria-label="ESG Optimizer, accueil"
            onClick={() => setOpen(false)}
          >
            <LogoSidebar />
          </Link>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Fermer le menu"
            className="md:hidden p-2 rounded-lg text-[#D4F0D8]/70 hover:text-[#D4F0D8] hover:bg-white/10"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                onClick={() => setOpen(false)}
                className={
                  isActive
                    ? "flex items-center gap-3 px-4 py-2.5 rounded-lg text-[#D4F0D8] bg-white/15 font-semibold text-sm"
                    : "flex items-center gap-3 px-4 py-2.5 rounded-lg text-[#D4F0D8]/70 hover:text-[#D4F0D8] hover:bg-white/10 transition-all duration-150 font-medium text-sm"
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Pied de sidebar : accueil public + compte */}
        <div className="px-3 pb-4 pt-2 border-t border-white/10 space-y-2">
          <Link
            href="/"
            onClick={() => setOpen(false)}
            className="flex items-center gap-3 px-4 py-2 rounded-lg text-[#D4F0D8]/70 hover:text-[#D4F0D8] hover:bg-white/10 transition-all text-sm"
          >
            <Home className="w-4 h-4" />
            Accueil public
          </Link>
          <div className="flex items-center gap-3 px-4 py-2">
            <UserButton
              appearance={{ elements: { avatarBox: "w-8 h-8" } }}
              afterSignOutUrl="/"
            />
            <span className="text-[#D4F0D8]/60 text-xs">Mon compte</span>
          </div>
        </div>
      </aside>
    </>
  );
}
