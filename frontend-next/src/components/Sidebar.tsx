"use client";

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
} from "lucide-react";
import { LogoSidebar } from "@/components/Logo";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/resultats", label: "Résultats", icon: BarChart2 },
  { href: "/parametres", label: "Paramètres", icon: Settings },
  { href: "/plans", label: "Tarifs", icon: CreditCard },
  { href: "/info", label: "Mentions & Méthodo", icon: FileText },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="fixed left-0 top-0 h-full w-64 flex flex-col z-40"
      style={{ background: "#1A3D22" }}
    >
      {/* Logo */}
      <div className="border-b border-white/10">
        <Link href="/" aria-label="ESG Optimizer AI — Accueil">
          <LogoSidebar />
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
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

      {/* Footer sidebar : user + accueil */}
      <div className="px-3 pb-4 pt-2 border-t border-white/10 space-y-2">
        <Link
          href="/"
          className="flex items-center gap-3 px-4 py-2 rounded-lg text-[#D4F0D8]/70 hover:text-[#D4F0D8] hover:bg-white/10 transition-all text-sm"
        >
          <Home className="w-4 h-4" />
          Accueil public
        </Link>
        <div className="flex items-center gap-3 px-4 py-2">
          <UserButton
            appearance={{
              elements: {
                avatarBox: "w-8 h-8",
              },
            }}
            afterSignOutUrl="/"
          />
          <span className="text-[#D4F0D8]/60 text-xs">Mon compte</span>
        </div>
      </div>
    </aside>
  );
}
