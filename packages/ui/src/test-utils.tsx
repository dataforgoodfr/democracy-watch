import { cssVariablesResolver, theme } from "@democracy-watch/theme";
import { MantineProvider } from "@mantine/core";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { type LinkProps, type Navigation, NavigationProvider } from "./core/navigation.tsx";

const AnchorLink = (props: LinkProps) => <a {...props} />;

/** Rendu de test : thème Mantine et navigation simulée (les liens et navigations sont observables). */
export const renderWithProviders = (
  ui: ReactElement,
  { pathname = "/" }: { pathname?: string } = {},
) => {
  const visited: string[] = [];
  const navigation: Navigation = {
    Link: AnchorLink,
    navigate: (href) => {
      visited.push(href);
    },
    pathname,
  };
  const result = render(
    <MantineProvider theme={theme} cssVariablesResolver={cssVariablesResolver}>
      <NavigationProvider value={navigation}>{ui}</NavigationProvider>
    </MantineProvider>,
  );
  return { ...result, visited };
};
