"""Point d'entrée de l'API FastAPI Democracy Watch."""

from fastapi import FastAPI

from democracy_watch.config import Settings, load_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construit et configure l'application FastAPI."""
    resolved_settings = settings if settings is not None else load_settings()
    application = FastAPI(
        title="Democracy Watch API",
        version="0.1.0",
        description="API de suivi parlementaire pour les chargés de plaidoyer associatifs.",
    )
    application.state.settings = resolved_settings

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        """Vérifie que l'application est prête à répondre aux requêtes."""
        return {"status": "ok"}

    return application


app = create_app()
