import type { NextConfig } from "next";

const config: NextConfig = {
  // Les packages du monorepo sont publiés en TypeScript source.
  transpilePackages: [
    "@democracy-watch/api",
    "@democracy-watch/brand",
    "@democracy-watch/data",
    "@democracy-watch/screens",
    "@democracy-watch/state",
    "@democracy-watch/theme",
    "@democracy-watch/ui",
  ],
  // Image autonome pour le déploiement Docker (Coolify).
  output: "standalone",
  outputFileTracingRoot: new URL("../..", import.meta.url).pathname,
  experimental: {
    optimizePackageImports: ["@mantine/core", "@mantine/hooks", "@tabler/icons-react"],
  },
};

export default config;
