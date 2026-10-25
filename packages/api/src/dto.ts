/** Réponses de l'API FastAPI (server/democracy_watch/api/schemas.py). Dates en ISO 8601. */

export type CommissionDto = {
  uid: string;
  slug: string;
  nom: string;
  nom_court?: string | null;
  role: "fond" | "avis" | string;
};

export type DossierDto = {
  uid: string;
  legislature: number;
  titre: string;
  titre_court?: string | null;
  procedure_libelle?: string | null;
  etat?: string | null;
  date_depot?: string | null;
  date_adoption?: string | null;
  url_an?: string | null;
  commissions: CommissionDto[];
  textes: { texte_ref: string; articles: number }[];
};

export type ArticleDto = {
  texte_ref: string;
  numero: string;
  libelle: string;
  ordre: number;
  contenu: string;
  source_url?: string | null;
};

export type AmendementDto = {
  uid: string;
  numero: string;
  legislature: number;
  chambre: string;
  auteur_libelle?: string | null;
  groupe_ref?: string | null;
  texte_ref?: string | null;
  article_vise?: string | null;
  dispositif?: string | null;
  expose_sommaire?: string | null;
  sort?: string | null;
  date_depot?: string | null;
  dossier_uid?: string | null;
  cosignataires: number;
};

export type SearchResponseDto = {
  mode: "grouped" | "federated";
  page: number;
  results?: Partial<
    Record<
      "amendements" | "dossiers" | "articles",
      { hits: Record<string, unknown>[]; total: number }
    >
  >;
};
