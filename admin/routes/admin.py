from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import hashlib
from datetime import datetime, timedelta
from functools import wraps

from database import SessionLocal
from models import AdminToken

router = APIRouter()
templates = Jinja2Templates(directory="admin/templates")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_admin(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Get token hash from cookie
        token_hash = request.cookies.get("admin_token")
        
        if not token_hash:
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
        # Verify token hash against database
        db = SessionLocal()
        try:
            admin_token = db.query(AdminToken).filter(AdminToken.token_hash == token_hash).first()
            if not admin_token:
                response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
                response.delete_cookie("admin_token")
                return response
        finally:
            db.close()
        
        return await func(request, *args, **kwargs)
    return wrapper

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, response: Response, db: Session = Depends(get_db)):
    form = await request.form()
    token = form.get("token")
    
    if not token:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Token is required"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Hash the provided token
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Check if token hash exists in database
    admin_token = db.query(AdminToken).filter(AdminToken.token_hash == token_hash).first()
    
    if not admin_token:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid token"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Set secure HTTP-only cookie that expires in 6 months
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="admin_token",
        value=token_hash,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=180 * 24 * 60 * 60  # 6 months in seconds
    )
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("admin_token")
    return response
