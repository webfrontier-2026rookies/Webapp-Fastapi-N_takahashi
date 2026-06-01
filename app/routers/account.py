from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from passlib.context import CryptContext


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# アカウント登録画面の表示
@router.get("/register", response_class=HTMLResponse)
def get_account_register(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="account/register.html"
    )

#ログイン画面の表示
@router.get("/login", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="account/login.html" 
    )

#登録ボタンが押された時の処理
@router.post("/account/register", response_class=HTMLResponse)
def register_button_clicked(request: Request, db: Session = Depends (get_db), username: str = Form(...),  hashed_password: str = Form(...)):
    #パスワードハッシュ化用のツールを準備
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

    hashed_password = pwd_context.hash( hashed_password)

    new_user = models.User(
        username=username,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(url="/login", status_code=303)