from fastapi import FastAPI
import os
from src.config import get_settings
from src.database import engine, Base
from src.routers import health, schema

# Ensure storage directories exist
settings = get_settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Auto-create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

# Register endpoints
app.include_router(health.router)
app.include_router(schema.router)