import os
import sys
import requests
import json
from datetime import datetime
from typing import Annotated, Dict, Any, Optional, List
import user_agents

from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import ContactMessage, Entry, Webhook
from config_manager import ConfigManager

# Set up templates with the correct path
templates = Jinja2Templates(directory="front/templates")

# Global variable to store device info temporarily
device_info_cache = {}

def get_webhooks_by_type(db: Session, webhook_type: str) -> List[Webhook]:
    """Get all enabled webhooks of a specific type from the database"""
    # Only return webhooks that are configured and enabled
    return db.query(Webhook).filter(Webhook.name == webhook_type).all()

def detect_webhook_platform(url: str) -> str:
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

def get_ip_info(ip_address: str):
    """Get geolocation information for an IP address"""
    # For testing purposes, use a known IP when localhost is detected
    if ip_address == "127.0.0.1":
        ip_address = "8.8.8.8"  # Google's DNS server for testing
        
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                return {
                    "country": data["country"],
                    "city": data["city"],
                    "region": data["regionName"],
                    "lat": data["lat"],
                    "lon": data["lon"]
                }
    except Exception as e:
        print(f"Error getting IP info: {str(e)}")
    return None

def get_map_url(lat: float, lon: float) -> str:
    """Generate a static map URL for the given coordinates"""
    return f"https://www.openstreetmap.org/export/embed.html?bbox={lon-0.1}%2C{lat-0.1}%2C{lon+0.1}%2C{lat+0.1}&layer=mapnik&marker={lat}%2C{lon}"

def format_device_info(user_agent_str: str, device_info: Dict[Any, Any] = None) -> tuple:
    """Format device information for Discord message"""
    # Parse user agent
    user_agent = user_agents.parse(user_agent_str)
    
    # Basic device info
    device_str = f"📱 Device: {user_agent.device.family}"
    if user_agent.device.brand and user_agent.device.model:
        device_str += f" ({user_agent.device.brand} {user_agent.device.model})"
    
    # OS info
    os_str = f"💻 OS: {user_agent.os.family} {user_agent.os.version_string}"
    
    # Browser info
    browser_str = f"🌐 Browser: {user_agent.browser.family} {user_agent.browser.version_string}"
    
    # Screen resolution
    resolution_parts = []
    if device_info and 'screen' in device_info:
        screen = device_info['screen']
        viewport = device_info.get('viewport', {})
        
        # Physical screen size
        if screen.get('width') and screen.get('height'):
            resolution_parts.append(f"📺 Physical: {screen['width']}x{screen['height']}")
        
        # Available screen size
        if screen.get('availWidth') and screen.get('availHeight'):
            resolution_parts.append(f"🖥️ Available: {screen['availWidth']}x{screen['availHeight']}")
        
        # Viewport size
        if viewport.get('width') and viewport.get('height'):
            resolution_parts.append(f"🔍 Viewport: {viewport['width']}x{viewport['height']}")
        
        # Additional screen info
        if screen.get('pixelRatio'):
            resolution_parts.append(f"📊 Pixel Ratio: {screen['pixelRatio']}")
        
        if screen.get('orientation') and isinstance(screen['orientation'], dict):
            orientation = screen['orientation']
            resolution_parts.append(f"📱 Orientation: {orientation.get('type', 'unknown')} ({orientation.get('angle', '0')}°)")
        
        resolution_str = "\n".join(resolution_parts)
    else:
        resolution_str = "📊 Resolution: Unknown"
    
    # Additional info
    additional_info = []
    if device_info:
        if device_info.get('username') and device_info['username'] != 'Unknown':
            additional_info.append(f"👤 Username: {device_info['username']}")
        
        if device_info.get('language'):
            additional_info.append(f"🌍 Language: {device_info['language']}")
        
        if device_info.get('deviceMemory'):
            additional_info.append(f"💾 Memory: {device_info['deviceMemory']}GB")
        
        if device_info.get('hardwareConcurrency'):
            additional_info.append(f"⚡ CPU Cores: {device_info['hardwareConcurrency']}")
        
        # Connection info
        if device_info.get('connection'):
            conn = device_info['connection']
            if conn.get('type'):
                additional_info.append(f"📡 Network: {conn['type']}")
            if conn.get('downlink'):
                additional_info.append(f"⬇️ Speed: {conn['downlink']} Mbps")
        
        # Platform details from high entropy values
        if device_info.get('platformDetails'):
            pd = device_info['platformDetails']
            if pd.get('platform') and pd.get('platformVersion'):
                additional_info.append(f"🖥️ Platform: {pd['platform']} {pd['platformVersion']}")
            if pd.get('architecture'):
                additional_info.append(f"🔧 Architecture: {pd['architecture']}")
    
    return device_str, os_str, browser_str, resolution_str, additional_info

