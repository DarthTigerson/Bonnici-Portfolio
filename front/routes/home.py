import os
import sys
import requests
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from front.models import ContactMessage

# Set up templates with the correct path
templates = Jinja2Templates(directory="front/templates")

# Discord webhook URL - ideally this should be moved to environment variables
webhook_url = "https://discord.com/api/webhooks/1356805711316779099/KebOTSaUK8gmlohsSdQ_94HCiBghMencrTPlODD_H_3fQ564ZMZFzRJv70rXSKbtEtbI"

router = APIRouter(
    prefix="",
    tags=["home"],
)

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/")
async def home(request: Request):
    """Render the home page"""
    return templates.TemplateResponse("home.html", {"request": request})


def send_discord_webhook(name: str, email: str, subject: str, message: str, ip_address: str):
    """Send notification to Discord webhook"""
    payload = {
        "content": f"New message from {name} ({email}):\nSubject: {subject}\nMessage: {message}\nIP Address: {ip_address}"
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 204
    except Exception as e:
        print(f"Discord webhook error: {str(e)}")
        return False


@router.post("/contact", response_class=HTMLResponse)
async def send_message(
    request: Request, 
    name: str = Form(...), 
    email: str = Form(...), 
    subject: str = Form(...), 
    message: str = Form(...), 
    db: Session = Depends(get_db)
):
    """Handle contact form submission"""
    try:
        # Get IP address
        ip_address = request.client.host if hasattr(request, "client") else None
        
        # Create contact message record
        contact_message = ContactMessage(
            archived=False,
            created=datetime.now(),
            email=email,
            fullname=name,
            ip_address=ip_address,
            message=message,
            subject=subject,
            viewed=False
        )
        
        # Save to database
        db.add(contact_message)
        db.commit()
        
        # Send Discord notification (won't fail form submission if it fails)
        send_discord_webhook(name, email, subject, message, ip_address)
        
        # Return success page
        return templates.TemplateResponse("success.html", {"request": request})
    except Exception as e:
        # Log the error
        print(f"Error saving contact message: {str(e)}")
        # Return to home page with error
        return templates.TemplateResponse("home.html", {"request": request, "error": "There was an error sending your message. Please try again later."})
    