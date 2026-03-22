import os
import sys
import io
import re
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form, Body
from fastapi.responses import JSONResponse
from PIL import Image
from colorthief import ColorThief
from config_manager import ConfigManager
from .admin import require_admin

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

SKILLS_IMAGE_DIR = "data/images/skills"

router = APIRouter(prefix="/api/profile", tags=["profile"])


def update_svg_color(svg_content: str) -> str:
    if not svg_content:
        return svg_content
    svg_content = svg_content.replace('fill="#000000"', 'fill="#6366f1"')
    svg_content = svg_content.replace("fill='#000000'", "fill='#6366f1'")
    svg_content = svg_content.replace('fill="#3498db"', 'fill="#6366f1"')
    svg_content = svg_content.replace("fill='#3498db'", "fill='#6366f1'")
    svg_content = svg_content.replace('fill="#10b981"', 'fill="#6366f1"')
    svg_content = svg_content.replace("fill='#10b981'", "fill='#6366f1'")
    svg_content = svg_content.replace('fill="#ffb800"', 'fill="#6366f1"')
    svg_content = svg_content.replace("fill='#ffb800'", "fill='#6366f1'")
    svg_content = svg_content.replace('fill="#FFFF00"', 'fill="#6366f1"')
    svg_content = svg_content.replace("fill='#FFFF00'", "fill='#6366f1'")
    svg_content = svg_content.replace('.st0{fill:#000000;}', '.st0{fill:#6366f1;}')
    svg_content = svg_content.replace('.st0{fill:#000000}', '.st0{fill:#6366f1}')
    svg_content = svg_content.replace('.st0 { fill:#000000; }', '.st0 { fill:#6366f1; }')
    svg_content = svg_content.replace('.st0 { fill: #000000; }', '.st0 { fill: #6366f1; }')
    svg_content = svg_content.replace('.st0{fill: #000000;}', '.st0{fill: #6366f1;}')
    svg_content = re.sub(r'\.st0\s*{\s*fill\s*:\s*#000000\s*;\s*}', '.st0{fill:#6366f1;}', svg_content)
    return svg_content


def standardize_svg_attributes(svg_content: str) -> str:
    if not svg_content or not svg_content.strip().startswith('<svg'):
        return svg_content
    svg_tag_pattern = r'<svg[^>]*>'
    svg_tag_match = re.search(svg_tag_pattern, svg_content)
    if not svg_tag_match:
        return svg_content
    svg_tag = svg_tag_match.group(0)
    has_all_attributes = all(attr in svg_tag for attr in ['height="200px"', 'width="200px"', 'version="1.0"', 'encoding="utf-8"'])
    if has_all_attributes:
        return svg_content
    svg_tag_updated = re.sub(r'(width|height|fill|version|encoding)=["\'][^"\']*["\']\s*', '', svg_tag)
    svg_tag_updated = svg_tag_updated.replace('<svg', '<svg fill="#6366f1" height="200px" width="200px" version="1.0" encoding="utf-8"')
    updated_svg = svg_content.replace(svg_tag, svg_tag_updated)
    if 'viewBox' not in svg_tag_updated:
        svg_viewbox = re.sub(r'<svg', '<svg viewBox="0 0 200 200"', svg_tag_updated)
        updated_svg = updated_svg.replace(svg_tag_updated, svg_viewbox)
    return updated_svg


def extract_colors_from_image(img):
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    color_thief = ColorThief(img_byte_arr)
    dominant_color = color_thief.get_color(quality=1)
    border_color = "#{:02x}{:02x}{:02x}".format(dominant_color[0], dominant_color[1], dominant_color[2])
    darkened = tuple(int(c * 0.2) for c in dominant_color)
    background_color = "#{:02x}{:02x}{:02x}".format(darkened[0], darkened[1], darkened[2])
    return {"border_color": border_color, "background_color": background_color}


