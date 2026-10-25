/**
 * Conversion des réponses de l'API vers le modèle du front (`@democracy-watch/data`).
 * Les champs que l'API ne fournit pas encore reçoivent une valeur neutre, documentée ici.
 */
import type {
  Amendment,
  AmendmentStatus,
  Article,
  Commission,
  ExaminationStage,
  GroupCode,
  LegislativeText,
  TextStage,
  TextType,
} from "@democracy-watch/data";
import type { AmendementDto, ArticleDto, CommissionDto, DossierDto } from "./dto.ts";

const GROUPS: GroupCode[] = [
  "RN",
  "EPR",
  "LFI",
  "SOC",
  "DR",
  "ECO",
  "DEM",
  "HOR",
  "LIOT",
  "GDR",
  "UDR",
  "NI",
];

/** « LFI-NFP » → « LFI » ; groupe inconnu → « NI ». */
const isGroup = (value: string): value is GroupCode => (GROUPS as string[]).includes(value);

export const toGroup = (ref: string | null | undefined): GroupCode => {
  const code = (ref ?? "").toUpperCase().split(/[-\s]/)[0] ?? "";
  return isGroup(code) ? code : "NI";
};

/** Sort de l'Assemblée → statut. Sans sort : en attente. */
export const toStatus = (sort: string | null | undefined): AmendmentStatus => {
  const value = (sort ?? "").toLowerCase();
  if (!value) return "en-attente";
  if (value.startsWith("adopt")) return "adopte";
  if (value.startsWith("rejet")) return "rejete";
  if (value.startsWith("tomb")) return "tombe";
  if (value.startsWith("retir")) return "retire";
  if (value.includes("non soutenu")) return "non-soutenu";
  if (value.includes("irrecevable")) return "irrecevable";
  return "en-attente";
};

/** « CE31 » → « CE 31 » ; « 1203 » reste « 1203 ». */
export const formatNumber = (numero: string) => numero.replace(/^([A-Z]+)\s*(\d)/, "$1 $2");

/**
 * Étape d'examen déduite du numéro : préfixe de commission (CE, CD, CL…) → commission ;
 * numéro seul → séance. La distinction fond / avis vient des commissions du dossier.
 */
export const toStage = (numero: string, leadPrefix: string | null): ExaminationStage => {
  const prefix = numero.match(/^([A-Z]+)/)?.[1];
  if (!prefix) return "seance";
  return leadPrefix && prefix !== leadPrefix ? "commission-avis" : "commission-fond";
};

const TEXT_STAGES: Record<string, TextStage> = {
  en_cours: "commission",
  adopte: "adopte",
  promulgue: "adopte",
};

const STAGE_LABELS: Record<TextStage, string> = {
  depot: "Dépôt",
  commission: "En cours d'examen",
  seance: "Séance publique",
  adopte: "Adopté",
};

export const toTextType = (procedure: string | null | undefined): TextType => {
  const value = (procedure ?? "").toLowerCase();
  if (value.includes("financement de la sécurité sociale")) return "PLFSS";
  if (value.includes("finances")) return "PLF";
  if (value.startsWith("projet")) return "PJL";
  return "PPL";
};

const dateOnly = (iso: string | null | undefined) => (iso ? iso.slice(0, 10) : "");

/** Numéro du texte, lu dans sa référence (« PRJLANR5L17B2436 » → 2436). */
export const textNumber = (texteRef: string | undefined) =>
  Number(texteRef?.match(/B(\d+)/)?.[1] ?? 0);

export const toCommission = (dto: CommissionDto): Commission => ({
  id: dto.slug,
  name: dto.nom_court ?? dto.nom,
});

export const toText = (dto: DossierDto): LegislativeText => {
  const stage = TEXT_STAGES[dto.etat ?? ""] ?? "depot";
  const lead = dto.commissions.find((commission) => commission.role === "fond");
  const texte = dto.textes[0];
  return {
    id: dto.uid,
    type: toTextType(dto.procedure_libelle),
    number: textNumber(texte?.texte_ref),
    title: dto.titre,
    shortTitle: dto.titre_court ?? dto.titre,
    depositedAt: dateOnly(dto.date_depot),
    stage,
    stageLabel: STAGE_LABELS[stage],
    // Non fournis par l'API pour l'instant.
    stageDetail: "",
    leadCommissionId: lead?.slug ?? "",
    opinionCommissionIds: dto.commissions.filter((c) => c.role === "avis").map((c) => c.slug),
    carriedBy: "",
    articleCount: texte ? texte.articles : null,
    amendmentCount: 0,
    nextDeadline: null,
    theme: null,
    excerpt: null,
  };
};

export const toArticle = (dto: ArticleDto, textId: string): Article => ({
  id: `${textId}-art-${dto.numero}`,
  textId,
  number: dto.numero,
  title: dto.libelle,
  // Résumé en langage clair pas encore produit : début du contenu officiel.
  summary: dto.contenu.length > 180 ? `${dto.contenu.slice(0, 177)}…` : dto.contenu,
});

/** « Article 3 » / « art. 3 » → « 3 ». */
export const articleNumber = (articleVise: string | null | undefined) =>
  (articleVise ?? "").replace(/^\s*(article|art\.?)\s*/i, "").trim();

export const toAmendment = (
  dto: AmendementDto,
  textId: string,
  leadPrefix: string | null,
): Amendment => ({
  id: dto.uid,
  number: formatNumber(dto.numero),
  textId,
  articleId: `${textId}-art-${articleNumber(dto.article_vise)}`,
  alinea: null,
  author: { name: dto.auteur_libelle ?? "Auteur inconnu", group: toGroup(dto.groupe_ref) },
  cosignatories: dto.cosignataires,
  // Résumé en langage clair pas encore produit : début du dispositif officiel.
  summary: (dto.dispositif ?? dto.expose_sommaire ?? "").replace(/<[^>]+>/g, "").slice(0, 200),
  status: toStatus(dto.sort),
  stage: toStage(dto.numero, leadPrefix),
  commissionId: null,
  depositedAt: dateOnly(dto.date_depot),
  parentId: null,
  similarTo: null,
  redepositedAs: null,
});

/** Préfixe des amendements de la commission saisie au fond, déduit des numéros (le plus fréquent). */
export const leadPrefixOf = (amendements: AmendementDto[]) => {
  const counts = new Map<string, number>();
  for (const { numero } of amendements) {
    const prefix = numero.match(/^([A-Z]+)/)?.[1];
    if (prefix) counts.set(prefix, (counts.get(prefix) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;
};
