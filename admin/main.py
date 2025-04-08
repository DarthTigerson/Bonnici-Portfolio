from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes import admin, home, messages, portfolio, profile, visitors, webhooks
import sys
import os
# Add the parent directory to sys.path to allow importing from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine
import models

app = FastAPI(
    title="Admin Panel",
    description="Bonnici Portfolioo Admin Panel",
    version="0.4.1"
)

models.Base.metadata.create_all(bind=engine)

# Mount static directories
app.mount("/static", StaticFiles(directory="admin/static"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")

app.include_router(admin.router)
app.include_router(home.router)
app.include_router(messages.router)
app.include_router(portfolio.router)
app.include_router(profile.router)
app.include_router(visitors.router)
app.include_router(webhooks.router)