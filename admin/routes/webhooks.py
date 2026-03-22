import os
import sys
import uuid
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import Webhook
from .admin import require_admin


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def detect_platform(url: str) -> str:
    u = url.lower()
    if "discord.com/api/webhooks" in u:
        return "discord"
    if "hooks.slack.com" in u:
        return "slack"
    if "webhook.office.com" in u or "office365.com" in u:
        return "teams"
    return "generic"


def format_visitor_payload(platform: str) -> dict:
    ts = datetime.now()
    if platform == "discord":
        return {"embeds": [{"title": "🔔 New Website Visit (Test)", "color": 5763719, "fields": [{"name": "Device", "value": "Test Device", "inline": True}, {"name": "Time", "value": ts.strftime("%Y-%m-%d %H:%M:%S"), "inline": True}], "footer": {"text": "Test notification"}}]}
    if platform == "slack":
        return {"blocks": [{"type": "header", "text": {"type": "plain_text", "text": "🔔 New Website Visit (Test)", "emoji": True}}, {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Test at {ts.strftime('%Y-%m-%d %H:%M:%S')}"}]}]}
    if platform == "teams":
        return {"@type": "MessageCard", "@context": "http://schema.org/extensions", "summary": "Test Visit", "sections": [{"activityTitle": "🔔 New Website Visit (Test)", "text": "This is a test notification"}]}
    return {"event": "visitor", "test": True, "timestamp": ts.isoformat()}


def format_message_payload(platform: str) -> dict:
    ts = datetime.now()
    if platform == "discord":
        return {"embeds": [{"title": "📨 New Message (Test)", "color": 16776960, "fields": [{"name": "From", "value": "Test User", "inline": True}, {"name": "Email", "value": "test@example.com", "inline": True}, {"name": "Message", "value": "This is a test message."}], "footer": {"text": "Test notification"}}]}
    if platform == "slack":
        return {"blocks": [{"type": "header", "text": {"type": "plain_text", "text": "📨 New Message (Test)", "emoji": True}}, {"type": "section", "fields": [{"type": "mrkdwn", "text": "*From:*\nTest User"}, {"type": "mrkdwn", "text": "*Email:*\ntest@example.com"}]}]}
    if platform == "teams":
        return {"@type": "MessageCard", "@context": "http://schema.org/extensions", "summary": "Test Message", "sections": [{"activityTitle": "📨 New Message (Test)", "text": "This is a test message."}]}
    return {"event": "message", "test": True, "timestamp": ts.isoformat()}


router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.get("")
@require_admin
async def get_webhooks(request: Request, db: Session = Depends(get_db)):
    webhooks = db.query(Webhook).all()
    config = {
        "message": {"enabled": False, "url": ""},
        "visitor": {"enabled": False, "url": ""},
    }
    for w in webhooks:
        if w.name in config:
            config[w.name] = {"enabled": True, "url": w.url}
    return config


@router.post("")
@require_admin
async def save_webhooks(request: Request, data: dict = Body(...), db: Session = Depends(get_db)):
    try:
        db.query(Webhook).delete()
        for key in ("message", "visitor"):
            wh = data.get(key, {})
            if wh.get("enabled") and wh.get("url"):
                db.add(Webhook(id=uuid.uuid4(), name=key, url=wh["url"], created=datetime.now()))
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/{webhook_type}")
@require_admin
async def test_webhook(request: Request, webhook_type: str, data: dict = Body(...)):
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    platform = detect_platform(url)
    if webhook_type == "visitor":
        payload = format_visitor_payload(platform)
    elif webhook_type == "message":
        payload = format_message_payload(platform)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown webhook type: {webhook_type}")
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=5)
        if 200 <= r.status_code < 300:
            return {"status": "success", "platform": platform}
        raise HTTPException(status_code=400, detail=f"Webhook returned {r.status_code}: {r.text}")
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/detect-platform")
@require_admin
async def detect_platform_endpoint(request: Request, data: dict = Body(...)):
    url = data.get("url", "")
    return {"platform": detect_platform(url) if url else "unknown"}
