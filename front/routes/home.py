import os
import sys
import requests
import json
from datetime import datetime
from typing import Annotated, Dict, Any, List

import user_agents

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import ContactMessage, Entry, Webhook
from config_manager import ConfigManager

# Global variable to store device info temporarily
device_info_cache = {}


def get_webhooks_by_type(db: Session, webhook_type: str) -> List[Webhook]:
    return db.query(Webhook).filter(Webhook.name == webhook_type).all()


def detect_webhook_platform(url: str) -> str:
    url_lower = url.lower()
    if "discord.com/api/webhooks" in url_lower:
        return "discord"
    elif "hooks.slack.com" in url_lower:
        return "slack"
    elif "webhook.office.com" in url_lower or "office365.com" in url_lower:
        return "teams"
    return "generic"


def get_ip_info(ip_address: str):
    if ip_address == "127.0.0.1":
        ip_address = "8.8.8.8"
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                return {
                    "country": data["country"],
                    "city": data["city"],
                    "region": data["regionName"],
                    "lat": data["lat"],
                    "lon": data["lon"],
                }
    except Exception as e:
        print(f"Error getting IP info: {e}")
    return None


def format_device_info(user_agent_str: str, device_info: Dict[Any, Any] = None) -> tuple:
    ua = user_agents.parse(user_agent_str)
    device_str = f"📱 Device: {ua.device.family}"
    if ua.device.brand and ua.device.model:
        device_str += f" ({ua.device.brand} {ua.device.model})"
    os_str = f"💻 OS: {ua.os.family} {ua.os.version_string}"
    browser_str = f"🌐 Browser: {ua.browser.family} {ua.browser.version_string}"

    resolution_parts = []
    if device_info and "screen" in device_info:
        screen = device_info["screen"]
        viewport = device_info.get("viewport", {})
        if screen.get("width") and screen.get("height"):
            resolution_parts.append(f"📺 Physical: {screen['width']}x{screen['height']}")
        if screen.get("availWidth") and screen.get("availHeight"):
            resolution_parts.append(f"🖥️ Available: {screen['availWidth']}x{screen['availHeight']}")
        if viewport.get("width") and viewport.get("height"):
            resolution_parts.append(f"🔍 Viewport: {viewport['width']}x{viewport['height']}")
        if screen.get("pixelRatio"):
            resolution_parts.append(f"📊 Pixel Ratio: {screen['pixelRatio']}")
        if screen.get("orientation") and isinstance(screen["orientation"], dict):
            orientation = screen["orientation"]
            resolution_parts.append(
                f"📱 Orientation: {orientation.get('type', 'unknown')} ({orientation.get('angle', '0')}°)"
            )
        resolution_str = "\n".join(resolution_parts)
    else:
        resolution_str = "📊 Resolution: Unknown"

    additional_info = []
    if device_info:
        if device_info.get("username") and device_info["username"] != "Unknown":
            additional_info.append(f"👤 Username: {device_info['username']}")
        if device_info.get("language"):
            additional_info.append(f"🌍 Language: {device_info['language']}")
        if device_info.get("deviceMemory"):
            additional_info.append(f"💾 Memory: {device_info['deviceMemory']}GB")
        if device_info.get("hardwareConcurrency"):
            additional_info.append(f"⚡ CPU Cores: {device_info['hardwareConcurrency']}")
        if device_info.get("connection"):
            conn = device_info["connection"]
            if conn.get("type"):
                additional_info.append(f"📡 Network: {conn['type']}")
            if conn.get("downlink"):
                additional_info.append(f"⬇️ Speed: {conn['downlink']} Mbps")
        if device_info.get("platformDetails"):
            pd = device_info["platformDetails"]
            if pd.get("platform") and pd.get("platformVersion"):
                additional_info.append(f"🖥️ Platform: {pd['platform']} {pd['platformVersion']}")
            if pd.get("architecture"):
                additional_info.append(f"🔧 Architecture: {pd['architecture']}")

    return device_str, os_str, browser_str, resolution_str, additional_info


