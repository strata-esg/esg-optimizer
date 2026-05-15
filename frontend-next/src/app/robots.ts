import type { MetadataRoute } from "next";

const BASE_URL = "https://esg-optimizer.fr";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Espaces authentifiés et routes techniques : non indexés.
      disallow: [
        "/dashboard",
        "/upload",
        "/resultats",
        "/parametres",
        "/plans",
        "/info",
        "/api/",
      ],
    },
    sitemap: `${BASE_URL}/sitemap.xml`,
    host: BASE_URL,
  };
}
