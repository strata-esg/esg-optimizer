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
  Shield,
} from "lucide-react";
import { LogoSidebar } from "@/components/Logo";

const navItems = [
  { href: "/dashboard", label: "Tableau de bord", icon: LayoutDashboard },
  { href: "/upload", label: "Analyser un rapport", icon: Upload },
  { href: "/resultats", label: "Resultats", icon: BarChart2 },
  { href: "/parametres", label: "Parametres", icon: Settings },
  { href: "/plans", label: "Tarifs", icon: CreditCard },
  { href: "/info", label: "Mentions & Methodo", icon: FileText },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Ouvrir le menu"
        className="fixed top-3 left-3 z-50 md:hidden flex items-center justify-center w-10 h-10 rounded-lg bg-[#1A3D22] text-[#D4F0D8] shadow-md"
      >
        <Menu className="w-5 h-5" />
      </button>

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

        <div className="px-3 pb-4 pt-2 border-t border-white/10 space-y-1">
          <Link
            href="/admin"
            onClick={() => setOpen(false)}
            className="flex items-center gap-3 px-4 py-2 rounded-lg text-[#7FC686]/80 hover:text-[#7FC686] hover:bg-white/10 transition-all text-sm"
            title="Administration"
          >
            <Shield className="w-4 h-4" />
            Admin
          </Link>
          <Link
            href="/"
            onClick={() => setOpen(false)}
            className="flex items-center gap-3 px-4 py-2 rounded-lg text-[#D4F0D8]/70 hover:text-[#D4F0D8] hover:bg-white/10 transition-all text-sm"
          >
            <Home className="w-4 h-4" />
            Accueil public
          </Link>
          <div className="flex items-center gap-3 px-4 py-2 rounded-lg">
            <div className="flex-shrink-0 flex items-center">
              <UserButton
                appearance={{ elements: { avatarBox: "w-7 h-7" } }}
                afterSignOutUrl="/"
              />
            </div>
            <span className="text-[#D4F0D8]/70 text-sm font-medium leading-none">Mon compte</span>
          </div>
        </div>
      </aside>
    </>
  );
}
