import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .routes import admin, home, messages, portfolio, profile, settings, visitors, webhooks

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine
import models

app = FastAPI(
    title="Admin Panel",
    description="Bonnici Portfolio Admin Panel",
    version="0.5.0"
)

models.Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/data", StaticFiles(directory="data"), name="data")

app.include_router(admin.router)
app.include_router(home.router)
app.include_router(messages.router)
app.include_router(portfolio.router)
app.include_router(profile.router)
app.include_router(settings.router)
app.include_router(visitors.router)
app.include_router(webhooks.router)

# Serve React SPA
if os.path.isdir("admin-app/dist"):
    app.mount("/assets", StaticFiles(directory="admin-app/dist/assets"), name="spa-assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        # Don't intercept API routes (auth routes are fine — different methods or registered first)
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404)
        file_path = os.path.join("admin-app/dist", full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse("admin-app/dist/index.html")
