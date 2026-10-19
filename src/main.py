
from fastapi import FastAPI
import os

from src.config import get_settings
from src.database import engine, Base

from src.models.schema import SchemaRecord
from src.models.ingest import IngestionRecord, TransactionRecord
from src.models.exception import ReconException, AuditRecord

from src.routers import health, schema, ingest, match, exceptions, audit

settings = get_settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

app.include_router(health.router)
app.include_router(schema.router)
app.include_router(ingest.router)
app.include_router(match.router)
app.include_router(exceptions.router)
app.include_router(audit.router)