import { describe, expect, it } from "vitest";
import {
  articleNumber,
  formatNumber,
  leadPrefixOf,
  textNumber,
  toGroup,
  toStage,
  toStatus,
  toTextType,
} from "./mapping.ts";

describe("conversion API → modèle du front", () => {
  it("statuts : sorts de l'Assemblée", () => {
    expect(toStatus("Adopté")).toBe("adopte");
    expect(toStatus("Rejeté")).toBe("rejete");
    expect(toStatus("Tombé")).toBe("tombe");
    expect(toStatus("Retiré")).toBe("retire");
    expect(toStatus("Non soutenu")).toBe("non-soutenu");
    expect(toStatus("Irrecevable art. 40")).toBe("irrecevable");
    expect(toStatus(null)).toBe("en-attente");
  });

  it("groupes : suffixes retirés, inconnus en non-inscrits", () => {
    expect(toGroup("LFI-NFP")).toBe("LFI");
    expect(toGroup("rn")).toBe("RN");
    expect(toGroup("XYZ")).toBe("NI");
    expect(toGroup(null)).toBe("NI");
  });

  it("numéros et étapes d'examen", () => {
    expect(formatNumber("CE31")).toBe("CE 31");
    expect(formatNumber("1203")).toBe("1203");
    expect(toStage("CE31", "CE")).toBe("commission-fond");
    expect(toStage("CD14", "CE")).toBe("commission-avis");
    expect(toStage("1203", "CE")).toBe("seance");
    expect(leadPrefixOf([{ numero: "CE1" }, { numero: "CE2" }, { numero: "CD3" }] as never)).toBe(
      "CE",
    );
  });

  it("types de texte et références", () => {
    expect(toTextType("Projet de loi ordinaire")).toBe("PJL");
    expect(toTextType("Projet de loi de finances")).toBe("PLF");
    expect(toTextType("Projet de loi de financement de la sécurité sociale")).toBe("PLFSS");
    expect(toTextType("Proposition de loi ordinaire")).toBe("PPL");
    expect(textNumber("PRJLANR5L17B2436")).toBe(2436);
    expect(articleNumber("Article 3")).toBe("3");
    expect(articleNumber("art. 1er")).toBe("1er");
  });
});
