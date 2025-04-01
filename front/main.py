from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes import home
import sys
import os
# Add the parent directory to sys.path to allow importing from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine
import front.models as models

# Create FastAPI app
app = FastAPI(
    title="Portfolio Website",
    description="Aakash Rajbanshi's Portfolio",
    version="0.1.0"
)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Mount static files directory - point to the static directory within front/
app.mount("/static", StaticFiles(directory="front/static"), name="static")

# Include routers
app.include_router(home.router)