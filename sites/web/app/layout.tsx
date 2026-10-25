import "@mantine/core/styles.css";
import "@democracy-watch/theme/styles.css";
import { ColorSchemeScript, mantineHtmlProps } from "@mantine/core";
import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Providers } from "./providers.tsx";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.SITE_URL ?? "http://localhost:3000"),
  title: { default: "Democracy Watch", template: "%s · Democracy Watch" },
  description: "Veille législative pour les associations, ONG et équipes de plaidoyer.",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon.svg", type: "image/svg+xml" },
    ],
    apple: "/apple-touch-icon.png",
  },
  manifest: "/site.webmanifest",
  openGraph: { images: "/og-image.png", siteName: "Democracy Watch", locale: "fr_FR" },
};

export const viewport: Viewport = { themeColor: "#17322E" };

const RootLayout = ({ children }: { children: ReactNode }) => (
  <html lang="fr" {...mantineHtmlProps}>
    <head>
      <ColorSchemeScript forceColorScheme="light" />
    </head>
    <body>
      <Providers>{children}</Providers>
    </body>
  </html>
);

export default RootLayout;
