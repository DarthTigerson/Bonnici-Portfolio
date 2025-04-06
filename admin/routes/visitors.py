import os
import sys
import json
from datetime import datetime, timedelta
from typing import Annotated
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import requests
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import Entry
from .admin import require_admin

# Set up templates
templates = Jinja2Templates(directory="admin/templates")

# Add custom filter for JSON parsing
templates.env.filters["from_json"] = lambda x: json.loads(x) if x else {}

router = APIRouter(
    prefix="/visitors",
    tags=["visitors"],
)

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_location_info(ip_address):
    """Get location information for an IP address"""
    if not ip_address or ip_address == "127.0.0.1":
        return {
            "country": "Local",
            "city": "Local",
            "lat": None,
            "lon": None,
            "region": None,
            "timezone": None,
            "isp": None,
            "org": None,
            "as": None
        }
    
    try:
        # Use 8.8.8.8 (Google DNS) for testing when IP is localhost
        ip_to_query = "8.8.8.8" if ip_address == "127.0.0.1" else ip_address
        response = requests.get(f"http://ip-api.com/json/{ip_to_query}")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {
                    "country": data.get("country"),
                    "city": data.get("city"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon"),
                    "region": data.get("regionName"),
                    "timezone": data.get("timezone"),
                    "isp": data.get("isp"),
                    "org": data.get("org"),
                    "as": data.get("as")
                }
    except Exception as e:
        print(f"Error getting location for IP {ip_address}: {str(e)}")
    
    return {
        "country": "Unknown",
        "city": "Unknown",
        "lat": None,
        "lon": None,
        "region": None,
        "timezone": None,
        "isp": None,
        "org": None,
        "as": None
    }

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/")
@require_admin
async def visitors(request: Request, db: Session = Depends(get_db)):
    """Display visitor statistics"""
    # Get today's date at midnight
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    last_week = today - timedelta(days=7)
    
    # Total statistics
    total_unique_visitors = db.query(func.count(distinct(Entry.ip_address))).scalar()
    total_page_views = db.query(func.count(Entry.id)).scalar()
    
    # Today's statistics
    todays_unique_visitors = db.query(func.count(distinct(Entry.ip_address)))\
        .filter(Entry.created >= today)\
        .scalar()
    todays_page_views = db.query(func.count(Entry.id))\
        .filter(Entry.created >= today)\
        .scalar()
    
    # Last 7 days statistics
    weekly_unique_visitors = db.query(func.count(distinct(Entry.ip_address)))\
        .filter(Entry.created >= last_week)\
        .scalar()
    weekly_page_views = db.query(func.count(Entry.id))\
        .filter(Entry.created >= last_week)\
        .scalar()
    
    # Get the last 50 visitors with their details
    recent_visitors = db.query(Entry)\
        .order_by(Entry.created.desc())\
        .limit(50)\
        .all()
    
    # Get location data for each unique IP address
    unique_ips = {visitor.ip_address for visitor in recent_visitors if visitor.ip_address}
    ip_locations = {}
    
    # Use ThreadPoolExecutor to fetch location data concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        location_futures = {executor.submit(get_location_info, ip): ip for ip in unique_ips}
        for future in location_futures:
            ip = location_futures[future]
            ip_locations[ip] = future.result()
    
    # Add location data to visitors
    visitors_with_location = []
    for visitor in recent_visitors:
        visitor_data = {
            "id": str(visitor.id),
            "created": visitor.created,
            "device_info": visitor.device_info,
            "browser_info": visitor.browser_info,
            "ip_address": visitor.ip_address,
            "location": ip_locations.get(visitor.ip_address, {
                "country": "Unknown",
                "city": "Unknown",
                "region": "Unknown",
                "lat": None,
                "lon": None
            })
        }
        visitors_with_location.append(visitor_data)
    
    return templates.TemplateResponse(
        "visitors.html",
        {
            "request": request,
            "total_unique_visitors": total_unique_visitors,
            "total_page_views": total_page_views,
            "todays_unique_visitors": todays_unique_visitors,
            "todays_page_views": todays_page_views,
            "weekly_unique_visitors": weekly_unique_visitors,
            "weekly_page_views": weekly_page_views,
            "recent_visitors": visitors_with_location
        }
    )

@router.get("/details/{entry_id}")
@require_admin
async def get_visitor_details(request: Request, entry_id: UUID, db: Session = Depends(get_db)):
    """Get detailed information about a specific visitor entry"""
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Get location data
    location = get_location_info(entry.ip_address)
    
    # Parse JSON strings
    device_info = json.loads(entry.device_info) if entry.device_info else {}
    browser_info = json.loads(entry.browser_info) if entry.browser_info else {}
    system_info = json.loads(entry.system_info) if entry.system_info else {}
    display_info = json.loads(entry.display_info) if entry.display_info else {}
    
    return templates.TemplateResponse(
        "visitor_details.html",
        {
            "request": request,
            "entry": {
                "id": str(entry.id),
                "created": entry.created,
                "ip_address": entry.ip_address,
                "device_info": device_info,
                "browser_info": browser_info,
                "system_info": system_info,
                "display_info": display_info,
                "location": location
            }
        }
    )
