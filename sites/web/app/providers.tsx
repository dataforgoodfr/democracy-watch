"use client";

import { ApiProvider } from "@democracy-watch/api";
import { rehydrateStores } from "@democracy-watch/state";
import { cssVariablesResolver, theme } from "@democracy-watch/theme";
import { type LinkProps, type Navigation, NavigationProvider } from "@democracy-watch/ui";
import { MantineProvider } from "@mantine/core";
import NextLink from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";
import { createAppRepository } from "../lib/api.ts";

const RouterLink = ({ href, ...props }: LinkProps) => <NextLink href={href} {...props} />;

/**
 * Branche le thème, les données (TanStack Query + API ou mock) et le routeur Next.js sur les
 * composants — qui, eux, ne connaissent pas Next. L'état du navigateur est lu après le premier rendu.
 */
export const Providers = ({ children }: { children: ReactNode }) => {
  const router = useRouter();
  const pathname = usePathname();
  const [repository] = useState(createAppRepository);

  useEffect(() => {
    void rehydrateStores();
  }, []);

  const navigation: Navigation = {
    Link: RouterLink,
    navigate: (href) => router.push(href, { scroll: false }),
    pathname,
  };
  return (
    <MantineProvider theme={theme} cssVariablesResolver={cssVariablesResolver}>
      <ApiProvider repository={repository}>
        <NavigationProvider value={navigation}>{children}</NavigationProvider>
      </ApiProvider>
    </MantineProvider>
  );
};
