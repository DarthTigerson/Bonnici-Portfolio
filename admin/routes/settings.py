import io
import json
import os
import sys
import uuid
import zipfile
from datetime import datetime

from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from models import Webhook
from .admin import require_admin

CONFIG_FILE = "data/config.json"
IMAGES_DIR = "data/images"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _collect_image_paths(config: dict) -> list[str]:
    """Return all image file paths referenced in config that exist on disk."""
    paths = set()

    # Profile image — fixed path, not in config
    profile_path = os.path.join(IMAGES_DIR, "profile.webp")
    if os.path.isfile(profile_path):
        paths.add(profile_path)

    # Skill images
    for section in config.get("skills", {}).get("sections", {}).values():
        for skill in section.get("skills", []):
            img = skill.get("image", "")
            if img:
                # img may be "data/images/skills/foo.webp" or just "skills/foo.webp"
                candidate = img if os.path.isabs(img) else img.lstrip("/")
                if not candidate.startswith("data/"):
                    candidate = os.path.join(IMAGES_DIR, candidate)
                if os.path.isfile(candidate):
                    paths.add(candidate)

    # Portfolio images
    for project in config.get("portfolio", {}).get("projects", []):
        img = project.get("image", "")
        if img:
            candidate = img if os.path.isabs(img) else img.lstrip("/")
            if not candidate.startswith("data/"):
                candidate = os.path.join(IMAGES_DIR, candidate)
            if os.path.isfile(candidate):
                paths.add(candidate)

    return list(paths)


router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/export")
@require_admin
async def export_data(request: Request, db: Session = Depends(get_db)):
    try:
        # Read config
        if not os.path.isfile(CONFIG_FILE):
            raise HTTPException(status_code=404, detail="config.json not found")
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        # Serialize webhooks
        webhooks = db.query(Webhook).all()
        webhooks_data = [{"name": w.name, "url": w.url} for w in webhooks]

        # Build ZIP in memory
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("config.json", json.dumps(config, indent=4))
            zf.writestr("webhooks.json", json.dumps(webhooks_data, indent=4))
            for path in _collect_image_paths(config):
                # Store with relative path inside ZIP (e.g. data/images/profile.webp)
                zf.write(path, arcname=path)

        buf.seek(0)
        filename = f"portfolio_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
@require_admin
async def import_data(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip archive")

    extracted: list[str] = []
    warnings: list[str] = []

    try:
        content = await file.read()
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names = zf.namelist()

            # --- config.json ---
            if "config.json" not in names:
                raise HTTPException(status_code=400, detail="Archive is missing config.json")
            try:
                config_bytes = zf.read("config.json")
                config = json.loads(config_bytes)
                os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
                with open(CONFIG_FILE, "w") as f:
                    json.dump(config, f, indent=4)
                extracted.append("config.json")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to restore config.json: {e}")

            # --- webhooks.json ---
            if "webhooks.json" in names:
                try:
                    wh_data = json.loads(zf.read("webhooks.json"))
                    db.query(Webhook).delete()
                    for wh in wh_data:
                        if wh.get("name") and wh.get("url"):
                            db.add(Webhook(id=uuid.uuid4(), name=wh["name"], url=wh["url"], created=datetime.now()))
                    db.commit()
                    extracted.append("webhooks.json")
                except Exception as e:
                    db.rollback()
                    warnings.append(f"webhooks.json: {e}")
            else:
                warnings.append("webhooks.json not found in archive — webhooks unchanged")

            # --- images ---
            os.makedirs(IMAGES_DIR, exist_ok=True)
            image_entries = [n for n in names if n.startswith("data/images/") and not n.endswith("/")]
            for entry in image_entries:
                try:
                    dest = entry  # preserve relative path (data/images/...)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    with open(dest, "wb") as f:
                        f.write(zf.read(entry))
                    extracted.append(entry)
                except Exception as e:
                    warnings.append(f"{entry}: {e}")

        return {"status": "success", "extracted": extracted, "warnings": warnings}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
