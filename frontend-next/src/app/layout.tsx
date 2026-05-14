import type { Metadata, Viewport } from "next";
import { Suspense } from "react";
import { ClerkProvider } from "@clerk/nextjs";
import PostHogProvider from "@/components/PostHogProvider";
import "./globals.css";

export const viewport: Viewport = {
  themeColor: "#1A3D22",
};

export const metadata: Metadata = {
  title: {
    default: "ESG Optimizer AI - Audit CSRD/ESRS en 3 minutes",
    template: "%s | ESG Optimizer AI",
  },
  description:
    "Analysez vos rapports de durabilite en 3 minutes grace a l'IA. Conformite CSRD/ESRS, scoring E/S/G, benchmark sectoriel.",
  keywords: ["ESG", "CSRD", "ESRS", "rapport durabilite", "conformite", "analyse IA", "audit ESG", "PME"],
  authors: [{ name: "ESG Optimizer AI", url: "https://esg-optimizer.fr" }],
  creator: "ESG Optimizer AI",
  publisher: "ESG Optimizer AI",
  metadataBase: new URL("https://esg-optimizer.fr"),

  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
    other: [
      { rel: "mask-icon", url: "/favicon.svg", color: "#1A3D22" },
    ],
  },

  manifest: "/site.webmanifest",

  openGraph: {
    title: "ESG Optimizer AI - Audit CSRD/ESRS en 3 minutes",
    description: "Analysez votre conformite ESG en 3 minutes grace a l'IA. Scoring ESRS, rapport PDF.",
    locale: "fr_FR",
    type: "website",
    url: "https://esg-optimizer.fr",
    siteName: "ESG Optimizer AI",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "ESG Optimizer AI - Audit CSRD/ESRS automatise",
      },
    ],
  },

  twitter: {
    card: "summary_large_image",
    title: "ESG Optimizer AI - Audit CSRD/ESRS en 3 minutes",
    description: "Analysez votre conformite ESG en 3 minutes grace a l'IA.",
    images: ["/og-image.png"],
  },

  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="fr">
        <body>
          <Suspense>
            <PostHogProvider>
              {children}
            </PostHogProvider>
          </Suspense>
        </body>
      </html>
    </ClerkProvider>
  );
}
