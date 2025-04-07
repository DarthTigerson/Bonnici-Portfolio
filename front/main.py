from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes import home
import sys
import os
# Add the parent directory to sys.path to allow importing from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine
import models

app = FastAPI(
    title="Portfolio Website",
    description="Thomas Bonnici's Portfolio",
    version="0.4.0"
)

models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="front/static"), name="static")

app.include_router(home.router)