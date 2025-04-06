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
    version="0.3.2"
)

models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="admin/static"), name="static")

app.include_router(admin.router)
app.include_router(home.router)
app.include_router(messages.router)
app.include_router(visitors.router)