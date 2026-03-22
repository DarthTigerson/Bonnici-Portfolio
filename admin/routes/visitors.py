import os
import sys
import json
from datetime import datetime, timedelta
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request, HTTPException
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import Entry
from .admin import require_admin


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_location_info(ip_address: str) -> dict:
    if not ip_address or ip_address == "127.0.0.1":
        return {"country": "Local", "city": "Local"}
    try:
        r = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
        if r.status_code == 200:
            data = r.json()
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
                }
    except Exception as e:
        print(f"Error getting location for {ip_address}: {e}")
    return {"country": "Unknown", "city": "Unknown"}


router = APIRouter(prefix="/api/visitors", tags=["visitors"])


@router.get("")
@require_admin
async def get_visitors(request: Request, db: Session = Depends(get_db)):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    last_week = today - timedelta(days=7)

    total_unique = db.query(func.count(distinct(Entry.ip_address))).scalar()
    total_views = db.query(func.count(Entry.id)).scalar()
    today_unique = db.query(func.count(distinct(Entry.ip_address))).filter(Entry.created >= today).scalar()
    today_views = db.query(func.count(Entry.id)).filter(Entry.created >= today).scalar()
    last7_unique = db.query(func.count(distinct(Entry.ip_address))).filter(Entry.created >= last_week).scalar()
    last7_views = db.query(func.count(Entry.id)).filter(Entry.created >= last_week).scalar()

    recent = db.query(Entry).order_by(Entry.created.desc()).limit(200).all()
    unique_ips = {v.ip_address for v in recent if v.ip_address}

    ip_locations: dict = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_location_info, ip): ip for ip in unique_ips}
        for future, ip in futures.items():
            ip_locations[ip] = future.result()

    visitors_out = []
    for v in recent:
        loc = ip_locations.get(v.ip_address, {})
        di = json.loads(v.device_info) if v.device_info else {}
        bi = json.loads(v.browser_info) if v.browser_info else {}
        si = json.loads(v.system_info) if v.system_info else {}
        dsi = json.loads(v.display_info) if v.display_info else {}
        visitors_out.append({
            "id": str(v.id),
            "created": v.created.isoformat(),
            "ip_address": v.ip_address,
            "device_info": di,
            "browser_info": bi,
            "system_info": si,
            "display_info": dsi,
            **loc,
        })

    return {
        "total_unique": total_unique,
        "total_views": total_views,
        "today_unique": today_unique,
        "today_views": today_views,
        "last7_unique": last7_unique,
        "last7_views": last7_views,
        "visitors": visitors_out,
    }


@router.get("/{entry_id}")
@require_admin
async def get_visitor(request: Request, entry_id: UUID, db: Session = Depends(get_db)):
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    loc = get_location_info(entry.ip_address)
    return {
        "id": str(entry.id),
        "created": entry.created.isoformat(),
        "ip_address": entry.ip_address,
        "device_info": json.loads(entry.device_info) if entry.device_info else {},
        "browser_info": json.loads(entry.browser_info) if entry.browser_info else {},
        "system_info": json.loads(entry.system_info) if entry.system_info else {},
        "display_info": json.loads(entry.display_info) if entry.display_info else {},
        **loc,
    }
