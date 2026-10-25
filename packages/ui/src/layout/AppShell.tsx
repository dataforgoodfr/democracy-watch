"use client";

import { Logo } from "@democracy-watch/brand";
import type { ReactNode } from "react";
import { Link, useNavigation } from "../core/navigation.tsx";
import { GlobalSearch } from "./GlobalSearch.tsx";
import classes from "./layout.module.css";

export type NavItem = { href: string; label: string; count?: number };

type AppShellProps = {
  nav: NavItem[];
  /** Valeur initiale de la recherche globale. */
  query?: string;
  /** Zone du compte, à droite du header (utilisateur, déconnexion). */
  account?: ReactNode;
  children: ReactNode;
};

const isActive = (pathname: string, href: string) =>
  href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);

/** Cadre de l'application connectée : header de marque, recherche, navigation, contenu, pied de page. */
export const AppShell = ({ nav, query, account, children }: AppShellProps) => {
  const { pathname } = useNavigation();
  return (
    <div className={classes.shell}>
      <a className={classes.skipLink} href="#contenu">
        Aller au contenu
      </a>
      <header className={classes.header}>
        <div className={classes.headerTop}>
          <Link href="/" className={classes.logoLink} aria-label="Democracy Watch — accueil">
            <Logo size={34} />
          </Link>
          <GlobalSearch defaultValue={query} />
          {account ? <div className={classes.account}>{account}</div> : null}
        </div>
        <nav aria-label="Navigation principale" className={classes.nav}>
          <ul>
            {nav.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={classes.navLink}
                    aria-current={active ? "page" : undefined}
                  >
                    {item.label}
                    {item.count === undefined ? null : ` (${item.count})`}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </header>
      <main id="contenu" className={classes.main}>
        {children}
      </main>
      <footer className={classes.footer}>
        <p>
          Democracy Watch · un projet <a href="https://dataforgood.fr">Data for Good</a> · Données
          ouvertes de l'Assemblée nationale et de Légifrance
        </p>
      </footer>
    </div>
  );
};
