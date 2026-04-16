import logging

from fastapi import FastAPI

from app.api.routes import auth, dashboard, farms, lots, settings, sync, vaccinations, vaccines
from app.core.config import settings as app_settings
from app.db.database import Base, SessionLocal, engine
from app.services.bootstrap import BootstrapService
from app.services.schema_service import SchemaService

logger = logging.getLogger(__name__)

app = FastAPI(title=app_settings.app_name, version="1.0.0")


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Starting LoteCerto API bootstrap")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Base metadata ensured")

        SchemaService.ensure_schema(engine)
        logger.info("Schema migration ensured")

        with SessionLocal() as db:
            BootstrapService.ensure_defaults(db)
        logger.info("Default data ensured")
    except Exception:
        logger.exception("Startup bootstrap failed")
        raise


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": 'ok'}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix=app_settings.api_prefix)
app.include_router(farms.router, prefix=app_settings.api_prefix)
app.include_router(lots.router, prefix=app_settings.api_prefix)
app.include_router(vaccines.router, prefix=app_settings.api_prefix)
app.include_router(vaccinations.router, prefix=app_settings.api_prefix)
app.include_router(settings.router, prefix=app_settings.api_prefix)
app.include_router(dashboard.router, prefix=app_settings.api_prefix)
app.include_router(sync.router, prefix=app_settings.api_prefix)
