from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# アカウント登録画面の表示
@router.get("/account/register", response_class=HTMLResponse)
def get_account_register(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )