import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import ContactMessage, Entry
from .admin import require_admin

# Set up templates
templates = Jinja2Templates(directory="admin/templates")

# Database dependency
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_todays_page_views(db: Session) -> int:
    """Get the count of entries for the current day"""
    today = datetime.now().date()
    return db.query(Entry).filter(
        func.date(Entry.created) == today
    ).count()

def get_unique_visitors_today(db: Session) -> int:
    """Get the count of unique visitors (by IP) for the current day"""
    today = datetime.now().date()
    return db.query(distinct(Entry.ip_address)).filter(
        func.date(Entry.created) == today
    ).count()

def get_unread_messages_count(db: Session) -> int:
    """Get the count of unread messages"""
    return db.query(ContactMessage).filter(
        ContactMessage.viewed == False,
        ContactMessage.archived == False
    ).count()

router = APIRouter(
    prefix="",
    tags=["admin"],
)

@router.get("/")
@require_admin
async def home(request: Request, db: Session = Depends(get_db)):
    # Get today's entry counts
    todays_entries = get_todays_page_views(db)
    unique_visitors = get_unique_visitors_today(db)
    unread_messages = get_unread_messages_count(db)
    
    return templates.TemplateResponse(
        "home.html", 
        {
            "request": request,
            "todays_entries": todays_entries,
            "unique_visitors": unique_visitors,
            "unread_messages": unread_messages
        }
    )