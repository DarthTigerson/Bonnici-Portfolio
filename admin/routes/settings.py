import io
import json
import os
import shutil
import sys
import uuid
import zipfile
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import Webhook
from .admin import require_admin

templates = Jinja2Templates(directory="admin/templates")

CONFIG_FILE = "data/config.json"
IMAGES_DIR = "data/images"

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_referenced_images(config: dict) -> list:
    """Return list of (filesystem_path, zip_path) for all images referenced in config."""
    images = []

    # Profile image
    profile_path = os.path.join(IMAGES_DIR, "profile.webp")
    if os.path.exists(profile_path):
        images.append((profile_path, "images/profile.webp"))

    # Skills images — stored as bare filenames in skills sections
    for section in config.get("skills", {}).get("sections", {}).values():
        for skill in section.get("skills", []):
            img = skill.get("image", "")
            if img:
                skill_path = os.path.join(IMAGES_DIR, "skills", img)
                if os.path.exists(skill_path):
                    images.append((skill_path, f"images/skills/{img}"))

    # Portfolio images — check portfolio/ subfolder first, then root images/
    for project in config.get("portfolio", {}).get("projects", []):
        img = project.get("image", "")
        if img:
            portfolio_path = os.path.join(IMAGES_DIR, "portfolio", img)
            general_path = os.path.join(IMAGES_DIR, img)
            if os.path.exists(portfolio_path):
                images.append((portfolio_path, f"images/portfolio/{img}"))
            elif os.path.exists(general_path):
                images.append((general_path, f"images/{img}"))

    return images


@router.get("")
@require_admin
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})


@router.get("/export")
@require_admin
async def export_data(request: Request, db: Session = Depends(get_db)):
    """Generate and stream a ZIP export of all portfolio data (excluding messages and traffic)."""
    try:
        if not os.path.exists(CONFIG_FILE):
            raise HTTPException(status_code=404, detail="Config file not found")

        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        webhooks = db.query(Webhook).all()
        webhooks_data = [{"name": w.name, "url": w.url} for w in webhooks]

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("config.json", json.dumps(config, indent=4))
            zf.writestr("webhooks.json", json.dumps(webhooks_data, indent=4))

            seen = set()
            for fs_path, zip_path in get_referenced_images(config):
                if zip_path not in seen:
                    zf.write(fs_path, zip_path)
                    seen.add(zip_path)

        buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bonnici_portfolio_export_{timestamp}.zip"

        return StreamingResponse(
            buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
@require_admin
async def import_data(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import a previously exported ZIP, fully replacing current config, images, and webhooks."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip archive")

    try:
        content = await file.read()
        buffer = io.BytesIO(content)

        if not zipfile.is_zipfile(buffer):
            raise HTTPException(status_code=400, detail="Invalid ZIP file")

        buffer.seek(0)
        with zipfile.ZipFile(buffer, "r") as zf:
            names = zf.namelist()

            if "config.json" not in names:
                raise HTTPException(status_code=400, detail="Missing config.json in archive")

            config_data = json.loads(zf.read("config.json"))

            webhooks_data = []
            if "webhooks.json" in names:
                webhooks_data = json.loads(zf.read("webhooks.json"))

            # Write config
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                json.dump(config_data, f, indent=4)

            # Replace webhooks
            db.query(Webhook).delete()
            for wh in webhooks_data:
                name = wh.get("name")
                url = wh.get("url")
                if name and url:
                    db.add(Webhook(id=uuid.uuid4(), name=name, url=url, created=datetime.now()))
            db.commit()

            # Extract images
            for name in names:
                if name.startswith("images/") and not name.endswith("/"):
                    target_path = os.path.join("data", name)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zf.open(name) as src, open(target_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)

        return {"status": "success", "message": "Import completed successfully"}

    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in archive")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
