import json
import os
import shutil
from typing import Any, Dict, List
from fastapi import HTTPException

CONFIG_FILE = "data/config.json"
SAMPLE_FILE = "data/sample.json"
MAX_SKILL_SECTIONS = 10

class ConfigManager:
    @staticmethod
    def read_config() -> Dict[str, Any]:
        """Read the configuration file"""
        try:
            if not os.path.exists(CONFIG_FILE):
                # Create config from sample if it exists
                if os.path.exists(SAMPLE_FILE):
                    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
                    shutil.copy2(SAMPLE_FILE, CONFIG_FILE)
                else:
                    raise HTTPException(status_code=404, detail="Neither config nor sample file found")
            
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid config file format")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def write_config(config: Dict[str, Any]) -> None:
        """Write to the configuration file"""
        try:
            # Ensure the data directory exists
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            
            # Write the config with pretty formatting
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def update_config(updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update specific fields in the config"""
        try:
            current_config = ConfigManager.read_config()
            
            def deep_update(d: dict, u: dict) -> dict:
                for k, v in u.items():
                    if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                        deep_update(d[k], v)
                    else:
                        d[k] = v
                return d
            
            # For skills section, replace it entirely instead of deep update
            if "skills" in updates:
                current_config["skills"] = updates["skills"]
                # Validate skills section
                ConfigManager.validate_skills_section(current_config["skills"])
            
            # For what_im_doing section, replace it entirely
            if "what_im_doing" in updates:
                current_config["what_im_doing"] = updates["what_im_doing"]
            
            # For other sections, use deep update
            for section in updates:
                if section not in ["skills", "what_im_doing"]:
                    if section in current_config:
                        deep_update(current_config[section], updates[section])
                    else:
                        current_config[section] = updates[section]
            
            # Write back to file
            ConfigManager.write_config(current_config)
            
            return current_config
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def get_section(section: str) -> Dict[str, Any]:
        """Get a specific section of the config"""
        config = ConfigManager.read_config()
        if section not in config:
            raise HTTPException(status_code=404, detail=f"Section {section} not found")
        return config[section]

    @staticmethod
    def validate_skills_section(skills_data: Dict[str, Any]) -> None:
        """Validate the skills section of the config"""
        if "sections" not in skills_data:
            raise HTTPException(status_code=400, detail="Skills data must contain 'sections'")
        
        sections = skills_data["sections"]
        
        # Check number of sections
        if len(sections) > MAX_SKILL_SECTIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Maximum number of skill sections ({MAX_SKILL_SECTIONS}) exceeded"
            )
        
        # Validate each section
        for section_id, section in sections.items():
            if "title" not in section:
                raise HTTPException(
                    status_code=400,
                    detail=f"Section {section_id} missing title"
                )
            
            if "skills" not in section:
                raise HTTPException(
                    status_code=400,
                    detail=f"Section {section_id} missing skills array"
                )
            
            # Validate each skill in the section
            for skill in section["skills"]:
                if "title" not in skill:
                    raise HTTPException(
                        status_code=400,
                        detail="Skill missing title"
                    )
                
                if "image" not in skill:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Skill {skill.get('title', 'unknown')} missing image"
                    )
                
                # Validate image path
                if not skill["image"].endswith('.webp'):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Skill {skill['title']} image must be in webp format"
                    )

    @staticmethod
    def get_skills() -> Dict[str, Any]:
        """Get the skills section of the config"""
        config = ConfigManager.read_config()
        return config.get("skills", {"sections": {}})

    @staticmethod
    def update_skills(skills_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update only the skills section of the config"""
        try:
            # Validate the skills data
            ConfigManager.validate_skills_section(skills_data)
            
            # Update the config
            return ConfigManager.update_config({"skills": skills_data})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def delete_section(section_id: str) -> Dict[str, Any]:
        """Delete a specific section from the skills configuration"""
        try:
            current_config = ConfigManager.read_config()
            skills_data = current_config.get("skills", {"sections": {}})
            
            # Remove the section if it exists
            if section_id in skills_data["sections"]:
                del skills_data["sections"][section_id]
                
                # Renumber remaining sections to maintain sequential order
                sections = list(skills_data["sections"].items())
                skills_data["sections"] = {
                    f"section_{i+1}": section_data
                    for i, (_, section_data) in enumerate(sections)
                }
                
                # Update the config
                return ConfigManager.update_config({"skills": skills_data})
            
            return current_config
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) 