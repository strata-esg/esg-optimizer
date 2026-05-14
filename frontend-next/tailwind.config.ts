import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand ESG Optimizer
        forest: {
          DEFAULT: "#1A3D22",
          mid: "#2A5C34",
          600: "#3A7D3C",
        },
        leaf: "#7FC686",
        mint: "#D4F0D8",
        parchment: "#F5F2EC",
        cream: "#F7F2E8",
        amber: {
          DEFAULT: "#D97706",
          light: "#FEF3C7",
        },
        esg: {
          alert: "#DC2626",
          alertLight: "#FEE2E2",
          border: "#E5E0D8",
          muted: "#6B7280",
          text: "#1C1C1C",
        },
      },
      fontFamily: {
        serif: ["DM Serif Display", "Georgia", "serif"],
        sans: ["DM Sans", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        sm: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
        md: "0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.04)",
        card: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
      },
      borderRadius: {
        card: "12px",
      },
    },
  },
  plugins: [],
};
export default config;
