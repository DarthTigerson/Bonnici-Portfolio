import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routes import home

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine
import models

app = FastAPI(title="Portfolio Website", version="0.5.0")

models.Base.metadata.create_all(bind=engine)

# CORS — only needed for local Vite dev server (Vite proxy handles prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Mount shared data directory (images, etc.)
app.mount("/data", StaticFiles(directory="data"), name="data")

# API routes
app.include_router(home.router)

# Serve React build for everything else (SPA fallback)
FRONT_APP_DIST = "front-app/dist"

if os.path.isdir(FRONT_APP_DIST):
    app.mount("/assets", StaticFiles(directory=f"{FRONT_APP_DIST}/assets"), name="front-assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        # Serve static files that exist (e.g. favicon.ico, icons.svg)
        file_path = os.path.join(FRONT_APP_DIST, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(f"{FRONT_APP_DIST}/index.html")
