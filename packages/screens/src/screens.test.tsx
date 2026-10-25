import { useFollowStore, useSessionStore } from "@democracy-watch/state";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import {
  AddTextsScreen,
  AppLayout,
  ArticleScreen,
  FollowedAmendmentsScreen,
  HomeScreen,
  LoginScreen,
  MyTextsScreen,
  SearchScreen,
  TextScreen,
} from "./index.ts";
import { renderScreen } from "./test-utils.tsx";

describe("Recherche élargie", () => {
  it("reproduit la maquette « pesticides écoles »", async () => {
    await renderScreen(<SearchScreen params={{ q: "pesticides écoles" }} />, {
      pathname: "/recherche",
    });
    expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent(
      "résultats pour « pesticides écoles »",
    );
    expect(screen.getByText("Commission au fond · J-1")).toBeInTheDocument();
  });

  it("met à jour l'URL quand on coche un filtre", async () => {
    const { visited } = await renderScreen(<SearchScreen params={{ q: "pesticides" }} />);
    await userEvent.click(await screen.findByRole("checkbox", { name: "En commission" }));
    expect(visited).toEqual(["/recherche?q=pesticides&etape=commission"]);
  });

  it("restreint aux textes suivis (état du navigateur)", async () => {
    await renderScreen(<SearchScreen params={{ q: "pesticides", suivis: "1" }} />, {
      followed: ["ppl-2511"],
    });
    expect(await screen.findByRole("link", { name: /protéger les enfants/ })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /transition agricole/ })).not.toBeInTheDocument();
  });

  it("affiche un état vide sans résultat", async () => {
    await renderScreen(<SearchScreen params={{ q: "zzzz" }} />);
    expect(await screen.findByText("Aucun résultat")).toBeInTheDocument();
  });
});

describe("Sélectionner puis suivre des textes", () => {
  it("enregistre la sélection et ses préférences, puis mène à « Mes textes de loi »", async () => {
    const { visited } = await renderScreen(<AddTextsScreen />);
    const button = screen.getByRole("button", { name: /Ajouter 0 texte à mon étude/ });
    expect(button).toBeDisabled();
    await userEvent.click(
      await screen.findByRole("checkbox", {
        name: /Sélectionner Proposition de loi visant à protéger/,
      }),
    );
    await userEvent.click(
      screen.getByRole("checkbox", { name: "un amendement similaire apparaît ailleurs" }),
    );
    const panel = screen.getByRole("complementary", { name: "Ma sélection" });
    expect(within(panel).getByText("PPL exposition aux pesticides")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Ajouter 1 texte à mon étude/ }));
    expect(useFollowStore.getState().texts).toMatchObject([
      { id: "ppl-2511", articles: "tous", alerts: ["amendements", "etape", "similaires"] },
    ]);
    expect(visited).toEqual(["/textes"]);
  });

  it("un texte déjà suivi n'est pas sélectionnable", async () => {
    await renderScreen(<AddTextsScreen />, { followed: ["pjl-2436"] });
    expect(await screen.findByLabelText("Déjà à l'étude")).toBeInTheDocument();
  });

  it("« Mes textes de loi » liste les textes suivis et permet d'arrêter le suivi", async () => {
    await renderScreen(<MyTextsScreen />, { followed: ["pjl-2436", "ppl-2511"] });
    expect(await screen.findByRole("link", { name: /transition agricole/ })).toBeInTheDocument();
    await userEvent.click(
      screen.getAllByRole("button", { name: "Ne plus suivre" })[0] as HTMLElement,
    );
    expect(useFollowStore.getState().texts.map((text) => text.id)).toEqual(["ppl-2511"]);
  });

  it("sans texte suivi : invitation à en ajouter", async () => {
    await renderScreen(<MyTextsScreen />);
    expect(
      screen.getByRole("link", { name: "Ajoutez vos premiers textes à l'étude" }),
    ).toHaveAttribute("href", "/textes/ajouter");
  });

  it("fiche texte : sommaire et bouton « Suivre ce texte »", async () => {
    await renderScreen(<TextScreen textId="pjl-2436" />);
    expect(
      await screen.findByRole("link", { name: "Art. 3 · Produits phytosanitaires" }),
    ).toHaveAttribute("href", "/textes/pjl-2436/articles/3");
    await userEvent.click(screen.getByRole("button", { name: "Suivre ce texte" }));
    expect(useFollowStore.getState().texts.map((text) => text.id)).toEqual(["pjl-2436"]);
  });
});

