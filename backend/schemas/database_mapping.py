import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Double,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, OID, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ActionDescriptions(Base):
    __tablename__ = "action_descriptions"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="action_descriptions_pkey"),
        Index("action_descriptions_texte_key", "texte", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    texte: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    actions_lobby: Mapped[list[ActionsLobby]] = relationship(
        "ActionsLobby", back_populates="description"
    )


class CandidatsMandatsLocaux(Base):
    __tablename__ = "candidats_mandats_locaux"
    __table_args__ = (PrimaryKeyConstraint("id", name="candidats_mandats_locaux_pkey"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    scrutin: Mapped[str] = mapped_column(Text, nullable=False)
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    prenom: Mapped[str] = mapped_column(Text, nullable=False)
    mandats: Mapped[object] = mapped_column(JSONB, nullable=False)
    confiance: Mapped[str] = mapped_column(Text, nullable=False)
    source_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class CibleTypes(Base):
    __tablename__ = "cible_types"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="cible_types_pkey"),
        Index("cible_types_label_key", "label", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    actions_lobby: Mapped[list[ActionsLobby]] = relationship(
        "ActionsLobby", back_populates="cible_type"
    )


class Circonscriptions(Base):
    __tablename__ = "circonscriptions"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="circonscriptions_pkey"),
        Index("circonscriptions_departement_idx", "departement"),
        Index(
            "circonscriptions_departement_numero_type_key",
            "departement",
            "numero",
            "type",
            unique=True,
        ),
        Index("circonscriptions_type_idx", "type"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    departement: Mapped[str] = mapped_column(Text, nullable=False)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    type: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'legislative'::text")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    population: Mapped[int | None] = mapped_column(Integer)

    candidatures_listes: Mapped[list[CandidaturesListes]] = relationship(
        "CandidaturesListes", back_populates="circonscription"
    )
    parlementaires: Mapped[list[Parlementaires]] = relationship(
        "Parlementaires", back_populates="circonscription"
    )
    resultats_listes: Mapped[list[ResultatsListes]] = relationship(
        "ResultatsListes", back_populates="circonscription"
    )
    resultats_tours: Mapped[list[ResultatsTours]] = relationship(
        "ResultatsTours", back_populates="circonscription"
    )
    mandats_parlementaires: Mapped[list[MandatsParlementaires]] = relationship(
        "MandatsParlementaires", back_populates="circonscription"
    )


class Commissions(Base):
    __tablename__ = "commissions"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="commissions_pkey"),
        Index("commissions_actif_idx", "actif"),
        Index("commissions_chambre_idx", "chambre"),
        Index("commissions_organe_ref_idx", "organe_ref"),
        Index("commissions_slug_key", "slug", unique=True),
        Index("commissions_type_idx", "type"),
        Index("commissions_uid_key", "uid", unique=True),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    uid: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    chambre: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    date_debut: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    organe_ref: Mapped[str | None] = mapped_column(Text)
    nom_court: Mapped[str | None] = mapped_column(Text)
    date_fin: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))

    reunions: Mapped[list[Reunions]] = relationship("Reunions", back_populates="commission")
    dossier_commissions: Mapped[list[DossierCommissions]] = relationship(
        "DossierCommissions", back_populates="commission"
    )
    mandats: Mapped[list[Mandats]] = relationship("Mandats", back_populates="commission")


class EvenementsInstitutionnels(Base):
    __tablename__ = "evenements_institutionnels"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="evenements_institutionnels_pkey"),
        Index("evenements_institutionnels_date_debut_idx", "date_debut"),
        Index("evenements_institutionnels_important_idx", "important"),
        Index("evenements_institutionnels_slug_key", "slug", unique=True),
        Index("evenements_institutionnels_type_idx", "type"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    titre: Mapped[str] = mapped_column(Text, nullable=False)
    date_debut: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    date_precise: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    important: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    description: Mapped[str | None] = mapped_column(Text)
    date_fin: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    chambre: Mapped[str | None] = mapped_column(Text)
    sources: Mapped[object | None] = mapped_column(JSONB)


class GroupesPolitiques(Base):
    __tablename__ = "groupes_politiques"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="groupes_politiques_pkey"),
        Index("groupes_politiques_chambre_idx", "chambre"),
        Index("groupes_politiques_legislature_idx", "legislature"),
        Index(
            "groupes_politiques_slug_chambre_legislature_key",
            "slug",
            "chambre",
            "legislature",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    chambre: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'assemblee'::text")
    )
    nom_complet: Mapped[str | None] = mapped_column(Text)
    couleur: Mapped[str | None] = mapped_column(Text)
    position: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[str | None] = mapped_column(Text)
    stats_membres_actifs: Mapped[int | None] = mapped_column(Integer)
    stats_presence_moyenne: Mapped[int | None] = mapped_column(Integer)
    stats_loyaute_moyenne: Mapped[int | None] = mapped_column(Integer)
    stats_cohesion: Mapped[int | None] = mapped_column(Integer)
    stats_participation: Mapped[int | None] = mapped_column(Integer)
    stats_calculated_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    logo_url: Mapped[str | None] = mapped_column(Text)
    stats_votes_pour: Mapped[int | None] = mapped_column(Integer)
    stats_votes_contre: Mapped[int | None] = mapped_column(Integer)
    stats_votes_abstention: Mapped[int | None] = mapped_column(Integer)
    stats_votes_absent: Mapped[int | None] = mapped_column(Integer)
    stats_presence_solennel_moyenne: Mapped[int | None] = mapped_column(Integer)
    legislature: Mapped[int | None] = mapped_column(Integer)
    nom_court: Mapped[str | None] = mapped_column(Text)

    groupes_alliances_groupe_from: Mapped[list[GroupesAlliances]] = relationship(
        "GroupesAlliances",
        foreign_keys="[GroupesAlliances.groupe_from_id]",
        back_populates="groupe_from",
    )
    groupes_alliances_groupe_to: Mapped[list[GroupesAlliances]] = relationship(
        "GroupesAlliances",
        foreign_keys="[GroupesAlliances.groupe_to_id]",
        back_populates="groupe_to",
    )
    groupes_thematiques: Mapped[list[GroupesThematiques]] = relationship(
        "GroupesThematiques", back_populates="groupe"
    )
    parlementaires: Mapped[list[Parlementaires]] = relationship(
        "Parlementaires", back_populates="groupe"
    )
    mandats_parlementaires: Mapped[list[MandatsParlementaires]] = relationship(
        "MandatsParlementaires", back_populates="groupe"
    )


