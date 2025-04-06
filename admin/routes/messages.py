import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session
import requests

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import ContactMessage, Entry
from .admin import require_admin

# Set up templates
templates = Jinja2Templates(directory="admin/templates")

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)

@router.get("")
@require_admin
async def messages(request: Request, show_unread: bool = False, db: Session = Depends(get_db)):
    """Get all non-archived messages with optional unread filter"""
    query = db.query(ContactMessage).filter(ContactMessage.archived == False)
    
    if show_unread:
        query = query.filter(ContactMessage.viewed == False)
    
    messages = query.order_by(ContactMessage.created.desc()).all()
    
    return templates.TemplateResponse("messages.html", {
        "request": request,
        "messages": messages,
        "show_unread": show_unread
    })

@router.get("/{message_id}")
@require_admin
async def get_message(request: Request, message_id: UUID, db: Session = Depends(get_db)):
    """Get a specific message by UUID"""
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Get IP geolocation data
    ip_info = None
    if message.ip_address:
        # Use 8.8.8.8 (Google DNS) for testing when IP is localhost
        ip_to_query = "8.8.8.8" if message.ip_address == "127.0.0.1" else message.ip_address
        
        try:
            response = requests.get(f"http://ip-api.com/json/{ip_to_query}")
            if response.status_code == 200:
                ip_info = response.json()
        except Exception as e:
            print(f"Error getting IP info: {str(e)}")
    
    return {
        "id": str(message.id),
        "fullname": message.fullname,
        "email": message.email,
        "subject": message.subject,
        "message": message.message,
        "created": message.created.isoformat(),
        "ip_address": message.ip_address,
        "country": ip_info.get("country") if ip_info and ip_info.get("status") == "success" else None,
        "city": ip_info.get("city") if ip_info and ip_info.get("status") == "success" else None,
        "latitude": ip_info.get("lat") if ip_info and ip_info.get("status") == "success" else None,
        "longitude": ip_info.get("lon") if ip_info and ip_info.get("status") == "success" else None
    }

@router.post("/{message_id}/read")
@require_admin
async def mark_as_read(request: Request, message_id: UUID, db: Session = Depends(get_db)):
    """Mark a message as read"""
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.viewed = True
    db.commit()
    return {"status": "success"}

@router.post("/{message_id}/archive")
@require_admin
async def archive_message(request: Request, message_id: UUID, db: Session = Depends(get_db)):
    """Archive a message"""
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.archived = True
    db.commit()
    return {"status": "success"}

@router.post("/{message_id}/unread")
@require_admin
async def mark_as_unread(request: Request, message_id: UUID, db: Session = Depends(get_db)):
    """Mark a message as unread"""
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.viewed = False
    db.commit()
    return {"status": "success"}

@router.delete("/{message_id}/delete")
@require_admin
async def delete_message(request: Request, message_id: UUID, db: Session = Depends(get_db)):
    """Delete a message"""
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    db.delete(message)
    db.commit()
    return {"status": "success"}

@router.delete("/all")
@require_admin
async def delete_all_messages(request: Request, db: Session = Depends(get_db)):
    """Delete all messages"""
    try:
        # Delete all messages
        db.query(ContactMessage).delete()
        db.commit()
        return {"status": "success", "message": "All messages deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    