describe("Article — avancement (kanban)", () => {
  it("répartit les 8 amendements de l'article 3 par étape", async () => {
    await renderScreen(<ArticleScreen textId="pjl-2436" articleNumber="3" />, {
      followed: ["pjl-2436"],
    });
    expect(
      await screen.findByRole("region", { name: "Commission au fond — 6" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Commission pour avis — 2" })).toBeInTheDocument();
    expect(screen.getByText(/redéposé en CE 23/)).toBeInTheDocument();
    expect(screen.getByText("Suivi")).toBeInTheDocument();
  });

  it("regroupe les similaires quand le filtre est actif", async () => {
    await renderScreen(
      <ArticleScreen textId="pjl-2436" articleNumber="3" params={{ similaires: "1" }} />,
    );
    expect(await screen.findByText("CE 23")).toBeInTheDocument();
    expect(screen.queryByText("CE 61")).not.toBeInTheDocument();
  });

  it("article inconnu : page introuvable", async () => {
    await renderScreen(<ArticleScreen textId="pjl-2436" articleNumber="42" />);
    expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent("Page introuvable");
  });
});

describe("Autres écrans", () => {
  it("Mes amendements suivis : amendements des textes suivis, filtre par statut", async () => {
    await renderScreen(<FollowedAmendmentsScreen params={{ statut: "adopte" }} />, {
      followed: ["pjl-2436"],
    });
    expect(await screen.findByRole("heading", { level: 1 })).toHaveTextContent(
      "Mes amendements suivis (13)",
    );
    expect(screen.queryByText("Rejeté", { selector: "[data-tone]" })).not.toBeInTheDocument();
  });

  it("Accueil : échéance J-1 des textes suivis, invitation sinon", async () => {
    await renderScreen(<HomeScreen />, { followed: ["pjl-2436"] });
    expect(await screen.findByText("J-1")).toBeInTheDocument();
  });

  it("Connexion : session « rester connecté » puis retour à la page demandée", async () => {
    const { visited } = await renderScreen(<LoginScreen params={{ suite: "/textes" }} />, {
      signedIn: false,
    });
    await userEvent.type(screen.getByLabelText(/Adresse e-mail/), "asso@example.org");
    await userEvent.type(screen.getByLabelText(/Mot de passe/, { selector: "input" }), "secret");
    await userEvent.click(screen.getByRole("checkbox", { name: "Rester connecté" }));
    await userEvent.click(screen.getByRole("button", { name: "Se connecter" }));
    expect(useSessionStore.getState().session).toMatchObject({
      email: "asso@example.org",
      remember: true,
    });
    expect(localStorage.getItem("dw:session")).toContain("asso@example.org");
    expect(visited).toEqual(["/textes"]);
  });

  it("Connexion : refuse une redirection externe", async () => {
    const { visited } = await renderScreen(<LoginScreen params={{ suite: "//exemple.com" }} />, {
      signedIn: false,
    });
    await userEvent.type(screen.getByLabelText(/Adresse e-mail/), "asso@example.org");
    await userEvent.type(screen.getByLabelText(/Mot de passe/, { selector: "input" }), "secret");
    await userEvent.click(screen.getByRole("button", { name: "Se connecter" }));
    expect(visited).toEqual(["/"]);
  });

  it("Cadre : sans session, renvoie vers la connexion", async () => {
    const { visited } = await renderScreen(<AppLayout>contenu</AppLayout>, {
      pathname: "/textes",
      signedIn: false,
    });
    expect(visited).toEqual(["/connexion?suite=%2Ftextes"]);
    expect(screen.queryByText("contenu")).not.toBeInTheDocument();
  });

  it("Cadre : compteurs issus des textes suivis, déconnexion", async () => {
    const { visited } = await renderScreen(<AppLayout>contenu</AppLayout>, {
      followed: ["pjl-2436"],
    });
    expect(screen.getByRole("link", { name: "Mes textes de loi (1)" })).toBeInTheDocument();
    expect(
      await screen.findByRole("link", { name: "Mes amendements suivis (13)" }),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Se déconnecter" }));
    expect(useSessionStore.getState().session).toBeNull();
    expect(visited).toContain("/connexion");
  });
});
