import { amendments, texts } from "@democracy-watch/data";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Badge } from "./core/Badge.tsx";
import { FilterPanel } from "./filters/FilterPanel.tsx";
import { Pills } from "./filters/Pills.tsx";
import { AppShell } from "./layout/AppShell.tsx";
import { AmendmentCard } from "./legislative/AmendmentCard.tsx";
import { AmendmentStatusBadge, CommissionBadge } from "./legislative/badges.tsx";
import { LegislativeTextCard } from "./legislative/LegislativeTextCard.tsx";
import { StageColumn } from "./legislative/StageColumn.tsx";
import { renderWithProviders } from "./test-utils.tsx";

const find = <T extends { id: string }>(items: T[], id: string) => {
  const item = items.find((candidate) => candidate.id === id);
  if (!item) throw new Error(`${id} absent des données fictives`);
  return item;
};

describe("Badge", () => {
  it("porte son ton en attribut, le texte reste lisible", () => {
    renderWithProviders(<Badge tone="succes">Adopté</Badge>);
    expect(screen.getByText("Adopté")).toHaveAttribute("data-tone", "succes");
  });

  it("affiche le statut d'un amendement en toutes lettres", () => {
    renderWithProviders(<AmendmentStatusBadge status="rejete" />);
    expect(screen.getByText("Rejeté")).toHaveAttribute("data-tone", "erreur");
  });

  it("indique l'échéance d'une commission (« J-1 »)", () => {
    renderWithProviders(<CommissionBadge label="Commission au fond" deadline={1} />);
    expect(screen.getByText("Commission au fond · J-1")).toBeInTheDocument();
  });
});

describe("AppShell", () => {
  const nav = [
    { href: "/", label: "Accueil" },
    { href: "/textes", label: "Mes textes de loi", count: 2 },
    { href: "/amendements", label: "Mes amendements suivis", count: 13 },
  ];

  it("signale l'onglet actif et propose un lien d'évitement", () => {
    renderWithProviders(<AppShell nav={nav}>contenu</AppShell>, { pathname: "/textes/ajouter" });
    expect(screen.getByRole("link", { name: "Mes textes de loi (2)" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Accueil" })).not.toHaveAttribute("aria-current");
    expect(screen.getByRole("link", { name: "Aller au contenu" })).toHaveAttribute(
      "href",
      "#contenu",
    );
  });

  it("envoie la recherche globale vers /recherche", async () => {
    const { visited } = renderWithProviders(<AppShell nav={nav}>contenu</AppShell>);
    await userEvent.type(screen.getByRole("textbox", { name: /rechercher/i }), "pesticides écoles");
    await userEvent.click(screen.getByRole("button", { name: "Rechercher" }));
    expect(visited).toEqual(["/recherche?q=pesticides+%C3%A9coles"]);
  });
});

describe("filtres", () => {
  it("transmet la case cochée et la réinitialisation", async () => {
    const onToggle = vi.fn();
    const onReset = vi.fn();
    renderWithProviders(
      <FilterPanel
        groups={[
          {
            id: "stage",
            label: "Étape du texte",
            options: [{ value: "depot", label: "Dépôt", checked: false }],
          },
        ]}
        onToggle={onToggle}
        onReset={onReset}
      />,
    );
    await userEvent.click(screen.getByRole("checkbox", { name: "Dépôt" }));
    await userEvent.click(screen.getByRole("button", { name: "Réinitialiser" }));
    expect(onToggle).toHaveBeenCalledWith("stage", "depot");
    expect(onReset).toHaveBeenCalledOnce();
  });

  it("expose l'état des pilules (aria-pressed)", () => {
    renderWithProviders(
      <Pills
        label="Type de texte"
        items={[
          { value: "PJL", label: "PJL" },
          { value: "PPL", label: "PPL" },
        ]}
        active={["PJL"]}
        onSelect={() => {}}
      />,
    );
    expect(screen.getByRole("button", { name: "PJL" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "PPL" })).toHaveAttribute("aria-pressed", "false");
  });
});

describe("composants législatifs", () => {
  it("carte de texte : titre lié, extrait surligné, métadonnées", () => {
    renderWithProviders(
      <LegislativeTextCard
        text={find(texts, "pjl-2436")}
        commissionName="Affaires économiques"
        href="/textes/pjl-2436"
        followed
        highlight={["pesticide"]}
      />,
    );
    expect(
      screen.getByRole("link", { name: "Projet de loi d'orientation pour la transition agricole" }),
    ).toHaveAttribute("href", "/textes/pjl-2436");
    expect(screen.getByText("pesticides").tagName).toBe("MARK");
    expect(
      screen.getByText(/PJL n° 2436 · déposé le 3 sept\. 2026 · 6 articles · 22 amendements/),
    ).toBeInTheDocument();
    expect(screen.getByText("À l'étude")).toBeInTheDocument();
  });

  it("carte d'amendement : similaires et redépôt probable sont signalés comme calculés", () => {
    const ce23 = find(amendments, "ce-23");
    const similar = amendments.filter((item) => item.similarTo?.amendmentId === "ce-23");
    const { container } = renderWithProviders(
      <AmendmentCard amendment={ce23} similar={similar} redepositNumber="CE 99" />,
    );
    expect(screen.getByText("≈ 2 similaires · DEM, HOR")).toBeInTheDocument();
    expect(screen.getByText(/redéposé en CE 99/)).toBeInTheDocument();
    expect(container.querySelector("[data-similar]")).not.toBeNull();
  });

  it("colonne vide : affiche l'état vide", () => {
    renderWithProviders(
      <StageColumn
        title="Déposés"
        subtitle="pas encore examinés"
        count={0}
        emptyText="Aucun amendement en attente."
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Aucun amendement en attente.");
  });
});