def send_message_webhook(name: str, email: str, subject: str, message: str, ip_address: str, db: Session):
    """Send notification to configured message webhooks"""
    # Get message webhooks from database
    webhooks = get_webhooks_by_type(db, "message")
    if not webhooks:
        print("No message webhooks configured or enabled")
        return False
    
    # Get IP geolocation
    ip_info = get_ip_info(ip_address)
    timestamp = datetime.now()
    
    # Send to all configured webhooks
    success = False
    
    for webhook in webhooks:
        # Detect platform
        platform = detect_webhook_platform(webhook.url)
        
        if platform == "discord":
            # Discord format
            # Base fields
            fields = [
                {
                    "name": "📧  Email",
                    "value": f"```{email}```",
                    "inline": True
                },
                {
                    "name": "📝  Subject",
                    "value": f"```fix\n{subject}```",
                    "inline": True
                },
                {
                    "name": "💬  Message",
                    "value": f"```fix\n{message}```"
                }
            ]
            
            # Add IP and location information
            if ip_info:
                location_str = f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"
                
                fields.extend([
                    {
                        "name": "🌐  IP Address",
                        "value": f"```yaml\n{ip_address}```",
                        "inline": True
                    },
                    {
                        "name": "📍  Location",
                        "value": f"```yaml\n{location_str}```",
                        "inline": True
                    }
                ])
                
                # Using a larger map as the main image
                image = {
                    "url": f"https://static-maps.yandex.ru/1.x/?ll={ip_info['lon']},{ip_info['lat']}&size=650,400&z=11&l=map&pt={ip_info['lon']},{ip_info['lat']},pm2rdm1"
                }
            else:
                fields.append({
                    "name": "🌐  IP Address",
                    "value": f"```yaml\n{ip_address}```",
                    "inline": True
                })
                image = None
            
            payload = {
                "embeds": [{
                    "title": f"📨  New Message from {name}",
                    "color": 16776960,  # Discord yellow color
                    "fields": fields,
                    "footer": {
                        "text": "Portfolio Contact Form • Powered by IP-API",
                        "icon_url": "https://www.google.com/s2/favicons?domain=ip-api.com&sz=128"
                    },
                    "timestamp": timestamp.isoformat()
                }]
            }
            
            # Add image if we have location data
            if image:
                payload["embeds"][0]["image"] = image
        
        elif platform == "slack":
            # Slack format
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📨 New Message from {name}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Email:*\n{email}"},
                        {"type": "mrkdwn", "text": f"*Subject:*\n{subject}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Message:*\n>{message}"
                    }
                }
            ]
            
            # Add IP and location if available
            if ip_info:
                location_str = f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"
                blocks.append({
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*IP Address:*\n{ip_address}"},
                        {"type": "mrkdwn", "text": f"*Location:*\n{location_str}"}
                    ]
                })
                
                # Add map image
                blocks.append({
                    "type": "image",
                    "title": {
                        "type": "plain_text",
                        "text": "Location Map",
                        "emoji": True
                    },
                    "image_url": f"https://static-maps.yandex.ru/1.x/?ll={ip_info['lon']},{ip_info['lat']}&size=600,300&z=11&l=map&pt={ip_info['lon']},{ip_info['lat']},pm2rdm1&lang=en",
                    "alt_text": "Map showing visitor location"
                })
            else:
                blocks.append({
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*IP Address:*\n{ip_address}"}
                    ]
                })
            
            # Add timestamp
            blocks.append({
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Sent at: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"}
                ]
            })
            
            payload = {"blocks": blocks}
            
        elif platform == "teams":
            # Microsoft Teams format
            facts = [
                {"name": "Email", "value": email},
                {"name": "Subject", "value": subject}
            ]
            
            if ip_info:
                location_str = f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"
                facts.extend([
                    {"name": "IP Address", "value": ip_address},
                    {"name": "Location", "value": location_str}
                ])
            else:
                facts.append({"name": "IP Address", "value": ip_address})
            
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0078D7",
                "summary": f"New message from {name}",
                "sections": [
                    {
                        "activityTitle": f"📨 New Message from {name}",
                        "facts": facts,
                        "text": message
                    }
                ]
            }
            
        else:
            # Generic format
            payload = {
                "event": "message",
                "data": {
                    "timestamp": timestamp.isoformat(),
                    "fullname": name,
                    "email": email,
                    "subject": subject,
                    "message": message,
                    "ip_address": ip_address
                }
            }
            
            if ip_info:
                payload["data"]["location"] = {
                    "city": ip_info["city"],
                    "region": ip_info["region"],
                    "country": ip_info["country"],
                    "coordinates": {
                        "lat": ip_info["lat"],
                        "lon": ip_info["lon"]
                    }
                }
        
        # Send webhook
        try:
            response = requests.post(
                webhook.url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                success = True
                print(f"Successfully sent message webhook to {platform} platform")
            else:
                print(f"Failed to send message webhook to {platform}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error sending message webhook to {platform}: {str(e)}")
    
    return success

def send_visitor_webhook(request: Request, db: Session):
    """Send notification when someone visits the website and save to database"""
    try:
        # Get visitor webhooks from database
        webhooks = get_webhooks_by_type(db, "visitor")
        
        # Get IP address and user agent
        ip_address = request.client.host if hasattr(request, "client") else None
        user_agent_str = request.headers.get("user-agent", "Unknown Browser")
        
        # Get device info from cache if available
        device_info = device_info_cache.get(ip_address)
        
        # Get IP geolocation
        ip_info = get_ip_info(ip_address)
        
        # Format device information
        device_str, os_str, browser_str, resolution_str, additional_info = format_device_info(user_agent_str, device_info)
        
        # Create database entry
        entry = Entry(
            device_info=json.dumps({
                "device": device_str,
                "os": os_str
            }),
            display_info=json.dumps({
                "resolution": resolution_str
            }),
            system_info=json.dumps({
                "additional": additional_info
            }),
            browser_info=json.dumps({
                "browser": browser_str,
                "user_agent": user_agent_str
            }),
            ip_address=ip_address
        )
        
        # Save to database
        db.add(entry)
        db.commit()
        
        # If no webhooks or localhost, skip sending webhook but keep database entry
        if not webhooks:
            print("No visitor webhooks configured or enabled")
            # Clear device info from cache
            if ip_address in device_info_cache:
                del device_info_cache[ip_address]
            return
            
        # Skip sending webhook for localhost (127.0.0.1)
        if ip_address == "127.0.0.1":
            print("Skipping webhook for localhost entry")
            # Clear device info from cache
            if ip_address in device_info_cache:
                del device_info_cache[ip_address]
            return
        
        # Skip sending webhook for bots and scrapers
        is_bot = False
        
        # Check for common bot indicators in user agent
        bot_keywords = ["bot", "crawler", "spider", "headless", "phantomjs", "selenium", "puppeteer", "playwright"]
        if any(keyword in user_agent_str.lower() for keyword in bot_keywords):
            is_bot = True
            print(f"Skipping webhook for bot/scraper: {user_agent_str}")
        
        # Check device type from device info
        if device_info and 'device' in device_info:
            device_type = device_info['device'].lower()
            if device_type == "other" or "bot" in device_type:
                is_bot = True
                print(f"Skipping webhook for non-standard device: {device_type}")
        
        # Check browser from device info
        if device_info and 'browser' in device_info:
            browser = device_info['browser'].lower()
            if "headless" in browser or "bot" in browser:
                is_bot = True
                print(f"Skipping webhook for headless/bot browser: {browser}")
        
        # If it's a bot, skip the webhook
        if is_bot:
            # Clear device info from cache
            if ip_address in device_info_cache:
                del device_info_cache[ip_address]
            return
        
        timestamp = datetime.now()
        
        # Send to all configured webhooks
        for webhook in webhooks:
            # Detect platform
            platform = detect_webhook_platform(webhook.url)
            
            if platform == "discord":
                # Discord format
                # Base fields with device information
                fields = [
                    {
                        "name": "Device Information",
                        "value": f"```yaml\n{device_str}\n{os_str}\n{browser_str}```",
                        "inline": False
                    },
                    {
                        "name": "Display",
                        "value": f"```yaml\n{resolution_str}```",
                        "inline": False
                    }
                ]
                
                # Add additional device info if available
                if additional_info:
                    fields.append({
                        "name": "System Info",
                        "value": f"```yaml\n{chr(10).join(additional_info)}```",
                        "inline": False
                    })
                
                # Add IP and location information
                if ip_info:
                    location_str = f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"
                    fields.extend([
                        {
                            "name": "🔍  IP Address",
                            "value": f"```yaml\n{ip_address}```",
                            "inline": True
                        },
                        {
                            "name": "📍  Location",
                            "value": f"```yaml\n{location_str}```",
                            "inline": True
                        }
                    ])
                    
                    # Add map as main image with English language parameter
                    image = {
                        "url": f"https://static-maps.yandex.ru/1.x/?ll={ip_info['lon']},{ip_info['lat']}&size=650,400&z=11&l=map&pt={ip_info['lon']},{ip_info['lat']},pm2rdm1&lang=en"
                    }
                else:
                    fields.append({
                        "name": "🔍  IP Address",
                        "value": f"```yaml\n{ip_address}```",
                        "inline": True
                    })
                    image = None
                
                payload = {
                    "embeds": [{
                        "title": "🔔  New Website Visit",
                        "description": f"```Entry ID: {entry.id}```",
                        "color": 5763719,  # Green color (0x57F607 in decimal)
                        "fields": fields,
                        "footer": {
                            "text": "Portfolio Website • Powered by IP-API",
                            "icon_url": "https://www.google.com/s2/favicons?domain=ip-api.com&sz=128"
                        },
                        "timestamp": timestamp.isoformat()
                    }]
                }
                
                # Add image if we have location data
                if image:
                    payload["embeds"][0]["image"] = image
            
            elif platform == "slack":
                # Slack format
                blocks = [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🔔 New Website Visit",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Device:*\n{device_str}"},
                            {"type": "mrkdwn", "text": f"*OS:*\n{os_str}"}
                        ]
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Browser:*\n{browser_str}"}
                        ]
                    }
                ]
                
                # Add resolution info
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Display:*\n{resolution_str.replace('\n', ', ')}"
                    }
                })
                
                # Add IP and location if available
                if ip_info:
                    location_str = f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"
                    blocks.append({
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*IP Address:*\n{ip_address}"},
                            {"type": "mrkdwn", "text": f"*Location:*\n{location_str}"}
                        ]
                    })
                    
                    # Add map image
                    blocks.append({
                        "type": "image",
                        "title": {
                            "type": "plain_text",
                            "text": "Location Map",
                            "emoji": True
                        },
                        "image_url": f"https://static-maps.yandex.ru/1.x/?ll={ip_info['lon']},{ip_info['lat']}&size=600,300&z=11&l=map&pt={ip_info['lon']},{ip_info['lat']},pm2rdm1&lang=en",
                        "alt_text": "Map showing visitor location"
                    })
                else:
                    blocks.append({
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*IP Address:*\n{ip_address}"}
                        ]
                    })
                
                # Add timestamp
                blocks.append({
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"Visited at: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"}
                    ]
                })
                
                payload = {"blocks": blocks}
                
            elif platform == "teams":
                # Microsoft Teams format
                facts = [
                    {"name": "Device", "value": device_str},
                    {"name": "OS", "value": os_str},
                    {"name": "Browser", "value": browser_str}
                ]
                
                if ip_info:
                    location_str = f"{ip_info['city']}, {ip_info['region']}, {ip_info['country']}"
                    facts.extend([
                        {"name": "IP Address", "value": ip_address},
                        {"name": "Location", "value": location_str}
                    ])
                else:
                    facts.append({"name": "IP Address", "value": ip_address})
                
                payload = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "0078D7",
                    "summary": "New Website Visit",
                    "sections": [
                        {
                            "activityTitle": "🔔 New Website Visit",
                            "facts": facts,
                            "text": f"Display: {resolution_str.replace('\n', ', ')}"
                        }
                    ]
                }
                
            else:
                # Generic format
                payload = {
                    "event": "visitor",
                    "data": {
                        "id": str(entry.id),
                        "timestamp": timestamp.isoformat(),
                        "device_info": device_str,
                        "browser_info": browser_str,
                        "system_info": os_str,
                        "display_info": resolution_str,
                        "ip_address": ip_address
                    }
                }
                
                if ip_info:
                    payload["data"]["location"] = {
                        "city": ip_info["city"],
                        "region": ip_info["region"],
                        "country": ip_info["country"],
                        "coordinates": {
                            "lat": ip_info["lat"],
                            "lon": ip_info["lon"]
                        }
                    }
            
            # Send webhook
            try:
                response = requests.post(
                    webhook.url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                if response.status_code >= 200 and response.status_code < 300:
                    print(f"Successfully sent visitor webhook to {platform} platform")
                else:
                    print(f"Failed to send visitor webhook to {platform}: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error sending visitor webhook to {platform}: {str(e)}")
        
        # Clear device info from cache
        if ip_address in device_info_cache:
            del device_info_cache[ip_address]
            
    except Exception as e:
        print(f"Error sending visitor webhook: {str(e)}")

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
async def home(request: Request, db: Session = Depends(get_db)):
    """Render the home page"""
    try:
        # Get config data
        config = ConfigManager.read_config()
        
        # Send entry webhook (don't await to avoid slowing down page load)
        try:
            send_visitor_webhook(request, db)
        except Exception as e:
            print(f"Error in entry webhook: {str(e)}")
        
        return templates.TemplateResponse("home.html", {
            "request": request,
            "config": config
        })
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        return templates.TemplateResponse("home.html", {"request": request})

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
        # Get config data
        config = ConfigManager.read_config()
        
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
        
        # Send notification (won't fail form submission if it fails)
        send_message_webhook(name, email, subject, message, ip_address, db)
        
        # Return success page
        return templates.TemplateResponse("success.html", {"request": request, "config": config})
    except Exception as e:
        # Log the error
        print(f"Error saving contact message: {str(e)}")
        
        # Get config data to avoid the same error in the error page
        try:
            config = ConfigManager.read_config()
        except Exception as config_error:
            print(f"Error loading config: {str(config_error)}")
            config = {}
            
        # Return to home page with error
        return templates.TemplateResponse("home.html", {
            "request": request, 
            "error": "There was an error sending your message. Please try again later.",
            "config": config
        })

@router.post("/device-info")
async def device_info(request: Request):
    """Handle device information submission"""
    try:
        # Get the device info from request body
        device_info = await request.json()
        
        # Store in cache using IP as key
        ip_address = request.client.host if hasattr(request, "client") else None
        if ip_address:
            device_info_cache[ip_address] = device_info
            
        return {"status": "success"}
    except Exception as e:
        print(f"Error handling device info: {str(e)}")
        return {"status": "error"}
    