class Lobbyistes(Base):
    __tablename__ = "lobbyistes"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="lobbyistes_pkey"),
        Index("lobbyistes_identifiant_national_key", "identifiant_national", unique=True),
        Index("lobbyistes_nom_idx", "nom"),
        Index("lobbyistes_secteur_idx", "secteur"),
        Index("lobbyistes_type_idx", "type"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    siren: Mapped[str | None] = mapped_column(Text)
    secteur: Mapped[str | None] = mapped_column(Text)
    adresse: Mapped[str | None] = mapped_column(Text)
    code_postal: Mapped[str | None] = mapped_column(Text)
    ville: Mapped[str | None] = mapped_column(Text)
    budget_annuel: Mapped[float | None] = mapped_column(Double(53))
    nb_lobbyistes: Mapped[int | None] = mapped_column(Integer)
    site_web: Mapped[str | None] = mapped_column(Text)
    source_data: Mapped[object | None] = mapped_column(JSONB)
    identifiant_national: Mapped[str | None] = mapped_column(Text)

    lobbyistes_secteurs: Mapped[list[LobbyistesSecteurs]] = relationship(
        "LobbyistesSecteurs", back_populates="lobbyiste"
    )
    actions_lobby: Mapped[list[ActionsLobby]] = relationship(
        "ActionsLobby", back_populates="lobbyiste"
    )


t_pg_stat_statements = Table(
    "pg_stat_statements",
    Base.metadata,
    Column("userid", OID),
    Column("dbid", OID),
    Column("toplevel", Boolean),
    Column("queryid", BigInteger),
    Column("query", Text),
    Column("plans", BigInteger),
    Column("total_plan_time", Double(53)),
    Column("min_plan_time", Double(53)),
    Column("max_plan_time", Double(53)),
    Column("mean_plan_time", Double(53)),
    Column("stddev_plan_time", Double(53)),
    Column("calls", BigInteger),
    Column("total_exec_time", Double(53)),
    Column("min_exec_time", Double(53)),
    Column("max_exec_time", Double(53)),
    Column("mean_exec_time", Double(53)),
    Column("stddev_exec_time", Double(53)),
    Column("rows", BigInteger),
    Column("shared_blks_hit", BigInteger),
    Column("shared_blks_read", BigInteger),
    Column("shared_blks_dirtied", BigInteger),
    Column("shared_blks_written", BigInteger),
    Column("local_blks_hit", BigInteger),
    Column("local_blks_read", BigInteger),
    Column("local_blks_dirtied", BigInteger),
    Column("local_blks_written", BigInteger),
    Column("temp_blks_read", BigInteger),
    Column("temp_blks_written", BigInteger),
    Column("blk_read_time", Double(53)),
    Column("blk_write_time", Double(53)),
    Column("temp_blk_read_time", Double(53)),
    Column("temp_blk_write_time", Double(53)),
    Column("wal_records", BigInteger),
    Column("wal_fpi", BigInteger),
    Column("wal_bytes", Numeric),
    Column("jit_functions", BigInteger),
    Column("jit_generation_time", Double(53)),
    Column("jit_inlining_count", BigInteger),
    Column("jit_inlining_time", Double(53)),
    Column("jit_optimization_count", BigInteger),
    Column("jit_optimization_time", Double(53)),
    Column("jit_emission_count", BigInteger),
    Column("jit_emission_time", Double(53)),
)


t_pg_stat_statements_info = Table(
    "pg_stat_statements_info",
    Base.metadata,
    Column("dealloc", BigInteger),
    Column("stats_reset", DateTime(True)),
)


class Secteurs(Base):
    __tablename__ = "secteurs"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="secteurs_pkey"),
        Index("secteurs_label_key", "label", unique=True),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    lobbyistes_secteurs: Mapped[list[LobbyistesSecteurs]] = relationship(
        "LobbyistesSecteurs", back_populates="secteur"
    )
    actions_secteurs: Mapped[list[ActionsSecteurs]] = relationship(
        "ActionsSecteurs", back_populates="secteur"
    )


class SourceStates(Base):
    __tablename__ = "source_states"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="source_states_pkey"),
        Index("source_states_source_data_type_key", "source", "data_type", unique=True),
        Index("source_states_source_idx", "source"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    data_type: Mapped[str] = mapped_column(Text, nullable=False)
    resource_url: Mapped[str] = mapped_column(Text, nullable=False)
    last_sync_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    last_check_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    last_etag: Mapped[str | None] = mapped_column(Text)
    last_modified: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    metadata_: Mapped[object | None] = mapped_column("metadata", JSONB)


class Sujets(Base):
    __tablename__ = "sujets"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="sujets_pkey"),
        Index("sujets_actif_idx", "actif"),
        Index("sujets_category_idx", "category"),
        Index("sujets_featured_featured_order_idx", "featured", "featured_order"),
        Index("sujets_slug_key", "slug", unique=True),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    dossier_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    scrutin_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    featured_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'en_cours'::text")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    date_debut: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    date_fin: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    date_dernier_vote: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    match_method: Mapped[str | None] = mapped_column(Text)
    resume: Mapped[str | None] = mapped_column(Text)
    enjeux: Mapped[str | None] = mapped_column(Text)
    ia_content_hash: Mapped[str | None] = mapped_column(Text)
    ia_generated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(True))
    groupe_amendement_descriptions: Mapped[object | None] = mapped_column(JSONB)
    ia_groupe_amendement_hash: Mapped[str | None] = mapped_column(Text)
    context_resolved_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    context_input_hash: Mapped[str | None] = mapped_column(Text)

    dossiers_legislatifs: Mapped[list[DossiersLegislatifs]] = relationship(
        "DossiersLegislatifs", back_populates="sujet"
    )
    sujet_liens: Mapped[list[SujetLiens]] = relationship("SujetLiens", back_populates="sujet")


class SyncLogs(Base):
    __tablename__ = "sync_logs"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="sync_logs_pkey"),
        Index("sync_logs_source_data_type_idx", "source", "data_type"),
        Index("sync_logs_source_idx", "source"),
        Index("sync_logs_started_at_idx", "started_at"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    statut: Mapped[str] = mapped_column(Text, nullable=False)
    items_processed: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    items_created: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    items_updated: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    started_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    data_type: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'all'::text"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    metadata_: Mapped[object | None] = mapped_column("metadata", JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))


class CandidaturesListes(Base):
    __tablename__ = "candidatures_listes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["circonscription_id"],
            ["circonscriptions.id"],
            ondelete="RESTRICT",
            onupdate="CASCADE",
            name="candidatures_listes_circonscription_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="candidatures_listes_pkey"),
        Index(
            "candidatures_listes_scrutin_circonscription_id_idx", "scrutin", "circonscription_id"
        ),
        Index("candidatures_listes_scrutin_mode_scrutin_idx", "scrutin", "mode_scrutin"),
        Index("candidatures_listes_source_uid_key", "source_uid", unique=True),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    scrutin: Mapped[str] = mapped_column(Text, nullable=False)
    circonscription_id: Mapped[str] = mapped_column(Text, nullable=False)
    mode_scrutin: Mapped[str] = mapped_column(Text, nullable=False)
    source_uid: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    numero_depot: Mapped[int | None] = mapped_column(Integer)
    libelle: Mapped[str | None] = mapped_column(Text)
    nuance: Mapped[str | None] = mapped_column(Text)
    famille: Mapped[str | None] = mapped_column(Text)
    nuance_libelle: Mapped[str | None] = mapped_column(Text)

    circonscription: Mapped[Circonscriptions] = relationship(
        "Circonscriptions", back_populates="candidatures_listes"
    )
    candidatures: Mapped[list[Candidatures]] = relationship("Candidatures", back_populates="liste")


class DossiersLegislatifs(Base):
    __tablename__ = "dossiers_legislatifs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["sujet_id"],
            ["sujets.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="dossiers_legislatifs_sujet_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="dossiers_legislatifs_pkey"),
        Index("dossiers_legislatifs_date_depot_idx", "date_depot"),
        Index("dossiers_legislatifs_etat_idx", "etat"),
        Index("dossiers_legislatifs_legislature_idx", "legislature"),
        Index("dossiers_legislatifs_sujet_id_idx", "sujet_id"),
        Index("dossiers_legislatifs_uid_key", "uid", unique=True),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    uid: Mapped[str] = mapped_column(Text, nullable=False)
    legislature: Mapped[int] = mapped_column(Integer, nullable=False)
    titre: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    titre_court: Mapped[str | None] = mapped_column(Text)
    procedure_code: Mapped[str | None] = mapped_column(Text)
    procedure_libelle: Mapped[str | None] = mapped_column(Text)
    url_an: Mapped[str | None] = mapped_column(Text)
    url_senat: Mapped[str | None] = mapped_column(Text)
    etat: Mapped[str | None] = mapped_column(Text)
    date_depot: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    date_adoption: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    loi_numero: Mapped[str | None] = mapped_column(Text)
    loi_titre: Mapped[str | None] = mapped_column(Text)
    loi_date_jo: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    source_data: Mapped[object | None] = mapped_column(JSONB)
    url_legifrance: Mapped[str | None] = mapped_column(Text)
    sujet_id: Mapped[str | None] = mapped_column(Text)
    resume_ia: Mapped[str | None] = mapped_column(Text)
    ia_content_hash: Mapped[str | None] = mapped_column(Text)
    ia_generated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(True))

    sujet: Mapped[Sujets | None] = relationship("Sujets", back_populates="dossiers_legislatifs")
    amendements: Mapped[list[Amendements]] = relationship("Amendements", back_populates="dossier")
    dossier_commissions: Mapped[list[DossierCommissions]] = relationship(
        "DossierCommissions", back_populates="dossier"
    )
    interventions: Mapped[list[Interventions]] = relationship(
        "Interventions", back_populates="dossier"
    )
    textes_articles: Mapped[list[TextesArticles]] = relationship(
        "TextesArticles", back_populates="dossier"
    )
    scrutins: Mapped[list[Scrutins]] = relationship("Scrutins", back_populates="dossier")


