import os
import json
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from config_manager import ConfigManager
from .admin import require_admin
from PIL import Image
import io
from colorthief import ColorThief

# Set up templates
templates = Jinja2Templates(directory="admin/templates")

# Constants
SKILLS_IMAGE_DIR = "data/images/skills"

router = APIRouter(
    prefix="/profile",
    tags=["profile"],
)

def read_what_im_doing():
    """Read the what_im_doing.json file"""
    try:
        with open("data/what_im_doing.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default structure if file doesn't exist
        return {
            f"panel_{i}": {
                "enabled": False,
                "title": "",
                "description": "",
                "image": "",
                "flag": {
                    "enabled": False,
                    "text": ""
                }
            } for i in range(1, 5)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
@require_admin
async def profile_page(request: Request):
    """Display profile management page"""
    try:
        config = ConfigManager.read_config()
        
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "main_info": config["main_info"],
                "contact_card": config["contact_card"],
                "about_me": config["about_me"],
                "what_im_doing": config["what_im_doing"],
                "skills": config.get("skills", {"sections": {}}),
                "os": os
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def update_svg_color(svg_content: str) -> str:
    """Update the SVG color to match the correct yellow (#ffd404)"""
    if not svg_content:
        return svg_content
    
    # Replace any fill color with our yellow color
    svg_content = svg_content.replace('fill="#000000"', 'fill="#ffd404"')
    svg_content = svg_content.replace("fill='#000000'", "fill='#ffd404'")
    svg_content = svg_content.replace('fill="#3498db"', 'fill="#ffd404"')
    svg_content = svg_content.replace("fill='#3498db'", "fill='#ffd404'")
    svg_content = svg_content.replace('fill="#10b981"', 'fill="#ffd404"')
    svg_content = svg_content.replace("fill='#10b981'", "fill='#ffd404'")
    svg_content = svg_content.replace('fill="#ffb800"', 'fill="#ffd404"')
    svg_content = svg_content.replace("fill='#ffb800'", "fill='#ffd404'")
    svg_content = svg_content.replace('fill="#FFFF00"', 'fill="#ffd404"')
    svg_content = svg_content.replace("fill='#FFFF00'", "fill='#ffd404'")
    return svg_content

@router.post("/update")
@require_admin
async def update_profile(request: Request, updates: Dict[str, Any]):
    """Update profile information"""
    try:
        # Update SVG colors in what_im_doing panels
        if "what_im_doing" in updates:
            for panel in updates["what_im_doing"].values():
                if "image" in panel:
                    panel["image"] = update_svg_color(panel["image"])
        
        # Update the config with the new data
        updated_config = ConfigManager.update_config(updates)
        return JSONResponse({"status": "success", "data": updated_config})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-image")
@require_admin
async def upload_profile_image(request: Request, file: UploadFile = File(...)):
    """Upload and process profile image (convert to webp)"""
    try:
        # Validate file is an image
        if not file.content_type.startswith('image/'):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "detail": "File must be an image"}
            )
        
        # Read image content
        content = await file.read()
        if not content:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "detail": "Empty file uploaded"}
            )
        
        # Create data/images directory if it doesn't exist
        os.makedirs("data/images", exist_ok=True)
        
        try:
            # Open and process the image
            img = Image.open(io.BytesIO(content))
            
            # Calculate new dimensions (max 800x800)
            width, height = img.size
            if width > 800 or height > 800:
                ratio = min(800 / width, 800 / height)
                width = int(width * ratio)
                height = int(height * ratio)
                img = img.resize((width, height))
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Save as WebP
            filepath = os.path.join("data/images", "profile.webp")
            img.save(filepath, 'webp', quality=85, method=6)
            
            return JSONResponse({
                "status": "success",
                "path": "/data/images/profile.webp"
            })
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "detail": f"Failed to process image: {str(e)}"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": f"Internal server error: {str(e)}"}
        )

def extract_colors_from_image(img):
    """Extract dominant color from an image and darken it for background"""
    # Create a BytesIO object for ColorThief
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    color_thief = ColorThief(img_byte_arr)
    
    # Get the dominant color
    dominant_color = color_thief.get_color(quality=1)
    
    # Convert to hex for border color
    border_color = "#{:02x}{:02x}{:02x}".format(dominant_color[0], dominant_color[1], dominant_color[2])
    
    # Create a darkened version for background (multiply by 0.6 to darken but keep some brightness)
    darkened = tuple(int(c * 0.2) for c in dominant_color)
    background_color = "#{:02x}{:02x}{:02x}".format(darkened[0], darkened[1], darkened[2])
    
    return {
        "border_color": border_color,
        "background_color": background_color
    }

@router.post("/skills/upload-image")
@require_admin
async def upload_skill_image(
    request: Request,
    image: UploadFile = File(...),
    section_id: str = Form(...),
    skill_title: str = Form(...)
):
    """Upload and process skill image (SVG or convert to webp)"""
    try:
        # Validate file is an image
        if not image.content_type.startswith('image/'):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "detail": "File must be an image"}
            )
        
        # Read image content
        content = await image.read()
        if not content:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "detail": "Empty file uploaded"}
            )
        
        # Create skills directory if it doesn't exist
        try:
            os.makedirs(SKILLS_IMAGE_DIR, exist_ok=True)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "detail": f"Failed to create directory: {str(e)}"}
            )
        
        # Generate a safe filename from the original filename
        original_filename = image.filename.lower()
        base_name = os.path.splitext(original_filename)[0]
        safe_name = "".join(c for c in base_name if c.isalnum() or c in ('_', '-'))
        
        # Handle SVG files differently
        if image.content_type == 'image/svg+xml':
            try:
                # Save SVG directly with original extension
                filename = f"{safe_name}.svg"
                filepath = os.path.join(SKILLS_IMAGE_DIR, filename)
                
                # Handle duplicate filenames
                counter = 1
                while os.path.exists(filepath):
                    filename = f"{safe_name}_{counter}.svg"
                    filepath = os.path.join(SKILLS_IMAGE_DIR, filename)
                    counter += 1
                
                with open(filepath, 'wb') as f:
                    f.write(content)
                
                # For SVGs, we can't extract color so use default colors
                colors = {
                    "background_color": "#000000",
                    "border_color": "#3498db"
                }
                
                return JSONResponse({
                    "status": "success",
                    "filename": filename,
                    "colors": colors
                })
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "detail": f"Failed to save SVG: {str(e)}"}
                )
        
        # For non-SVG images, process as WebP
        try:
            img = Image.open(io.BytesIO(content))
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "detail": f"Invalid image file: {str(e)}"}
            )
        
        # Extract colors from the image
        colors = extract_colors_from_image(img)
        
        # Resize image if too large (max 256x256)
        if img.width > 256 or img.height > 256:
            img.thumbnail((256, 256))
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Save as WebP with original name
        filename = f"{safe_name}.webp"
        filepath = os.path.join(SKILLS_IMAGE_DIR, filename)
        
        # Handle duplicate filenames
        counter = 1
        while os.path.exists(filepath):
            filename = f"{safe_name}_{counter}.webp"
            filepath = os.path.join(SKILLS_IMAGE_DIR, filename)
            counter += 1
        
        try:
            img.save(filepath, 'webp', quality=85, method=6)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "detail": f"Failed to save image: {str(e)}"}
            )
        
        return JSONResponse({
            "status": "success",
            "filename": filename,
            "colors": colors
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": f"Internal server error: {str(e)}"}
        )
