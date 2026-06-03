from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from passlib.context import CryptContext
from fastapi import Cookie
from app.auth import create_access_token, verify_access_token

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

def get_current_user(request: Request, db: Session = Depends(get_db), access_token: str = Cookie(None)):
    if not access_token:
        return RedirectResponse(url="/login", status_code=303)
    username= verify_access_token(access_token)

    if not username:
        return RedirectResponse(url="/register", status_code = 303)
    
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        return RedirectResponse(url="/register", status_code = 303)

    return user

#ログインボタンが押された時の処理
@router.post("/account/login")
def login_button_clicked(request: Request, db: Session = Depends(get_db), username: str = Form(...), hashed_password: str = Form(...)):
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        return {"error": "ユーザー名、またはパスワードが違います"}

    is_correct = pwd_context.verify(hashed_password, user.hashed_password)

    if not is_correct:
        return {"error": "ユーザー名、またはパスワードが違います"}

    response = RedirectResponse(url="/api/todo", status_code=303)

    access_token = create_access_token(data={"username": username})

    #クッキーに保存
    response.set_cookie(key="access_token", value=access_token, httponly=True)

    return response

#ログアウト機能
@router.post("/account/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response
