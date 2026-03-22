import os
import sys
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import ContactMessage, Entry
from .admin import require_admin


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
@require_admin
async def dashboard(request: Request, db: Session = Depends(get_db)):
    today = datetime.now().date()
    unread = db.query(ContactMessage).filter(
        ContactMessage.viewed == False,
        ContactMessage.archived == False,
    ).count()
    visitors_today = db.query(distinct(Entry.ip_address)).filter(
        func.date(Entry.created) == today
    ).count()
    views_today = db.query(Entry).filter(
        func.date(Entry.created) == today
    ).count()
    return {
        "unread_messages": unread,
        "visitors_today": visitors_today,
        "page_views_today": views_today,
    }