def send_message_webhook(name: str, email: str, subject: str, message: str, ip_address: str, db: Session):
    webhooks = get_webhooks_by_type(db, "message")
    if not webhooks:
        return False

    ip_info = get_ip_info(ip_address)
    timestamp = datetime.now()
    success = False

    for webhook in webhooks:
        platform = detect_webhook_platform(webhook.url)

        if platform == "discord":
            fields = [
                {"name": "📧  Email", "value": f"```{email}```", "inline": True},
                {"name": "📝  Subject", "value": f"```fix\n{subject}```", "inline": True},
                {"name": "💬  Message", "value": f"```fix\n{message}```"},
            ]
            if ip_info:
                location_str = f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"
                fields.extend([
                    {"name": "🌐  IP Address", "value": f"```yaml\n{ip_address}```", "inline": True},
                    {"name": "📍  Location", "value": f"```yaml\n{location_str}```", "inline": True},
                ])
                image = {"url": f"https://static-maps.yandex.ru/1.x/?ll={ip_info['lon']},{ip_info['lat']}&size=650,400&z=11&l=map&pt={ip_info['lon']},{ip_info['lat']},pm2rdm1"}
            else:
                fields.append({"name": "🌐  IP Address", "value": f"```yaml\n{ip_address}```", "inline": True})
                image = None
            payload = {"embeds": [{"title": f"📨  New Message from {name}", "color": 16776960, "fields": fields, "footer": {"text": "Portfolio Contact Form • Powered by IP-API"}, "timestamp": timestamp.isoformat()}]}
            if image:
                payload["embeds"][0]["image"] = image

        elif platform == "slack":
            blocks = [
                {"type": "header", "text": {"type": "plain_text", "text": f"📨 New Message from {name}", "emoji": True}},
                {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Email:*\n{email}"}, {"type": "mrkdwn", "text": f"*Subject:*\n{subject}"}]},
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Message:*\n>{message}"}},
            ]
            if ip_info:
                location_str = f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"
                blocks.append({"type": "section", "fields": [{"type": "mrkdwn", "text": f"*IP Address:*\n{ip_address}"}, {"type": "mrkdwn", "text": f"*Location:*\n{location_str}"}]})
                blocks.append({"type": "image", "title": {"type": "plain_text", "text": "Location Map", "emoji": True}, "image_url": f"https://static-maps.yandex.ru/1.x/?ll={ip_info['lon']},{ip_info['lat']}&size=600,300&z=11&l=map&pt={ip_info['lon']},{ip_info['lat']},pm2rdm1&lang=en", "alt_text": "Map showing visitor location"})
            else:
                blocks.append({"type": "section", "fields": [{"type": "mrkdwn", "text": f"*IP Address:*\n{ip_address}"}]})
            blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": f"Sent at: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"}]})
            payload = {"blocks": blocks}

        elif platform == "teams":
            facts = [{"name": "Email", "value": email}, {"name": "Subject", "value": subject}]
            if ip_info:
                facts.extend([{"name": "IP Address", "value": ip_address}, {"name": "Location", "value": f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"}])
            else:
                facts.append({"name": "IP Address", "value": ip_address})
            payload = {"@type": "MessageCard", "@context": "http://schema.org/extensions", "themeColor": "0078D7", "summary": f"New message from {name}", "sections": [{"activityTitle": f"📨 New Message from {name}", "facts": facts, "text": message}]}

        else:
            payload = {"event": "message", "data": {"timestamp": timestamp.isoformat(), "fullname": name, "email": email, "subject": subject, "message": message, "ip_address": ip_address}}
            if ip_info:
                payload["data"]["location"] = {"city": ip_info["city"], "region": ip_info["region"], "country": ip_info["country"], "coordinates": {"lat": ip_info["lat"], "lon": ip_info["lon"]}}

        try:
            r = requests.post(webhook.url, json=payload, headers={"Content-Type": "application/json"}, timeout=5)
            if 200 <= r.status_code < 300:
                success = True
        except Exception as e:
            print(f"Error sending message webhook: {e}")

    return success


def send_visitor_webhook(request: Request, db: Session):
    try:
        webhooks = get_webhooks_by_type(db, "visitor")
        ip_address = request.client.host if hasattr(request, "client") else None
        user_agent_str = request.headers.get("user-agent", "Unknown Browser")
        device_info = device_info_cache.get(ip_address)
        ip_info = get_ip_info(ip_address)
        device_str, os_str, browser_str, resolution_str, additional_info = format_device_info(user_agent_str, device_info)

        entry = Entry(
            device_info=json.dumps({"device": device_str, "os": os_str}),
            display_info=json.dumps({"resolution": resolution_str}),
            system_info=json.dumps({"additional": additional_info}),
            browser_info=json.dumps({"browser": browser_str, "user_agent": user_agent_str}),
            ip_address=ip_address,
        )
        db.add(entry)
        db.commit()

        if not webhooks or ip_address == "127.0.0.1":
            device_info_cache.pop(ip_address, None)
            return

        bot_keywords = ["bot", "crawler", "spider", "headless", "phantomjs", "selenium", "puppeteer", "playwright"]
        if any(k in user_agent_str.lower() for k in bot_keywords):
            device_info_cache.pop(ip_address, None)
            return

        timestamp = datetime.now()
        for webhook in webhooks:
            platform = detect_webhook_platform(webhook.url)

            if platform == "discord":
                fields = [
                    {"name": "Device Information", "value": f"```yaml\n{device_str}\n{os_str}\n{browser_str}```", "inline": False},
                    {"name": "Display", "value": f"```yaml\n{resolution_str}```", "inline": False},
                ]
                if additional_info:
                    fields.append({"name": "System Info", "value": f"```yaml\n{chr(10).join(additional_info)}```", "inline": False})
                if ip_info:
                    location_str = f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"
                    fields.extend([{"name": "🔍  IP Address", "value": f"```yaml\n{ip_address}```", "inline": True}, {"name": "📍  Location", "value": f"```yaml\n{location_str}```", "inline": True}])
                    image = {"url": f"https://static-maps.yandex.ru/1.x/?ll={ip_info['lon']},{ip_info['lat']}&size=650,400&z=11&l=map&pt={ip_info['lon']},{ip_info['lat']},pm2rdm1&lang=en"}
                else:
                    fields.append({"name": "🔍  IP Address", "value": f"```yaml\n{ip_address}```", "inline": True})
                    image = None
                payload = {"embeds": [{"title": "🔔  New Website Visit", "description": f"```Entry ID: {entry.id}```", "color": 5763719, "fields": fields, "footer": {"text": "Portfolio Website • Powered by IP-API"}, "timestamp": timestamp.isoformat()}]}
                if image:
                    payload["embeds"][0]["image"] = image

            elif platform == "slack":
                blocks = [
                    {"type": "header", "text": {"type": "plain_text", "text": "🔔 New Website Visit", "emoji": True}},
                    {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Device:*\n{device_str}"}, {"type": "mrkdwn", "text": f"*OS:*\n{os_str}"}]},
                    {"type": "section", "fields": [{"type": "mrkdwn", "text": f"*Browser:*\n{browser_str}"}]},
                    {"type": "section", "text": {"type": "mrkdwn", "text": f"*Display:*\n{resolution_str.replace(chr(10), ', ')}"}},
                ]
                if ip_info:
                    location_str = f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"
                    blocks.append({"type": "section", "fields": [{"type": "mrkdwn", "text": f"*IP Address:*\n{ip_address}"}, {"type": "mrkdwn", "text": f"*Location:*\n{location_str}"}]})
                    blocks.append({"type": "image", "title": {"type": "plain_text", "text": "Location Map", "emoji": True}, "image_url": f"https://static-maps.yandex.ru/1.x/?ll={ip_info['lon']},{ip_info['lat']}&size=600,300&z=11&l=map&pt={ip_info['lon']},{ip_info['lat']},pm2rdm1&lang=en", "alt_text": "Map showing visitor location"})
                else:
                    blocks.append({"type": "section", "fields": [{"type": "mrkdwn", "text": f"*IP Address:*\n{ip_address}"}]})
                blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": f"Visited at: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"}]})
                payload = {"blocks": blocks}

            elif platform == "teams":
                facts = [{"name": "Device", "value": device_str}, {"name": "OS", "value": os_str}, {"name": "Browser", "value": browser_str}]
                if ip_info:
                    facts.extend([{"name": "IP Address", "value": ip_address}, {"name": "Location", "value": f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"}])
                else:
                    facts.append({"name": "IP Address", "value": ip_address})
                payload = {"@type": "MessageCard", "@context": "http://schema.org/extensions", "themeColor": "0078D7", "summary": "New Website Visit", "sections": [{"activityTitle": "🔔 New Website Visit", "facts": facts, "text": f"Display: {resolution_str.replace(chr(10), ', ')}"}]}

            else:
                payload = {"event": "visitor", "data": {"id": str(entry.id), "timestamp": timestamp.isoformat(), "device_info": device_str, "browser_info": browser_str, "system_info": os_str, "display_info": resolution_str, "ip_address": ip_address}}
                if ip_info:
                    payload["data"]["location"] = {"city": ip_info["city"], "region": ip_info["region"], "country": ip_info["country"], "coordinates": {"lat": ip_info["lat"], "lon": ip_info["lon"]}}

            try:
                r = requests.post(webhook.url, json=payload, headers={"Content-Type": "application/json"}, timeout=5)
                print(f"Visitor webhook {'sent' if 200 <= r.status_code < 300 else 'failed'}: {platform} {r.status_code}")
            except Exception as e:
                print(f"Error sending visitor webhook: {e}")

        device_info_cache.pop(ip_address, None)

    except Exception as e:
        print(f"Error in send_visitor_webhook: {e}")


router = APIRouter(prefix="/api", tags=["api"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.get("/config")
async def get_config(request: Request, db: Session = Depends(get_db)):
    """Return portfolio config as JSON and log the visit."""
    try:
        config = ConfigManager.read_config()
        try:
            send_visitor_webhook(request, db)
        except Exception as e:
            print(f"Error in visitor webhook: {e}")
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return JSONResponse(status_code=500, content={"detail": str(e)})


@router.post("/contact")
async def send_message(request: Request, db: Session = Depends(get_db)):
    """Handle contact form submission (accepts JSON body)."""
    try:
        body = await request.json()
        fullname = body.get("fullname", "")
        email = body.get("email", "")
        subject = body.get("subject", "")
        message = body.get("message", "")
        if not all([fullname, email, subject, message]):
            return JSONResponse(status_code=400, content={"detail": "All fields are required."})
        ip_address = request.client.host if hasattr(request, "client") else None
        contact_message = ContactMessage(
            archived=False,
            created=datetime.now(),
            email=email,
            fullname=fullname,
            ip_address=ip_address,
            message=message,
            subject=subject,
            viewed=False,
        )
        db.add(contact_message)
        db.commit()
        send_message_webhook(fullname, email, subject, message, ip_address, db)
        return {"status": "success"}
    except Exception as e:
        print(f"Error saving contact message: {e}")
        return JSONResponse(status_code=500, content={"detail": "Failed to send message. Please try again."})


@router.post("/device-info")
async def device_info(request: Request):
    """Cache client-side device info for enriching visitor webhook."""
    try:
        info = await request.json()
        ip_address = request.client.host if hasattr(request, "client") else None
        if ip_address:
            device_info_cache[ip_address] = info
        return {"status": "success"}
    except Exception as e:
        print(f"Error handling device info: {e}")
        return {"status": "error"}
