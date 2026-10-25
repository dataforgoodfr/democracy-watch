import { cssVariablesResolver, theme } from "@democracy-watch/theme";
import { type LinkProps, type Navigation, NavigationProvider } from "@democracy-watch/ui";
import { MantineProvider } from "@mantine/core";
import type { ReactNode } from "react";
import "./preview.css";

type PreviewProps = {
  children: ReactNode;
  /** Fond de page de l'application (gris) plutôt que blanc. */
  surface?: "page" | "blanc";
};

/** Dans un aperçu, les liens et la navigation ne quittent pas la page de documentation. */
const PreviewLink = ({ href, onClick, ...props }: LinkProps) => (
  <a
    href={href}
    {...props}
    onClick={(event) => {
      event.preventDefault();
      onClick?.(event);
    }}
  />
);

const previewNavigation: Navigation = { Link: PreviewLink, navigate: () => {}, pathname: "/" };

/**
 * Aperçu en direct d'un composant de @democracy-watch/ui, avec le thème de l'application.
 * Les variables Mantine et le schéma de couleurs sont limités au cadre `.dw-preview` :
 * l'aperçu ne modifie pas le style de la documentation.
 */
export const Preview = ({ children, surface = "blanc" }: PreviewProps) => (
  <div className="dw-preview not-prose" data-mantine-color-scheme="light" data-surface={surface}>
    <MantineProvider
      theme={theme}
      cssVariablesResolver={cssVariablesResolver}
      forceColorScheme="light"
      cssVariablesSelector=".dw-preview"
      getRootElement={() => undefined}
    >
      <NavigationProvider value={previewNavigation}>{children}</NavigationProvider>
    </MantineProvider>
  </div>
);
