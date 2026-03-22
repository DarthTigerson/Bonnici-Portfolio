import os
import sys
import json
import uuid
import base64
import io
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Body
from PIL import Image
from .admin import require_admin

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

PORTFOLIO_IMAGE_DIR = "data/images/portfolio"
CONFIG_FILE = "data/config.json"

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


def read_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"portfolio": {"enabled": True, "projects": []}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def save_config(config):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
@require_admin
async def get_portfolio(request: Request):
    config = read_config()
    portfolio = config.get("portfolio", {"enabled": True, "columns": 2, "mode": "tags", "projects": []})
    for project in portfolio.get("projects", []):
        if "image" in project and project["image"] and "image_url" not in project:
            name = project["image"]
            if os.path.exists(os.path.join("data/images/portfolio", name)):
                project["image_url"] = f"/data/images/portfolio/{name}"
            else:
                project["image_url"] = f"/data/images/{name}"
    return {
        "enabled": portfolio.get("enabled", True),
        "columns": portfolio.get("columns", 2),
        "mode": portfolio.get("mode", "tags"),
        "projects": portfolio.get("projects", []),
    }


@router.post("")
@require_admin
async def save_portfolio(request: Request, data: dict = Body(...)):
    try:
        os.makedirs(PORTFOLIO_IMAGE_DIR, exist_ok=True)
        projects = data.get("projects", [])
        for i, project in enumerate(projects):
            project["index"] = i
            image_url = project.pop("image_url", None)
            # If image_url is a base64 data URL, decode and save as webp
            if image_url and image_url.startswith("data:image/"):
                try:
                    _, b64data = image_url.split(",", 1)
                    raw = base64.b64decode(b64data)
                    img = Image.open(io.BytesIO(raw))
                    if img.width > 800 or img.height > 600:
                        img.thumbnail((800, 600))
                    ts = datetime.now().strftime("%Y%m%d%H%M%S")
                    filename = f"project_{i}_{ts}_{uuid.uuid4().hex[:8]}.webp"
                    img.save(os.path.join(PORTFOLIO_IMAGE_DIR, filename), "WEBP", quality=85)
                    project["image"] = filename
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Image processing failed: {e}")

        config = read_config()
        if "portfolio" not in config:
            config["portfolio"] = {}
        config["portfolio"]["projects"] = projects
        config["portfolio"]["enabled"] = data.get("enabled", True)
        config["portfolio"]["columns"] = data.get("columns", 2)
        config["portfolio"]["mode"] = data.get("mode", "tags")
        save_config(config)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