@router.get("")
@require_admin
async def get_profile(request: Request):
    try:
        config = ConfigManager.read_config()
        return {
            "main_info": config["main_info"],
            "contact_card": config["contact_card"],
            "about_me": config["about_me"],
            "what_im_doing": config["what_im_doing"],
            "skills": config.get("skills", {"sections": {}}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
@require_admin
async def update_profile(request: Request, updates: Dict[str, Any] = Body(...)):
    try:
        if "what_im_doing" in updates:
            for panel in updates["what_im_doing"].values():
                if "image" in panel and panel["image"]:
                    panel["image"] = update_svg_color(panel["image"])
                    panel["image"] = standardize_svg_attributes(panel["image"])
        updated_config = ConfigManager.update_config(updates)
        return {"status": "success", "data": updated_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image")
@require_admin
async def upload_profile_image(request: Request, file: UploadFile = File(...)):
    try:
        if not file.content_type.startswith('image/'):
            return JSONResponse(status_code=400, content={"status": "error", "detail": "File must be an image"})
        filename_lower = file.filename.lower()
        if filename_lower.endswith('.heic') or filename_lower.endswith('.heif') or 'heic' in file.content_type.lower():
            return JSONResponse(status_code=400, content={"status": "error", "detail": "HEIC/HEIF format not supported. Please use JPEG, PNG, or another standard format."})
        content = await file.read()
        if not content:
            return JSONResponse(status_code=400, content={"status": "error", "detail": "Empty file uploaded"})
        os.makedirs("data/images", exist_ok=True)
        try:
            img = Image.open(io.BytesIO(content))
            width, height = img.size
            if width > 800 or height > 800:
                ratio = min(800 / width, 800 / height)
                img = img.resize((int(width * ratio), int(height * ratio)))
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            filepath = os.path.join("data/images", "profile.webp")
            img.save(filepath, 'webp', quality=85, method=6)
            return JSONResponse({"status": "success", "path": "/data/images/profile.webp"})
        except Exception as e:
            return JSONResponse(status_code=500, content={"status": "error", "detail": f"Failed to process image: {str(e)}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": f"Internal server error: {str(e)}"})


@router.post("/skills/upload-image")
@require_admin
async def upload_skill_image(
    request: Request,
    image: UploadFile = File(...),
    section_id: str = Form(...),
    skill_title: str = Form(...),
):
    try:
        if not image.content_type.startswith('image/'):
            return JSONResponse(status_code=400, content={"status": "error", "detail": "File must be an image"})
        filename_lower = image.filename.lower()
        if filename_lower.endswith('.heic') or filename_lower.endswith('.heif') or 'heic' in image.content_type.lower():
            return JSONResponse(status_code=400, content={"status": "error", "detail": "HEIC/HEIF format not supported."})
        content = await image.read()
        if not content:
            return JSONResponse(status_code=400, content={"status": "error", "detail": "Empty file uploaded"})
        try:
            os.makedirs(SKILLS_IMAGE_DIR, exist_ok=True)
        except Exception as e:
            return JSONResponse(status_code=500, content={"status": "error", "detail": f"Failed to create directory: {str(e)}"})

        original_filename = image.filename.lower()
        base_name = os.path.splitext(original_filename)[0]
        safe_name = "".join(c for c in base_name if c.isalnum() or c in ('_', '-'))

        if image.content_type == 'image/svg+xml':
            try:
                filename = f"{safe_name}.svg"
                filepath = os.path.join(SKILLS_IMAGE_DIR, filename)
                counter = 1
                while os.path.exists(filepath):
                    filename = f"{safe_name}_{counter}.svg"
                    filepath = os.path.join(SKILLS_IMAGE_DIR, filename)
                    counter += 1
                svg_content = content.decode('utf-8')
                svg_tag_match = re.search(r'<svg[^>]*>', svg_content)
                if svg_tag_match:
                    svg_tag = svg_tag_match.group(0)
                    svg_tag_updated = re.sub(r'(width|height|fill|version|encoding)=["\'][^"\']*["\']\s*', '', svg_tag)
                    svg_tag_updated = svg_tag_updated.replace('<svg', '<svg fill="#6366f1" height="200px" width="200px" version="1.0" encoding="utf-8"')
                    svg_content = svg_content.replace(svg_tag, svg_tag_updated)
                    if 'viewBox' not in svg_tag_updated:
                        svg_content = svg_content.replace(svg_tag_updated, svg_tag_updated.replace('<svg', '<svg viewBox="0 0 200 200"'))
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
                return JSONResponse({"status": "success", "filename": filename, "colors": {"background_color": "#000000", "border_color": "#3498db"}})
            except Exception as e:
                return JSONResponse(status_code=500, content={"status": "error", "detail": f"Failed to save SVG: {str(e)}"})

        try:
            img = Image.open(io.BytesIO(content))
        except Exception as e:
            return JSONResponse(status_code=400, content={"status": "error", "detail": f"Invalid image file: {str(e)}"})

        colors = extract_colors_from_image(img)
        if img.width > 256 or img.height > 256:
            img.thumbnail((256, 256))
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        filename = f"{safe_name}.webp"
        filepath = os.path.join(SKILLS_IMAGE_DIR, filename)
        counter = 1
        while os.path.exists(filepath):
            filename = f"{safe_name}_{counter}.webp"
            filepath = os.path.join(SKILLS_IMAGE_DIR, filename)
            counter += 1
        try:
            img.save(filepath, 'webp', quality=85, method=6)
        except Exception as e:
            return JSONResponse(status_code=500, content={"status": "error", "detail": f"Failed to save image: {str(e)}"})

        return JSONResponse({"status": "success", "filename": filename, "colors": colors})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": f"Internal server error: {str(e)}"})
