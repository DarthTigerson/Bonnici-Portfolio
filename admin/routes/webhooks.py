import os
import sys
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, Body
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session
import requests
import uuid

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import Webhook
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

def get_webhook_config(db: Session):
    """Get the webhook configuration"""
    return db.query(Webhook).all()

router = APIRouter(
    prefix="/webhooks",
    tags=["webhooks"],
)

@router.get("/")
@require_admin
async def webhooks_page(request: Request, db: Session = Depends(get_db)):
    webhook_config = get_webhook_config(db)
    
    return templates.TemplateResponse(
        "webhooks.html",
        {
            "request": request,
            "webhook_config": webhook_config
        }
    )

@router.post("/save")
@require_admin
async def save_webhooks(request: Request, data: dict = Body(...), db: Session = Depends(get_db)):
    try:
        # Get webhooks from request
        webhooks = data.get("webhooks", [])
        
        # Delete existing webhooks
        db.query(Webhook).delete()
        
        # Create new webhook entries for enabled webhooks
        for webhook in webhooks:
            if webhook.get("enabled", False):
                name = webhook.get("name")
                url = webhook.get("url")
                
                if not name or not url:
                    continue
                
                new_webhook = Webhook(
                    id=uuid.uuid4(),
                    name=name,
                    url=url,
                    created=datetime.now()
                )
                db.add(new_webhook)
        
        db.commit()
        return {"status": "success", "message": "Webhook settings saved successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save webhook settings: {str(e)}")

@router.post("/test/{webhook_type}")
@require_admin
async def test_webhook(request: Request, webhook_type: str, data: dict = Body(...), db: Session = Depends(get_db)):
    try:
        url = data.get("url")
        
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        # Detect webhook platform
        platform = detect_webhook_platform(url)
        
        # Prepare test data based on webhook type and platform
        if webhook_type == "visitor":
            test_data = format_visitor_webhook(platform)
        elif webhook_type == "message":
            test_data = format_message_webhook(platform)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown webhook type: {webhook_type}")
        
        # Send test webhook
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        # Check response
        if response.status_code >= 200 and response.status_code < 300:
            return {"status": "success", "message": f"Test webhook sent successfully", "platform": platform}
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Webhook endpoint returned status {response.status_code}: {response.text}"
            )
    
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to send webhook: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test webhook: {str(e)}")

def detect_webhook_platform(url):
    """Detect the webhook platform based on URL patterns"""
    url_lower = url.lower()
    
    if "discord.com/api/webhooks" in url_lower:
        return "discord"
    elif "hooks.slack.com" in url_lower:
        return "slack"
    elif "webhook.office.com" in url_lower or "office365.com" in url_lower:
        return "teams"
    else:
        return "generic"

def format_visitor_webhook(platform):
    """Format visitor webhook data based on the platform"""
    timestamp = datetime.now()
    visitor_id = str(uuid.uuid4())
    
    # Generic data that will be transformed based on platform
    visitor_data = {
        "id": visitor_id,
        "timestamp": timestamp.isoformat(),
        "device_info": "Test Device",
        "browser_info": "Test Browser",
        "system_info": "Test System",
        "display_info": "Test Display",
        "ip_address": "127.0.0.1",
        "is_test": True
    }
    
    if platform == "discord":
        return {
            "content": "🔍 New Site Visitor Detected",
            "embeds": [{
                "title": "Visitor Information (Test)",
                "color": 3447003,  # Blue color
                "fields": [
                    {"name": "Device", "value": "Test Device", "inline": True},
                    {"name": "Browser", "value": "Test Browser", "inline": True},
                    {"name": "System", "value": "Test System", "inline": True},
                    {"name": "Time", "value": timestamp.strftime("%Y-%m-%d %H:%M:%S"), "inline": False}
                ],
                "footer": {"text": "This is a test notification"}
            }]
        }
    
    elif platform == "slack":
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍 New Site Visitor Detected (Test)",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Device:*\nTest Device"},
                        {"type": "mrkdwn", "text": "*Browser:*\nTest Browser"},
                        {"type": "mrkdwn", "text": "*System:*\nTest System"},
                        {"type": "mrkdwn", "text": "*Time:*\n" + timestamp.strftime("%Y-%m-%d %H:%M:%S")}
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": "This is a test notification"}
                    ]
                }
            ]
        }
    
    elif platform == "teams":
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": "New Site Visitor",
            "sections": [{
                "activityTitle": "🔍 New Site Visitor Detected (Test)",
                "facts": [
                    {"name": "Device", "value": "Test Device"},
                    {"name": "Browser", "value": "Test Browser"},
                    {"name": "System", "value": "Test System"},
                    {"name": "Time", "value": timestamp.strftime("%Y-%m-%d %H:%M:%S")},
                ],
                "text": "This is a test notification"
            }]
        }
    
    else:  # generic
        return {
            "event": "visitor",
            "data": visitor_data
        }

def format_message_webhook(platform):
    """Format message webhook data based on the platform"""
    timestamp = datetime.now()
    message_id = str(uuid.uuid4())
    
    # Generic data that will be transformed based on platform
    message_data = {
        "id": message_id,
        "timestamp": timestamp.isoformat(),
        "fullname": "Test User",
        "email": "test@example.com",
        "subject": "Test Subject",
        "message": "This is a test message from your webhook configuration page.",
        "ip_address": "127.0.0.1",
        "is_test": True
    }
    
    if platform == "discord":
        return {
            "content": "💬 New Message Received",
            "embeds": [{
                "title": "Message Details (Test)",
                "color": 5431,  # Green color
                "fields": [
                    {"name": "From", "value": "Test User", "inline": True},
                    {"name": "Email", "value": "test@example.com", "inline": True},
                    {"name": "Subject", "value": "Test Subject", "inline": False},
                    {"name": "Message", "value": "This is a test message from your webhook configuration page.", "inline": False},
                    {"name": "Time", "value": timestamp.strftime("%Y-%m-%d %H:%M:%S"), "inline": False}
                ],
                "footer": {"text": "This is a test notification"}
            }]
        }
    
    elif platform == "slack":
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "💬 New Message Received (Test)",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*From:*\nTest User"},
                        {"type": "mrkdwn", "text": "*Email:*\ntest@example.com"},
                        {"type": "mrkdwn", "text": "*Subject:*\nTest Subject"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Message:*\nThis is a test message from your webhook configuration page."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": "Received at: " + timestamp.strftime("%Y-%m-%d %H:%M:%S")}
                    ]
                }
            ]
        }
    
    elif platform == "teams":
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": "New Message Received",
            "sections": [{
                "activityTitle": "💬 New Message Received (Test)",
                "facts": [
                    {"name": "From", "value": "Test User"},
                    {"name": "Email", "value": "test@example.com"},
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "Time", "value": timestamp.strftime("%Y-%m-%d %H:%M:%S")},
                ],
                "text": "**Message:**\n\nThis is a test message from your webhook configuration page."
            }]
        }
    
    else:  # generic
        return {
            "event": "message",
            "data": message_data
        }

@router.post("/detect-platform")
@require_admin
async def detect_platform(request: Request, data: dict = Body(...)):
    """Detect the webhook platform from a URL"""
    url = data.get("url", "")
    if not url:
        return {"platform": "unknown"}
    
    platform = detect_webhook_platform(url)
    return {"platform": platform}