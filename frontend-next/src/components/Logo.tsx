import React from "react";

interface LogoIconProps {
  size?: number;
  className?: string;
}

/** Icone seule (jauge ESG) */
export function LogoIcon({ size = 32, className }: LogoIconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <rect width="64" height="64" rx="14" fill="#1A3D22" />
      {/* Arc track (dim) */}
      <path
        d="M12 38 A20 20 0 0 1 52 38"
        stroke="#D4F0D8"
        strokeOpacity="0.3"
        strokeWidth="5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Active arc */}
      <path
        d="M12 38 A20 20 0 0 1 43.3 19.3"
        stroke="#7FC686"
        strokeWidth="5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Needle */}
      <line
        x1="32"
        y1="38"
        x2="43.3"
        y2="19.3"
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      {/* Center dot */}
      <circle cx="32" cy="38" r="4" fill="#7FC686" />
      {/* Leaf left */}
      <ellipse
        cx="27"
        cy="46"
        rx="5"
        ry="3"
        fill="#7FC686"
        fillOpacity="0.55"
        transform="rotate(-25 27 46)"
      />
      {/* Leaf right */}
      <ellipse
        cx="37"
        cy="46"
        rx="5"
        ry="3"
        fill="#7FC686"
        fillOpacity="0.55"
        transform="rotate(25 37 46)"
      />
    </svg>
  );
}

interface LogoProps {
  variant?: "dark" | "light" | "white";
  size?: "sm" | "md" | "lg";
  showTagline?: boolean;
  className?: string;
}

/** Logo horizontal : icone + texte */
export function Logo({
  variant = "dark",
  size = "md",
  showTagline = false,
  className,
}: LogoProps) {
  const iconSize = size === "sm" ? 28 : size === "md" ? 36 : 48;

  const titleColor =
    variant === "dark"
      ? "text-white"
      : "text-[#1A3D22]";

  const aiColor =
    variant === "dark"
      ? "text-[#7FC686]"
      : "text-[#2A5C34]";

  const taglineColor =
    variant === "dark"
      ? "text-[#D4F0D8]/70"
      : "text-[#6B7280]";

  const titleSize =
    size === "sm"
      ? "text-base"
      : size === "md"
      ? "text-lg"
      : "text-2xl";

  const taglineSize = size === "sm" ? "text-[10px]" : "text-xs";

  return (
    <div className={`flex items-center gap-2.5 ${className ?? ""}`}>
      <LogoIcon size={iconSize} />
      <div className="flex flex-col leading-none">
        <div className="flex items-baseline gap-1">
          <span
            className={`font-bold tracking-tight ${titleSize} ${titleColor}`}
            style={{ fontFamily: "var(--font-sans)" }}
          >
            ESG Optimizer
          </span>
          <span className={`font-bold text-sm ${aiColor}`}>AI</span>
        </div>
        {showTagline && (
          <span className={`${taglineSize} ${taglineColor} mt-0.5 font-medium tracking-wide`}>
            Audit CSRD · ESRS
          </span>
        )}
      </div>
    </div>
  );
}

/** Logo compact pour la sidebar (icone + nom court) */
export function LogoSidebar() {
  return (
    <div className="flex items-center gap-2.5 px-4 py-3">
      <LogoIcon size={34} />
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
