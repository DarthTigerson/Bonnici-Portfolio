import os
import sys
from uuid import UUID
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import ContactMessage
from .admin import require_admin


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("")
@require_admin
async def list_messages(request: Request, unread: bool = False, db: Session = Depends(get_db)):
    query = db.query(ContactMessage).filter(ContactMessage.archived == False)
    if unread:
        query = query.filter(ContactMessage.viewed == False)
    msgs = query.order_by(ContactMessage.created.desc()).all()
    return [
        {
            "id": str(m.id),
            "fullname": m.fullname,
            "email": m.email,
            "subject": m.subject,
            "message": m.message,
            "created": m.created.isoformat(),
            "viewed": m.viewed,
            "archived": m.archived,
            "ip_address": m.ip_address,
        }
        for m in msgs
    ]


@router.delete("")
@require_admin
async def delete_all(request: Request, db: Session = Depends(get_db)):
    try:
        db.query(ContactMessage).delete()
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{message_id}")
@require_admin
async def get_message(request: Request, message_id: UUID, db: Session = Depends(get_db)):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    ip_info = None
    if msg.ip_address:
        ip = "8.8.8.8" if msg.ip_address == "127.0.0.1" else msg.ip_address
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "success":
                    ip_info = data
        except Exception:
            pass

    return {
        "id": str(msg.id),
        "fullname": msg.fullname,
        "email": msg.email,
        "subject": msg.subject,
        "message": msg.message,
        "created": msg.created.isoformat(),
        "viewed": msg.viewed,
        "archived": msg.archived,
        "ip_address": msg.ip_address,
        "country": ip_info.get("country") if ip_info else None,
        "city": ip_info.get("city") if ip_info else None,
        "latitude": ip_info.get("lat") if ip_info else None,
        "longitude": ip_info.get("lon") if ip_info else None,
    }


@router.post("/{message_id}/read")
@require_admin
async def mark_read(request: Request, message_id: UUID, db: Session = Depends(get_db)):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.viewed = True
    db.commit()
    return {"status": "success"}


@router.post("/{message_id}/unread")
@require_admin
async def mark_unread(request: Request, message_id: UUID, db: Session = Depends(get_db)):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.viewed = False
    db.commit()
    return {"status": "success"}


@router.delete("/{message_id}")
@require_admin
async def delete_message(request: Request, message_id: UUID, db: Session = Depends(get_db)):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(msg)
    db.commit()
    return {"status": "success"}
