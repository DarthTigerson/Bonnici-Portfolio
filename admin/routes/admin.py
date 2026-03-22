import hashlib
from datetime import datetime, timedelta
from functools import wraps
from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import SessionLocal
from models import AdminToken

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        token_hash = request.cookies.get("admin_token")
        if not token_hash:
            return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
        db = SessionLocal()
        try:
            admin_token = db.query(AdminToken).filter(AdminToken.token_hash == token_hash).first()
            if not admin_token:
                response = JSONResponse(status_code=401, content={"detail": "Invalid token"})
                response.delete_cookie("admin_token")
                return response
        finally:
            db.close()
        return await func(request, *args, **kwargs)
    return wrapper


@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    token = form.get("token")
    if not token:
        return JSONResponse(status_code=400, content={"error": "Token is required"})
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    admin_token = db.query(AdminToken).filter(AdminToken.token_hash == token_hash).first()
    if not admin_token:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
    response = JSONResponse(content={"status": "success"})
    response.set_cookie(
        key="admin_token",
        value=token_hash,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=180 * 24 * 60 * 60,
    )
    return response


@router.get("/logout")
async def logout():
    response = JSONResponse(content={"status": "success"})
    response.delete_cookie("admin_token")
    return response
