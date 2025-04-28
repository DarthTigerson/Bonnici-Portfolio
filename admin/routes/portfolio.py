import os
import json
import sys
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session
import requests
import uuid
from PIL import Image
import io
import shutil

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database import SessionLocal
from .admin import require_admin

# Set up templates
templates = Jinja2Templates(directory="admin/templates")

# Constants
PORTFOLIO_IMAGE_DIR = "data/images/portfolio"
CONFIG_FILE = "data/config.json"

router = APIRouter(
    prefix="/portfolio",
    tags=["portfolio"],
)

def read_config():
    """Read the main config file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"portfolio": {"enabled": True, "projects": []}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def save_config(config):
    """Save the main config file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
@require_admin
async def portfolio_page(request: Request):
    config = read_config()
    
    # Get portfolio data from config
    portfolio_config = config.get("portfolio", {"enabled": True, "projects": []})
    
    # Get enabled state
    show_on_frontend = portfolio_config.get("enabled", True)
    
    # Add image_url to each project if not present
    for project in portfolio_config.get("projects", []):
        if "image_url" not in project and "image" in project:
            image_name = project['image']
            
            # Check image locations in this order: 
            # 1. portfolio subfolder (new images)
            # 2. main images directory (old images)
            
            portfolio_path = f"/data/images/portfolio/{image_name}"
            general_path = f"/data/images/{image_name}"
            
            # First check in portfolio subfolder (for newly uploaded images)
            if os.path.exists(os.path.join("data/images/portfolio", image_name)):
                project["image_url"] = portfolio_path
            else:
                # Default to the main images directory
                project["image_url"] = general_path
    
    return templates.TemplateResponse(
        "portfolio.html", 
        {
            "request": request,
            "portfolio_config": portfolio_config,
            "show_on_frontend": show_on_frontend
        }
    )

@router.post("/save")
@require_admin
async def save_portfolio(
    request: Request,
    data: str = Form(...),
):
    """Save portfolio projects including handling image uploads"""
    try:
        # Parse projects JSON
        portfolio_data = json.loads(data)
        projects_data = portfolio_data.get("projects", [])
        
        # Log project names and their indexes
        project_order = [(p.get('index', 'N/A'), p.get('title', 'Untitled')) for p in projects_data]
        print(f"Received projects in order: {project_order}")
        
        # Ensure projects is a list
        if not isinstance(projects_data, list):
            raise HTTPException(status_code=400, detail="Projects data must be a list")
        
        # Create portfolio directory if it doesn't exist
        os.makedirs(PORTFOLIO_IMAGE_DIR, exist_ok=True)
        
        # Get other portfolio settings
        show_on_frontend = portfolio_data.get("enabled", True)
        columns = portfolio_data.get("columns", 2)
        display_mode = portfolio_data.get("mode", "description")
        
        # Process any uploaded images
        form_data = await request.form()
        updated_projects = []
        
        for i, project in enumerate(projects_data):
            # Ensure each project has the correct index based on its position in the array
            # This ensures the order is maintained
            project['index'] = i + 1
            
            image_key = f"image_{i}"
            
            if image_key in form_data:
                # Get the uploaded file
                image_file = form_data[image_key]
                
                # Generate a safe filename with project ID to avoid overwriting
                original_filename = image_file.filename
                ext = os.path.splitext(original_filename)[1].lower()
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"project_{i}_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
                
                # Save the image
                file_path = os.path.join(PORTFOLIO_IMAGE_DIR, filename)
                
                try:
                    # If SVG or GIF, save directly
                    if ext.lower() in ['.svg', '.gif']:
                        with open(file_path, 'wb') as f:
                            content = await image_file.read()
                            f.write(content)
                    else:
                        # Process and convert to webp for all other image types
                        content = await image_file.read()
                        img = Image.open(io.BytesIO(content))
                        
                        # Resize if too large
                        max_width, max_height = 800, 600
                        if img.width > max_width or img.height > max_height:
                            img.thumbnail((max_width, max_height))
                        
                        # Save as webp
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        webp_filename = f"project_{i}_{timestamp}_{uuid.uuid4().hex[:8]}.webp"
                        webp_path = os.path.join(PORTFOLIO_IMAGE_DIR, webp_filename)
                        img.save(webp_path, 'WEBP', quality=85)
                        filename = webp_filename
                        file_path = webp_path
                except Exception as e:
                    # Log the error
                    print(f"Error processing image upload: {str(e)}")
                    # Return a specific error message about the failed image
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Failed to process image for project '{project.get('title', 'Unknown')}': {str(e)}"
                    )
                
                # Update project with the new image filename
                project['image'] = filename
                
                # Add to updated projects list
                updated_projects.append({
                    'index': project['index'],
                    'image': filename
                })
            
            # Remove temporary image_url if it exists
            if 'image_url' in project:
                del project['image_url']
        
        # Log final order of projects
        final_order = [(p.get('index', 'N/A'), p.get('title', 'Untitled')) for p in projects_data]
        print(f"Final project order to save: {final_order}")
        
        # Read existing config
        config = read_config()
        
        # Update portfolio section in config
        if "portfolio" not in config:
            config["portfolio"] = {}
            
        config["portfolio"]["projects"] = projects_data
        config["portfolio"]["enabled"] = show_on_frontend
        config["portfolio"]["columns"] = columns
        config["portfolio"]["mode"] = display_mode
        
        # Save full config
        save_config(config)
        
        return {
            "success": True,
            "updated_projects": updated_projects
        }
    except Exception as e:
        print(f"Error saving portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

