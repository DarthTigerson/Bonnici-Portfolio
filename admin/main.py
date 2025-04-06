from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes import home, messages, visitors, admin
import sys
import os
# Add the parent directory to sys.path to allow importing from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine
import models

app = FastAPI(
    title="Admin Panel",
    description="Thomas Bonnici's Admin Panel",
    version="0.3.0"
)

models.Base.metadata.create_all(bind=engine)

# Mount static files at /static
app.mount("/static", StaticFiles(directory="admin/static"), name="static")

# Include routes
app.include_router(admin.router)  # Include admin routes first (login, etc.)
app.include_router(home.router)
app.include_router(messages.router)
app.include_router(visitors.router)