class GroupesAlliances(Base):
    __tablename__ = "groupes_alliances"
    __table_args__ = (
        ForeignKeyConstraint(
            ["groupe_from_id"],
            ["groupes_politiques.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="groupes_alliances_groupe_from_id_fkey",
        ),
        ForeignKeyConstraint(
            ["groupe_to_id"],
            ["groupes_politiques.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="groupes_alliances_groupe_to_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="groupes_alliances_pkey"),
        Index(
            "groupes_alliances_groupe_from_id_groupe_to_id_key",
            "groupe_from_id",
            "groupe_to_id",
            unique=True,
        ),
        Index("groupes_alliances_groupe_from_id_idx", "groupe_from_id"),
        Index("groupes_alliances_groupe_to_id_idx", "groupe_to_id"),
        Index("groupes_alliances_taux_accord_idx", "taux_accord"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    groupe_from_id: Mapped[str] = mapped_column(Text, nullable=False)
    groupe_to_id: Mapped[str] = mapped_column(Text, nullable=False)
    votes_communs: Mapped[int] = mapped_column(Integer, nullable=False)
    votes_totaux: Mapped[int] = mapped_column(Integer, nullable=False)
    taux_accord: Mapped[int] = mapped_column(Integer, nullable=False)
    calculated_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    groupe_from: Mapped[GroupesPolitiques] = relationship(
        "GroupesPolitiques",
        foreign_keys=[groupe_from_id],
        back_populates="groupes_alliances_groupe_from",
    )
    groupe_to: Mapped[GroupesPolitiques] = relationship(
        "GroupesPolitiques",
        foreign_keys=[groupe_to_id],
        back_populates="groupes_alliances_groupe_to",
    )


class GroupesThematiques(Base):
    __tablename__ = "groupes_thematiques"
    __table_args__ = (
        ForeignKeyConstraint(
            ["groupe_id"],
            ["groupes_politiques.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="groupes_thematiques_groupe_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="groupes_thematiques_pkey"),
        Index("groupes_thematiques_groupe_id_idx", "groupe_id"),
        Index(
            "groupes_thematiques_groupe_id_thematique_key", "groupe_id", "thematique", unique=True
        ),
        Index("groupes_thematiques_thematique_idx", "thematique"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    groupe_id: Mapped[str] = mapped_column(Text, nullable=False)
    thematique: Mapped[str] = mapped_column(Text, nullable=False)
    votes_totaux: Mapped[int] = mapped_column(Integer, nullable=False)
    votes_pour: Mapped[int] = mapped_column(Integer, nullable=False)
    votes_contre: Mapped[int] = mapped_column(Integer, nullable=False)
    votes_abstention: Mapped[int] = mapped_column(Integer, nullable=False)
    position_moyenne: Mapped[float] = mapped_column(Double(53), nullable=False)
    cohesion_moyenne: Mapped[int] = mapped_column(Integer, nullable=False)
    calculated_at: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    groupe: Mapped[GroupesPolitiques] = relationship(
        "GroupesPolitiques", back_populates="groupes_thematiques"
    )


class LobbyistesSecteurs(Base):
    __tablename__ = "lobbyistes_secteurs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["lobbyiste_id"],
            ["lobbyistes.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="lobbyistes_secteurs_lobbyiste_id_fkey",
        ),
        ForeignKeyConstraint(
            ["secteur_id"],
            ["secteurs.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="lobbyistes_secteurs_secteur_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="lobbyistes_secteurs_pkey"),
        Index("lobbyistes_secteurs_lobbyiste_id_idx", "lobbyiste_id"),
        Index(
            "lobbyistes_secteurs_lobbyiste_id_secteur_id_key",
            "lobbyiste_id",
            "secteur_id",
            unique=True,
        ),
        Index("lobbyistes_secteurs_secteur_id_idx", "secteur_id"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    lobbyiste_id: Mapped[str] = mapped_column(Text, nullable=False)
    secteur_id: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    lobbyiste: Mapped[Lobbyistes] = relationship("Lobbyistes", back_populates="lobbyistes_secteurs")
    secteur: Mapped[Secteurs] = relationship("Secteurs", back_populates="lobbyistes_secteurs")


class Parlementaires(Base):
    __tablename__ = "parlementaires"
    __table_args__ = (
        ForeignKeyConstraint(
            ["circonscription_id"],
            ["circonscriptions.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="parlementaires_circonscription_id_fkey",
        ),
        ForeignKeyConstraint(
            ["groupe_id"],
            ["groupes_politiques.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="parlementaires_groupe_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="parlementaires_pkey"),
        Index("parlementaires_actif_idx", "actif"),
        Index("parlementaires_chambre_actif_idx", "chambre", "actif"),
        Index("parlementaires_chambre_idx", "chambre"),
        Index("parlementaires_groupe_id_idx", "groupe_id"),
        Index("parlementaires_nom_prenom_idx", "nom", "prenom"),
        Index("parlementaires_slug_idx", "slug"),
        Index("parlementaires_slug_key", "slug", unique=True),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    chambre: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'assemblee'::text")
    )
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    prenom: Mapped[str] = mapped_column(Text, nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    sexe: Mapped[str | None] = mapped_column(Text)
    date_naissance: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    lieu_naissance: Mapped[str | None] = mapped_column(Text)
    profession: Mapped[str | None] = mapped_column(Text)
    photo_url: Mapped[str | None] = mapped_column(Text)
    twitter: Mapped[str | None] = mapped_column(Text)
    facebook: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    site_web: Mapped[str | None] = mapped_column(Text)
    groupe_id: Mapped[str | None] = mapped_column(Text)
    circonscription_id: Mapped[str | None] = mapped_column(Text)
    serie: Mapped[str | None] = mapped_column(Text)
    commission_permanente: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[str | None] = mapped_column(Text)
    source_data: Mapped[object | None] = mapped_column(JSONB)
    stats_presence: Mapped[int | None] = mapped_column(Integer)
    stats_loyaute: Mapped[int | None] = mapped_column(Integer)
    stats_participation: Mapped[int | None] = mapped_column(Integer)
    stats_interventions: Mapped[int | None] = mapped_column(Integer)
    stats_amendements: Mapped[int | None] = mapped_column(Integer)
    stats_amendements_adoptes: Mapped[int | None] = mapped_column(Integer)
    stats_questions: Mapped[int | None] = mapped_column(Integer)
    stats_calculated_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    stats_presence_solennel: Mapped[int | None] = mapped_column(Integer)
    resume_ia: Mapped[str | None] = mapped_column(Text)
    parcours_ia: Mapped[str | None] = mapped_column(Text)
    positions_cles_ia: Mapped[str | None] = mapped_column(Text)
    faits_notables_ia: Mapped[str | None] = mapped_column(Text)
    ia_content_hash: Mapped[str | None] = mapped_column(Text)
    ia_generated_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    stats_carriere_presence: Mapped[int | None] = mapped_column(Integer)
    stats_carriere_loyaute: Mapped[int | None] = mapped_column(Integer)
    stats_carriere_participation: Mapped[int | None] = mapped_column(Integer)
    stats_carriere_interventions: Mapped[int | None] = mapped_column(Integer)
    stats_carriere_amendements: Mapped[int | None] = mapped_column(Integer)
    ia_sources: Mapped[object | None] = mapped_column(JSONB)

    circonscription: Mapped[Circonscriptions | None] = relationship(
        "Circonscriptions", back_populates="parlementaires"
    )
    groupe: Mapped[GroupesPolitiques | None] = relationship(
        "GroupesPolitiques", back_populates="parlementaires"
    )
    actions_lobby: Mapped[list[ActionsLobby]] = relationship(
        "ActionsLobby", back_populates="parlementaire"
    )
    amendements: Mapped[list[Amendements]] = relationship(
        "Amendements", back_populates="parlementaire"
    )
    amendements_: Mapped[list[Amendements]] = relationship(
        "Amendements", secondary="_AmendementCosignataires", back_populates="parlementaires"
    )
    candidatures: Mapped[list[Candidatures]] = relationship(
        "Candidatures", back_populates="personne"
    )
    declarations_hatvp: Mapped[list[DeclarationsHatvp]] = relationship(
        "DeclarationsHatvp", back_populates="parlementaire"
    )
    interventions: Mapped[list[Interventions]] = relationship(
        "Interventions", back_populates="parlementaire"
    )
    mandats: Mapped[list[Mandats]] = relationship("Mandats", back_populates="parlementaire")
    mandats_parlementaires: Mapped[list[MandatsParlementaires]] = relationship(
        "MandatsParlementaires", back_populates="personne"
    )
    parlementaires_identifiants: Mapped[list[ParlementairesIdentifiants]] = relationship(
        "ParlementairesIdentifiants", back_populates="personne"
    )
    reunion_participants: Mapped[list[ReunionParticipants]] = relationship(
        "ReunionParticipants", back_populates="parlementaire"
    )
    votes: Mapped[list[Votes]] = relationship("Votes", back_populates="parlementaire")


class ResultatsListes(Base):
    __tablename__ = "resultats_listes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["circonscription_id"],
            ["circonscriptions.id"],
            ondelete="RESTRICT",
            onupdate="CASCADE",
            name="resultats_listes_circonscription_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="resultats_listes_pkey"),
        Index("resultats_listes_scrutin_circonscription_id_idx", "scrutin", "circonscription_id"),
        Index(
            "resultats_listes_scrutin_liste_source_uid_tour_key",
            "scrutin",
            "liste_source_uid",
            "tour",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    scrutin: Mapped[str] = mapped_column(Text, nullable=False)
    circonscription_id: Mapped[str] = mapped_column(Text, nullable=False)
    tour: Mapped[int] = mapped_column(Integer, nullable=False)
    liste_source_uid: Mapped[str] = mapped_column(Text, nullable=False)
    voix: Mapped[int] = mapped_column(Integer, nullable=False)
    libelle_source: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    pct_inscrits: Mapped[float | None] = mapped_column(Double(53))
    pct_exprimes: Mapped[float | None] = mapped_column(Double(53))
    sieges: Mapped[int | None] = mapped_column(Integer)
    elu: Mapped[bool | None] = mapped_column(Boolean)
    nuance_source: Mapped[str | None] = mapped_column(Text)

    circonscription: Mapped[Circonscriptions] = relationship(
        "Circonscriptions", back_populates="resultats_listes"
    )


class ResultatsTours(Base):
    __tablename__ = "resultats_tours"
    __table_args__ = (
        ForeignKeyConstraint(
            ["circonscription_id"],
            ["circonscriptions.id"],
            ondelete="RESTRICT",
            onupdate="CASCADE",
            name="resultats_tours_circonscription_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="resultats_tours_pkey"),
        Index(
            "resultats_tours_scrutin_circonscription_id_tour_key",
            "scrutin",
            "circonscription_id",
            "tour",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    scrutin: Mapped[str] = mapped_column(Text, nullable=False)
    circonscription_id: Mapped[str] = mapped_column(Text, nullable=False)
    tour: Mapped[int] = mapped_column(Integer, nullable=False)
    inscrits: Mapped[int] = mapped_column(Integer, nullable=False)
    votants: Mapped[int] = mapped_column(Integer, nullable=False)
    abstentions: Mapped[int] = mapped_column(Integer, nullable=False)
    blancs: Mapped[int] = mapped_column(Integer, nullable=False)
    nuls: Mapped[int] = mapped_column(Integer, nullable=False)
    exprimes: Mapped[int] = mapped_column(Integer, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    publie_a: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    verifie_a: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    circonscription: Mapped[Circonscriptions] = relationship(
        "Circonscriptions", back_populates="resultats_tours"
    )


class Reunions(Base):
    __tablename__ = "reunions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["commission_id"],
            ["commissions.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="reunions_commission_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="reunions_pkey"),
        Index("reunions_commission_id_idx", "commission_id"),
        Index("reunions_date_debut_idx", "date_debut"),
        Index("reunions_etat_idx", "etat"),
        Index("reunions_organe_ref_idx", "organe_ref"),
        Index("reunions_type_idx", "type"),
        Index("reunions_uid_key", "uid", unique=True),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    uid: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    date_debut: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    etat: Mapped[str] = mapped_column(Text, nullable=False)
    captation_video: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    ouverte_presse: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    date_fin: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    lieu: Mapped[str | None] = mapped_column(Text)
    odj_resume: Mapped[str | None] = mapped_column(Text)
    odj_complet: Mapped[str | None] = mapped_column(Text)
    compte_rendu_ref: Mapped[str | None] = mapped_column(Text)
    url_video: Mapped[str | None] = mapped_column(Text)
    commission_id: Mapped[str | None] = mapped_column(Text)
    organe_ref: Mapped[str | None] = mapped_column(Text)

    commission: Mapped[Commissions | None] = relationship("Commissions", back_populates="reunions")
    interventions: Mapped[list[Interventions]] = relationship(
        "Interventions", back_populates="reunion"
    )
    reunion_participants: Mapped[list[ReunionParticipants]] = relationship(
        "ReunionParticipants", back_populates="reunion"
    )
    avis_commission: Mapped[list[AvisCommission]] = relationship(
        "AvisCommission", back_populates="reunion"
    )


class SujetLiens(Base):
    __tablename__ = "sujet_liens"
    __table_args__ = (
        ForeignKeyConstraint(
            ["sujet_id"],
            ["sujets.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="sujet_liens_sujet_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="sujet_liens_pkey"),
        Index("sujet_liens_sujet_id_famille_ordre_idx", "sujet_id", "famille", "ordre"),
        Index("sujet_liens_sujet_id_url_key", "sujet_id", "url", unique=True),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    sujet_id: Mapped[str] = mapped_column(Text, nullable=False)
    famille: Mapped[str] = mapped_column(Text, nullable=False)
    titre: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'auto'::text")
    )
    ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    source_label: Mapped[str | None] = mapped_column(Text)
    date_publication: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))

    sujet: Mapped[Sujets] = relationship("Sujets", back_populates="sujet_liens")


class ActionsLobby(Base):
    __tablename__ = "actions_lobby"
    __table_args__ = (
        ForeignKeyConstraint(
            ["cible_type_id"],
            ["cible_types.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="actions_lobby_cible_type_id_fkey",
        ),
        ForeignKeyConstraint(
            ["description_id"],
            ["action_descriptions.id"],
            ondelete="RESTRICT",
            onupdate="CASCADE",
            name="actions_lobby_description_id_fkey",
        ),
        ForeignKeyConstraint(
            ["lobbyiste_id"],
            ["lobbyistes.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="actions_lobby_lobbyiste_id_fkey",
        ),
        ForeignKeyConstraint(
            ["parlementaire_id"],
            ["parlementaires.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="actions_lobby_parlementaire_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="actions_lobby_pkey"),
        Index("actions_lobby_cible_type_id_idx", "cible_type_id"),
        Index("actions_lobby_date_debut_idx", "date_debut"),
        Index("actions_lobby_description_id_idx", "description_id"),
        Index("actions_lobby_lobbyiste_id_idx", "lobbyiste_id"),
        Index("actions_lobby_parlementaire_id_idx", "parlementaire_id"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    lobbyiste_id: Mapped[str] = mapped_column(Text, nullable=False)
    date_debut: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    description_id: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    cible: Mapped[str | None] = mapped_column(Text)
    date_fin: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    budget: Mapped[float | None] = mapped_column(Double(53))
    resultat: Mapped[str | None] = mapped_column(Text)
    texte_vise: Mapped[str | None] = mapped_column(Text)
    texte_vise_nom: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    parlementaire_id: Mapped[str | None] = mapped_column(Text)
    cible_type_id: Mapped[int | None] = mapped_column(Integer)

    cible_type: Mapped[CibleTypes | None] = relationship(
        "CibleTypes", back_populates="actions_lobby"
    )
    description: Mapped[ActionDescriptions] = relationship(
        "ActionDescriptions", back_populates="actions_lobby"
    )
    lobbyiste: Mapped[Lobbyistes] = relationship("Lobbyistes", back_populates="actions_lobby")
    parlementaire: Mapped[Parlementaires | None] = relationship(
        "Parlementaires", back_populates="actions_lobby"
    )
    actions_secteurs: Mapped[list[ActionsSecteurs]] = relationship(
        "ActionsSecteurs", back_populates="action"
    )


class Amendements(Base):
    __tablename__ = "amendements"
    __table_args__ = (
        ForeignKeyConstraint(
            ["amendement_parent_id"],
            ["amendements.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="amendements_amendement_parent_id_fkey",
        ),
        ForeignKeyConstraint(
            ["dossier_id"],
            ["dossiers_legislatifs.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="amendements_dossier_id_fkey",
        ),
        ForeignKeyConstraint(
            ["parlementaire_id"],
            ["parlementaires.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="amendements_parlementaire_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="amendements_pkey"),
        Index("amendements_amendement_parent_id_idx", "amendement_parent_id"),
        Index("amendements_auteur_ref_idx", "auteur_ref"),
        Index("amendements_chambre_id_discussion_commune_idx", "chambre", "id_discussion_commune"),
        Index(
            "amendements_chambre_id_discussion_identique_idx", "chambre", "id_discussion_identique"
        ),
        Index("amendements_chambre_idx", "chambre"),
        Index("amendements_date_depot_idx", "date_depot"),
        Index("amendements_dossier_id_idx", "dossier_id"),
        Index(
            "amendements_id_tri_idx",
            "id",
            postgresql_include=["date_depot", "dossier_id", "numero_ordre", "sort"],
        ),
        Index("amendements_legislature_idx", "legislature"),
        Index("amendements_numero_chambre_texte_ref_idx", "numero", "chambre", "texte_ref"),
        Index("amendements_parlementaire_id_idx", "parlementaire_id"),
        Index("amendements_sort_idx", "sort"),
        Index("amendements_uid_canonique_key", "uid_canonique", unique=True),
        Index("amendements_uid_key", "uid", unique=True),
        Index("idx_amendements_numero_ordre", "numero_ordre"),
        Index(
            "idx_amendements_senat_texte_numero",
            "chambre",
            "texte_ref",
            "numero",
            postgresql_where="(chambre = 'senat'::text)",
        ),
        Index("idx_amendements_texte_ref", "texte_ref", postgresql_where="(texte_ref IS NOT NULL)"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    numero: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    legislature: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("17"))
    uid: Mapped[str] = mapped_column(Text, nullable=False)
    chambre: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'assemblee'::text")
    )
    uid_canonique: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    article_vise: Mapped[str | None] = mapped_column(Text)
    dispositif: Mapped[str | None] = mapped_column(Text)
    sort: Mapped[str | None] = mapped_column(Text)
    date_depot: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    date_sort: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    auteur_libelle: Mapped[str | None] = mapped_column(Text)
    auteur_ref: Mapped[str | None] = mapped_column(Text)
    expose_sommaire: Mapped[str | None] = mapped_column(Text)
    groupe_ref: Mapped[str | None] = mapped_column(Text)
    texte_ref: Mapped[str | None] = mapped_column(Text)
    parlementaire_id: Mapped[str | None] = mapped_column(Text)
    dossier_id: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    numero_ordre: Mapped[int | None] = mapped_column(Integer)
    source_hash: Mapped[str | None] = mapped_column(Text)
    alinea: Mapped[str | None] = mapped_column(Text)
    alinea_numero: Mapped[int | None] = mapped_column(Integer)
    amendement_parent_id: Mapped[str | None] = mapped_column(Text)
    amendement_parent_ref: Mapped[str | None] = mapped_column(Text)
    chronotag: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    id_discussion_commune: Mapped[str | None] = mapped_column(Text)
    id_discussion_identique: Mapped[str | None] = mapped_column(Text)
    position_discussion_commune: Mapped[str | None] = mapped_column(Text)
    position_discussion_identique: Mapped[str | None] = mapped_column(Text)
    seance_discussion_ref: Mapped[str | None] = mapped_column(Text)
    tri_amendement: Mapped[str | None] = mapped_column(Text)

    amendement_parent: Mapped[Amendements | None] = relationship(
        "Amendements", remote_side=[id], back_populates="amendement_parent_reverse"
    )
    amendement_parent_reverse: Mapped[list[Amendements]] = relationship(
        "Amendements", remote_side=[amendement_parent_id], back_populates="amendement_parent"
    )
    dossier: Mapped[DossiersLegislatifs | None] = relationship(
        "DossiersLegislatifs", back_populates="amendements"
    )
    parlementaire: Mapped[Parlementaires | None] = relationship(
        "Parlementaires", back_populates="amendements"
    )
    parlementaires: Mapped[list[Parlementaires]] = relationship(
        "Parlementaires", secondary="_AmendementCosignataires", back_populates="amendements_"
    )
    scrutins: Mapped[list[Scrutins]] = relationship(
        "Scrutins", secondary="_AmendementToScrutin", back_populates="amendements"
    )
    avis_commission: Mapped[list[AvisCommission]] = relationship(
        "AvisCommission", back_populates="amendement"
    )
    scrutins_: Mapped[list[Scrutins]] = relationship("Scrutins", back_populates="amendement")


class Candidatures(Base):
    __tablename__ = "candidatures"
    __table_args__ = (
        ForeignKeyConstraint(
            ["liste_id"],
            ["candidatures_listes.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="candidatures_liste_id_fkey",
        ),
        ForeignKeyConstraint(
            ["personne_id"],
            ["parlementaires.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="candidatures_personne_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="candidatures_pkey"),
        Index("candidatures_liste_id_role_ordre_key", "liste_id", "role", "ordre", unique=True),
        Index("candidatures_nom_prenom_idx", "nom", "prenom"),
        Index("candidatures_personne_id_idx", "personne_id"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    liste_id: Mapped[str] = mapped_column(Text, nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    nom: Mapped[str] = mapped_column(Text, nullable=False)
    prenom: Mapped[str] = mapped_column(Text, nullable=False)
    sortant_declare: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    elu: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    sexe: Mapped[str | None] = mapped_column(Text)
    annee_naissance: Mapped[int | None] = mapped_column(Integer)
    profession_code: Mapped[str | None] = mapped_column(Text)
    profession_label: Mapped[str | None] = mapped_column(Text)
    personne_id: Mapped[str | None] = mapped_column(Text)
    match_confiance: Mapped[str | None] = mapped_column(Text)
    tour_election: Mapped[int | None] = mapped_column(Integer)

    liste: Mapped[CandidaturesListes] = relationship(
        "CandidaturesListes", back_populates="candidatures"
    )
    personne: Mapped[Parlementaires | None] = relationship(
        "Parlementaires", back_populates="candidatures"
    )


class DeclarationsHatvp(Base):
    __tablename__ = "declarations_hatvp"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parlementaire_id"],
            ["parlementaires.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="declarations_hatvp_parlementaire_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="declarations_hatvp_pkey"),
        Index(
            "declarations_hatvp_parl_type_date_key",
            "parlementaire_id",
            "type_document",
            "date_depot",
            unique=True,
        ),
        Index("declarations_hatvp_parlementaire_id_idx", "parlementaire_id"),
        Index("declarations_hatvp_type_document_idx", "type_document"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    parlementaire_id: Mapped[str] = mapped_column(Text, nullable=False)
    type_document: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    date_publication: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    date_depot: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    url_dossier: Mapped[str | None] = mapped_column(Text)
    nom_fichier: Mapped[str | None] = mapped_column(Text)
    xml_fichier: Mapped[str | None] = mapped_column(Text)
    statut: Mapped[str | None] = mapped_column(Text)
    departement: Mapped[str | None] = mapped_column(Text)

    parlementaire: Mapped[Parlementaires] = relationship(
        "Parlementaires", back_populates="declarations_hatvp"
    )


class DossierCommissions(Base):
    __tablename__ = "dossier_commissions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["commission_id"],
            ["commissions.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="dossier_commissions_commission_id_fkey",
        ),
        ForeignKeyConstraint(
            ["dossier_id"],
            ["dossiers_legislatifs.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="dossier_commissions_dossier_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="dossier_commissions_pkey"),
        Index("dossier_commissions_commission_id_idx", "commission_id"),
        Index(
            "dossier_commissions_dossier_id_commission_id_role_key",
            "dossier_id",
            "commission_id",
            "role",
            unique=True,
        ),
        Index("dossier_commissions_dossier_id_idx", "dossier_id"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    dossier_id: Mapped[str] = mapped_column(Text, nullable=False)
    commission_id: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    commission: Mapped[Commissions] = relationship(
        "Commissions", back_populates="dossier_commissions"
    )
    dossier: Mapped[DossiersLegislatifs] = relationship(
        "DossiersLegislatifs", back_populates="dossier_commissions"
    )


class Interventions(Base):
    __tablename__ = "interventions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["dossier_id"],
            ["dossiers_legislatifs.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="interventions_dossier_id_fkey",
        ),
        ForeignKeyConstraint(
            ["parlementaire_id"],
            ["parlementaires.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="interventions_parlementaire_id_fkey",
        ),
        ForeignKeyConstraint(
            ["reunion_id"],
            ["reunions.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="interventions_reunion_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="interventions_pkey"),
        Index("interventions_article_vise_idx", "article_vise"),
        Index("interventions_chambre_idx", "chambre"),
        Index("interventions_date_idx", "date"),
        Index("interventions_dossier_id_idx", "dossier_id"),
        Index("interventions_parlementaire_id_idx", "parlementaire_id"),
        Index("interventions_reunion_id_ordre_idx", "reunion_id", "ordre"),
        Index("interventions_seance_id_idx", "seance_id"),
        Index("interventions_seance_uid_ordre_absolu_idx", "seance_uid", "ordre_absolu"),
        Index("interventions_source_uid_key", "source_uid", unique=True),
        Index("interventions_type_idx", "type"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    contenu: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    chambre: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'assemblee'::text")
    )
    amendements_vises: Mapped[list[str]] = mapped_column(
        ARRAY(Text()), nullable=False, server_default=text("ARRAY[]::text[]")
    )
    est_presidence: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    seance_id: Mapped[str | None] = mapped_column(Text)
    mots_cles: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text()), server_default=text("ARRAY[]::text[]")
    )
    source_url: Mapped[str | None] = mapped_column(Text)
    parlementaire_id: Mapped[str | None] = mapped_column(Text)
    ordre: Mapped[int | None] = mapped_column(Integer)
    orateur_nom: Mapped[str | None] = mapped_column(Text)
    orateur_prenom: Mapped[str | None] = mapped_column(Text)
    orateur_qualite: Mapped[str | None] = mapped_column(Text)
    source_uid: Mapped[str | None] = mapped_column(Text)
    seance_uid: Mapped[str | None] = mapped_column(Text)
    ordre_absolu: Mapped[int | None] = mapped_column(Integer)
    code_grammaire: Mapped[str | None] = mapped_column(Text)
    article_vise: Mapped[str | None] = mapped_column(Text)
    texte_numero: Mapped[str | None] = mapped_column(Text)
    reunion_id: Mapped[str | None] = mapped_column(Text)
    orateur_groupe: Mapped[str | None] = mapped_column(Text)
    dossier_id: Mapped[str | None] = mapped_column(Text)

    dossier: Mapped[DossiersLegislatifs | None] = relationship(
        "DossiersLegislatifs", back_populates="interventions"
    )
    parlementaire: Mapped[Parlementaires | None] = relationship(
        "Parlementaires", back_populates="interventions"
    )
    reunion: Mapped[Reunions | None] = relationship("Reunions", back_populates="interventions")
    intervention_scrutin: Mapped[list[InterventionScrutin]] = relationship(
        "InterventionScrutin", back_populates="intervention"
    )


class Mandats(Base):
    __tablename__ = "mandats"
    __table_args__ = (
        ForeignKeyConstraint(
            ["commission_id"],
            ["commissions.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="mandats_commission_id_fkey",
        ),
        ForeignKeyConstraint(
            ["parlementaire_id"],
            ["parlementaires.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="mandats_parlementaire_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="mandats_pkey"),
        Index("mandats_commission_id_idx", "commission_id"),
        Index("mandats_date_debut_idx", "date_debut"),
        Index("mandats_parlementaire_id_idx", "parlementaire_id"),
        Index(
            "mandats_parlementaire_id_organe_ref_date_fin_idx",
            "parlementaire_id",
            "organe_ref",
            "date_fin",
        ),
        Index("mandats_source_uid_key", "source_uid", unique=True),
        Index("mandats_type_organe_idx", "type_organe"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    parlementaire_id: Mapped[str] = mapped_column(Text, nullable=False)
    type_organe: Mapped[str] = mapped_column(Text, nullable=False)
    date_debut: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    institution: Mapped[str | None] = mapped_column(Text)
    qualite: Mapped[str | None] = mapped_column(Text)
    date_fin: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    source_uid: Mapped[str | None] = mapped_column(Text)
    commission_id: Mapped[str | None] = mapped_column(Text)
    organe_ref: Mapped[str | None] = mapped_column(Text)

    commission: Mapped[Commissions | None] = relationship("Commissions", back_populates="mandats")
    parlementaire: Mapped[Parlementaires] = relationship("Parlementaires", back_populates="mandats")


class MandatsParlementaires(Base):
    __tablename__ = "mandats_parlementaires"
    __table_args__ = (
        ForeignKeyConstraint(
            ["circonscription_id"],
            ["circonscriptions.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="mandats_parlementaires_circonscription_id_fkey",
        ),
        ForeignKeyConstraint(
            ["groupe_id"],
            ["groupes_politiques.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="mandats_parlementaires_groupe_id_fkey",
        ),
        ForeignKeyConstraint(
            ["personne_id"],
            ["parlementaires.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="mandats_parlementaires_personne_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="mandats_parlementaires_pkey"),
        Index("mandats_parlementaires_chambre_legislature_idx", "chambre", "legislature"),
        Index("mandats_parlementaires_groupe_id_idx", "groupe_id"),
        Index("mandats_parlementaires_legislature_idx", "legislature"),
        Index("mandats_parlementaires_mandat_uid_key", "mandat_uid", unique=True),
        Index("mandats_parlementaires_mandature_idx", "mandature"),
        Index(
            "mandats_parlementaires_personne_id_chambre_legislature_mand_key",
            "personne_id",
            "chambre",
            "legislature",
            "mandature",
            unique=True,
        ),
        Index("mandats_parlementaires_personne_id_idx", "personne_id"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    personne_id: Mapped[str] = mapped_column(Text, nullable=False)
    chambre: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'assemblee'::text")
    )
    date_debut: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    legislature: Mapped[int | None] = mapped_column(Integer)
    mandature: Mapped[int | None] = mapped_column(Integer)
    serie: Mapped[str | None] = mapped_column(Text)
    date_fin: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    groupe_id: Mapped[str | None] = mapped_column(Text)
    circonscription_id: Mapped[str | None] = mapped_column(Text)
    commission_permanente: Mapped[str | None] = mapped_column(Text)
    stats_presence: Mapped[int | None] = mapped_column(Integer)
    stats_presence_solennel: Mapped[int | None] = mapped_column(Integer)
    stats_loyaute: Mapped[int | None] = mapped_column(Integer)
    stats_participation: Mapped[int | None] = mapped_column(Integer)
    stats_interventions: Mapped[int | None] = mapped_column(Integer)
    stats_amendements: Mapped[int | None] = mapped_column(Integer)
    stats_amendements_adoptes: Mapped[int | None] = mapped_column(Integer)
    stats_questions: Mapped[int | None] = mapped_column(Integer)
    stats_calculated_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(precision=3))
    mandat_uid: Mapped[str | None] = mapped_column(Text)
    source_data: Mapped[object | None] = mapped_column(JSONB)

    circonscription: Mapped[Circonscriptions | None] = relationship(
        "Circonscriptions", back_populates="mandats_parlementaires"
    )
    groupe: Mapped[GroupesPolitiques | None] = relationship(
        "GroupesPolitiques", back_populates="mandats_parlementaires"
    )
    personne: Mapped[Parlementaires] = relationship(
        "Parlementaires", back_populates="mandats_parlementaires"
    )


class ParlementairesIdentifiants(Base):
    __tablename__ = "parlementaires_identifiants"
    __table_args__ = (
        ForeignKeyConstraint(
            ["personne_id"],
            ["parlementaires.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="parlementaires_identifiants_personne_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="parlementaires_identifiants_pkey"),
        Index(
            "parlementaires_identifiants_chambre_source_id_key", "chambre", "source_id", unique=True
        ),
        Index("parlementaires_identifiants_personne_id_idx", "personne_id"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    personne_id: Mapped[str] = mapped_column(Text, nullable=False)
    chambre: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    personne: Mapped[Parlementaires] = relationship(
        "Parlementaires", back_populates="parlementaires_identifiants"
    )


class ReunionParticipants(Base):
    __tablename__ = "reunion_participants"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parlementaire_id"],
            ["parlementaires.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="reunion_participants_parlementaire_id_fkey",
        ),
        ForeignKeyConstraint(
            ["reunion_id"],
            ["reunions.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="reunion_participants_reunion_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="reunion_participants_pkey"),
        Index("reunion_participants_parlementaire_id_idx", "parlementaire_id"),
        Index(
            "reunion_participants_reunion_id_parlementaire_id_key",
            "reunion_id",
            "parlementaire_id",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    reunion_id: Mapped[str] = mapped_column(Text, nullable=False)
    parlementaire_id: Mapped[str] = mapped_column(Text, nullable=False)
    presence: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    parlementaire: Mapped[Parlementaires] = relationship(
        "Parlementaires", back_populates="reunion_participants"
    )
    reunion: Mapped[Reunions] = relationship("Reunions", back_populates="reunion_participants")


class TextesArticles(Base):
    __tablename__ = "textes_articles"
    __table_args__ = (
        ForeignKeyConstraint(
            ["dossier_id"],
            ["dossiers_legislatifs.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="textes_articles_dossier_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="textes_articles_pkey"),
        Index("textes_articles_chambre_legislature_idx", "chambre", "legislature"),
        Index("textes_articles_dossier_id_idx", "dossier_id"),
        Index("textes_articles_texte_ref_idx", "texte_ref"),
        Index("textes_articles_texte_ref_numero_key", "texte_ref", "numero", unique=True),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    texte_ref: Mapped[str] = mapped_column(Text, nullable=False)
    numero: Mapped[str] = mapped_column(Text, nullable=False)
    libelle: Mapped[str] = mapped_column(Text, nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False)
    contenu: Mapped[str] = mapped_column(Text, nullable=False)
    chambre: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'assemblee'::text")
    )
    legislature: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    dossier_id: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)

    dossier: Mapped[DossiersLegislatifs | None] = relationship(
        "DossiersLegislatifs", back_populates="textes_articles"
    )


t__AmendementCosignataires = Table(
    "_AmendementCosignataires",
    Base.metadata,
    Column("A", Text, primary_key=True),
    Column("B", Text, primary_key=True),
    ForeignKeyConstraint(
        ["A"],
        ["amendements.id"],
        ondelete="CASCADE",
        onupdate="CASCADE",
        name="_AmendementCosignataires_A_fkey",
    ),
    ForeignKeyConstraint(
        ["B"],
        ["parlementaires.id"],
        ondelete="CASCADE",
        onupdate="CASCADE",
        name="_AmendementCosignataires_B_fkey",
    ),
    PrimaryKeyConstraint("A", "B", name="_AmendementCosignataires_AB_pkey"),
    Index("_AmendementCosignataires_B_A_idx", "B", "A"),
    Index("_AmendementCosignataires_B_index", "B"),
)


class ActionsSecteurs(Base):
    __tablename__ = "actions_secteurs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["action_id"],
            ["actions_lobby.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="actions_secteurs_action_id_fkey",
        ),
        ForeignKeyConstraint(
            ["secteur_id"],
            ["secteurs.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="actions_secteurs_secteur_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="actions_secteurs_pkey"),
        Index("actions_secteurs_action_id_idx", "action_id"),
        Index("actions_secteurs_action_id_secteur_id_key", "action_id", "secteur_id", unique=True),
        Index("actions_secteurs_secteur_id_idx", "secteur_id"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    action_id: Mapped[str] = mapped_column(Text, nullable=False)
    secteur_id: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    action: Mapped[ActionsLobby] = relationship("ActionsLobby", back_populates="actions_secteurs")
    secteur: Mapped[Secteurs] = relationship("Secteurs", back_populates="actions_secteurs")


class AvisCommission(Base):
    __tablename__ = "avis_commission"
    __table_args__ = (
        ForeignKeyConstraint(
            ["amendement_id"],
            ["amendements.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="avis_commission_amendement_id_fkey",
        ),
        ForeignKeyConstraint(
            ["reunion_id"],
            ["reunions.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="avis_commission_reunion_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="avis_commission_pkey"),
        Index("avis_commission_amendement_id_idx", "amendement_id"),
        Index("avis_commission_reunion_id_numero_key", "reunion_id", "numero", unique=True),
        Index("avis_commission_sens_idx", "sens"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    reunion_id: Mapped[str] = mapped_column(Text, nullable=False)
    numero: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[str] = mapped_column(Text, nullable=False)
    sens: Mapped[str] = mapped_column(Text, nullable=False)
    ordre: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    amendement_id: Mapped[str | None] = mapped_column(Text)
    place: Mapped[str | None] = mapped_column(Text)
    auteur: Mapped[str | None] = mapped_column(Text)
    groupe: Mapped[str | None] = mapped_column(Text)

    amendement: Mapped[Amendements | None] = relationship(
        "Amendements", back_populates="avis_commission"
    )
    reunion: Mapped[Reunions] = relationship("Reunions", back_populates="avis_commission")


class Scrutins(Base):
    __tablename__ = "scrutins"
    __table_args__ = (
        ForeignKeyConstraint(
            ["amendement_id"],
            ["amendements.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="scrutins_amendement_id_fkey",
        ),
        ForeignKeyConstraint(
            ["dossier_id"],
            ["dossiers_legislatifs.id"],
            ondelete="SET NULL",
            onupdate="CASCADE",
            name="scrutins_dossier_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="scrutins_pkey"),
        UniqueConstraint(
            "numero", "chambre", "session", name="scrutins_numero_chambre_session_key"
        ),
        Index("scrutins_amendement_id_idx", "amendement_id"),
        Index(
            "scrutins_appariement", "seance_ref", "nombre_votants", "nombre_pour", "nombre_contre"
        ),
        Index("scrutins_chambre_date_numero_idx", "chambre", "date", "numero"),
        Index("scrutins_chambre_idx", "chambre"),
        Index("scrutins_date_idx", "date"),
        Index("scrutins_dossier_id_idx", "dossier_id"),
        Index("scrutins_importance_idx", "importance"),
        Index("scrutins_legislature_idx", "legislature"),
        Index("scrutins_nature_vote_idx", "nature_vote"),
        Index("scrutins_session_idx", "session"),
        Index("scrutins_tags_idx", "tags"),
        Index("scrutins_texte_id_idx", "texte_id"),
        Index("scrutins_type_vote_idx", "type_vote"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    titre: Mapped[str] = mapped_column(Text, nullable=False)
    type_vote: Mapped[str] = mapped_column(Text, nullable=False)
    sort: Mapped[str] = mapped_column(Text, nullable=False)
    nombre_votants: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre_pour: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre_contre: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre_abstention: Mapped[int] = mapped_column(Integer, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    chambre: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'assemblee'::text")
    )
    session: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'17'::text"))
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text()), server_default=text("ARRAY[]::text[]")
    )
    texte_id: Mapped[str | None] = mapped_column(Text)
    texte_numero: Mapped[str | None] = mapped_column(Text)
    texte_titre: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_data: Mapped[object | None] = mapped_column(JSONB)
    objet_libelle: Mapped[str | None] = mapped_column(Text)
    demandeur_texte: Mapped[str | None] = mapped_column(Text)
    seance_ref: Mapped[str | None] = mapped_column(Text)
    dossier_id: Mapped[str | None] = mapped_column(Text)
    amendement_id: Mapped[str | None] = mapped_column(Text)
    resume_ia: Mapped[str | None] = mapped_column(Text)
    ia_content_hash: Mapped[str | None] = mapped_column(Text)
    ia_generated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(True))
    legislature: Mapped[int | None] = mapped_column(Integer)
    nature_vote: Mapped[str | None] = mapped_column(Text)
    source_hash: Mapped[str | None] = mapped_column(Text)

    amendements: Mapped[list[Amendements]] = relationship(
        "Amendements", secondary="_AmendementToScrutin", back_populates="scrutins"
    )
    amendement: Mapped[Amendements | None] = relationship("Amendements", back_populates="scrutins_")
    dossier: Mapped[DossiersLegislatifs | None] = relationship(
        "DossiersLegislatifs", back_populates="scrutins"
    )
    intervention_scrutin: Mapped[list[InterventionScrutin]] = relationship(
        "InterventionScrutin", back_populates="scrutin"
    )
    votes: Mapped[list[Votes]] = relationship("Votes", back_populates="scrutin")


t__AmendementToScrutin = Table(
    "_AmendementToScrutin",
    Base.metadata,
    Column("A", Text, nullable=False),
    Column("B", Text, nullable=False),
    ForeignKeyConstraint(
        ["A"],
        ["amendements.id"],
        ondelete="CASCADE",
        onupdate="CASCADE",
        name="_AmendementToScrutin_A_fkey",
    ),
    ForeignKeyConstraint(
        ["B"],
        ["scrutins.id"],
        ondelete="CASCADE",
        onupdate="CASCADE",
        name="_AmendementToScrutin_B_fkey",
    ),
    Index("_AmendementToScrutin_AB_unique", "A", "B", unique=True),
    Index("_AmendementToScrutin_B_index", "B"),
)


class InterventionScrutin(Base):
    __tablename__ = "intervention_scrutin"
    __table_args__ = (
        ForeignKeyConstraint(
            ["intervention_id"],
            ["interventions.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="intervention_scrutin_intervention_id_fkey",
        ),
        ForeignKeyConstraint(
            ["scrutin_id"],
            ["scrutins.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="intervention_scrutin_scrutin_id_fkey",
        ),
        PrimaryKeyConstraint("intervention_id", "scrutin_id", name="intervention_scrutin_pkey"),
        Index("intervention_scrutin_scrutin_id_via_idx", "scrutin_id", "via"),
    )

    intervention_id: Mapped[str] = mapped_column(Text, primary_key=True)
    scrutin_id: Mapped[str] = mapped_column(Text, primary_key=True)
    via: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    intervention: Mapped[Interventions] = relationship(
        "Interventions", back_populates="intervention_scrutin"
    )
    scrutin: Mapped[Scrutins] = relationship("Scrutins", back_populates="intervention_scrutin")


class Votes(Base):
    __tablename__ = "votes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["parlementaire_id"],
            ["parlementaires.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="votes_parlementaire_id_fkey",
        ),
        ForeignKeyConstraint(
            ["scrutin_id"],
            ["scrutins.id"],
            ondelete="CASCADE",
            onupdate="CASCADE",
            name="votes_scrutin_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="votes_pkey"),
        Index("votes_parlementaire_id_idx", "parlementaire_id"),
        Index(
            "votes_parlementaire_id_scrutin_id_key", "parlementaire_id", "scrutin_id", unique=True
        ),
        Index("votes_position_idx", "position"),
        Index("votes_scrutin_id_idx", "scrutin_id"),
        Index("votes_scrutin_id_position_idx", "scrutin_id", "position"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    scrutin_id: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[str] = mapped_column(Text, nullable=False)
    par_delegation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    parlementaire_id: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(precision=3), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    mise_au_point: Mapped[str | None] = mapped_column(Text)

    parlementaire: Mapped[Parlementaires] = relationship("Parlementaires", back_populates="votes")
    scrutin: Mapped[Scrutins] = relationship("Scrutins", back_populates="votes")
