import React from "react";

type Tone = "dark" | "light" | "white";

interface LogoIconProps {
  size?: number;
  className?: string;
  /** "dark" = posé sur un fond sombre (sidebar), sinon fond clair. */
  variant?: Tone;
}

/**
 * Icone de marque : jauge ESG (speedometer).
 * Reprend le logomark utilise historiquement sur l'application.
 */
export function LogoIcon({ size = 32, className, variant = "light" }: LogoIconProps) {
  const onDark = variant === "dark";

  const trackColor = onDark ? "rgba(212,240,216,0.3)" : "#D4F0D8";
  const activeColor = onDark ? "#7FC686" : "#1A3D22";
  const hubColor = onDark ? "#D4F0D8" : "#1A3D22";
  const needleColor = onDark ? "#D4F0D8" : "#1A3D22";

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      {/* Arc de fond (jauge a 270 degres) */}
      <path
        d="M 6,24 A 14,14 0 1,1 34,24"
        stroke={trackColor}
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Arc actif */}
      <path
        d="M 6,24 A 14,14 0 0,1 28,9"
        stroke={activeColor}
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Moyeu central */}
      <circle cx="20" cy="22" r="2.5" fill={hubColor} />
      {/* Aiguille */}
      <line
        x1="20"
        y1="22"
        x2="30"
        y2="10"
        stroke={needleColor}
        strokeWidth="2"
        strokeLinecap="round"
      />
      {/* Pointe de l'aiguille */}
      <circle cx="30" cy="10" r="2" fill="#7FC686" />
    </svg>
  );
}

interface LogoProps {
  variant?: Tone;
  size?: "sm" | "md" | "lg";
  showTagline?: boolean;
  className?: string;
}

/** Logo horizontal : icone + nom de marque. */
export function Logo({
  variant = "light",
  size = "md",
  showTagline = false,
  className,
}: LogoProps) {
  const iconSize = size === "sm" ? 28 : size === "md" ? 34 : 46;
  const onDark = variant === "dark";

  const titleColor = onDark ? "text-white" : "text-[#1A3D22]";
  const taglineColor = onDark ? "text-[#D4F0D8]/70" : "text-[#6B7280]";
  const titleSize =
    size === "sm" ? "text-base" : size === "md" ? "text-lg" : "text-2xl";
  const taglineSize = size === "sm" ? "text-[10px]" : "text-xs";

  return (
    <div className={`flex items-center gap-2.5 ${className ?? ""}`}>
      <LogoIcon size={iconSize} variant={variant} />
      <div className="flex flex-col leading-none">
        <span
          className={`font-bold tracking-tight ${titleSize} ${titleColor}`}
          style={{ fontFamily: "var(--font-sans)" }}
        >
          ESG Optimizer
        </span>
        {showTagline && (
          <span className={`${taglineSize} ${taglineColor} mt-0.5 font-medium tracking-wide`}>
            Audit CSRD · ESRS
          </span>
        )}
      </div>
    </div>
  );
}

/** Logo compact pour la sidebar (fond sombre). */
export function LogoSidebar() {
  return (
    <div className="flex items-center gap-2.5 px-4 py-3">
      <LogoIcon size={34} variant="dark" />
      <div className="flex flex-col leading-none">
        <span className="font-bold text-white text-[15px] tracking-tight">
          ESG Optimizer
        </span>
        <span className="text-[10px] text-[#7FC686] font-semibold tracking-widest uppercase mt-0.5">
          Audit CSRD
        </span>
      </div>
    </div>
  );
}
