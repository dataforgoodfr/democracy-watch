"use client";

import {
  type AnchorHTMLAttributes,
  type ComponentType,
  createContext,
  type ReactNode,
  useContext,
} from "react";

export type LinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & { href: string };

/**
 * Adaptateur de routage. Les composants et écrans ne connaissent pas Next.js :
 * le site fournit son composant de lien et sa fonction de navigation.
 */
export type Navigation = {
  Link: ComponentType<LinkProps>;
  navigate: (href: string) => void;
  pathname: string;
};

const defaultNavigation: Navigation = {
  Link: (props) => <a {...props} />,
  navigate: (href) => window.location.assign(href),
  pathname: "/",
};

const NavigationContext = createContext<Navigation>(defaultNavigation);

export const NavigationProvider = ({
  value,
  children,
}: {
  value: Navigation;
  children: ReactNode;
}) => <NavigationContext.Provider value={value}>{children}</NavigationContext.Provider>;

export const useNavigation = () => useContext(NavigationContext);

/** Lien interne, rendu par le routeur du site. */
export const Link = (props: LinkProps) => {
  const { Link: RouterLink } = useNavigation();
  return <RouterLink {...props} />;
};
