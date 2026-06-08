from fastapi import APIRouter, Request, Depends, Form, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from passlib.context import CryptContext
from app.auth import create_access_token, verify_access_token
from app.schemas import verify_csrf_token
import secrets
import os

router = APIRouter(tags=["認証・セキュリティ"])
templates = Jinja2Templates(directory="templates")

# ----------------------------------------------------
# 📄 1. アカウント登録画面の表示 (GET)
# ----------------------------------------------------
@router.get("/account/register", response_class=HTMLResponse) # 💡URLを統一
def get_account_register(request: Request):
    csrf_token = secrets.token_urlsafe(32)

    response = templates.TemplateResponse(
        request=request,
        name="account/register.html",
        context={"csrf_token": csrf_token}
    )
    
    response.set_cookie(key="csrf_token", value=csrf_token, httponly=False, samesite="lax", path="/")
    return response


# ----------------------------------------------------
# 🛡️ 2. 登録ボタンが押された時の処理 (POST)
# ----------------------------------------------------
@router.post("/account/register", response_class=HTMLResponse, dependencies=[Depends(verify_csrf_token)])
def register_button_clicked(
    request: Request, 
    db: Session = Depends(get_db), 
    username: str = Form(...), 
    hashed_password: str = Form(...)
):
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
    hashed_password = pwd_context.hash(hashed_password)

    new_user = models.User(
        username=username,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 💡リダイレクト先を正しいログインURLに統一
    return RedirectResponse(url="/account/login", status_code=303)


# ----------------------------------------------------
# 📄 3. ログイン画面の表示 (GET)
# ----------------------------------------------------
@router.get("/account/login", response_class=HTMLResponse) # 💡URLを統一
def get_login_page(request: Request):
    csrf_token = secrets.token_urlsafe(32)
    response = templates.TemplateResponse(
        request=request,
        name="account/login.html",
        context={"csrf_token": csrf_token}
    )

    response.set_cookie(key="csrf_token", value=csrf_token, httponly=False, samesite="lax", path="/")
    return response


# ----------------------------------------------------
# 🛡️ 4. ログインボタンが押された時の処理 (POST)
# ----------------------------------------------------
@router.post("/account/login", dependencies=[Depends(verify_csrf_token)])
def login_button_clicked(
    request: Request, 
    db: Session = Depends(get_db), 
    username: str = Form(...), 
    hashed_password: str = Form(...)
):
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        return {"error": "ユーザー名、またはパスワードが違います"}

    is_correct = pwd_context.verify(hashed_password, user.hashed_password)

    if not is_correct:
        return {"error": "ユーザー名、またはパスワードが違います"}

    response = RedirectResponse(url="/api/todo", status_code=303)
    
    # 🟢 auth.pyを直したので、これで100%エラーにならず動きます！
    access_token = create_access_token(data={"username": username})
    current_csrf_token = request.cookies.get("csrf_token")

    ENV = os.getenv("ENVIRONMENT", "development")

    # 🔒 クッキーの設定を完璧に修正
    # access_token はJavaScriptに触らせない(httponly=True)、全体で使う(path="/")
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=(ENV=="production"), max_age=3600, path="/")
    # csrf_token は画面側から読ませる(httponly=False)、全体で使う(path="/")
    response.set_cookie(key="csrf_token", value=current_csrf_token, httponly=False, path="/")

    return response


# ----------------------------------------------------
# 👤 5. ログインユーザー取得用共通関数 (Depends)
# ----------------------------------------------------
def get_current_user(request: Request, db: Session = Depends(get_db), access_token: str = Cookie(None)):
    if not access_token:
        return RedirectResponse(url="/account/login", status_code=303)
    username = verify_access_token(access_token)

    if not username:
        return RedirectResponse(url="/account/register", status_code=303)
    
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        return RedirectResponse(url="/account/register", status_code=303)

    return user


# ----------------------------------------------------
# 6. ログアウト機能 (POST)
# ----------------------------------------------------
@router.post("/account/logout", dependencies=[Depends(verify_csrf_token)])
def logout():
    response = RedirectResponse(url="/account/login", status_code=303)
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="csrf_token", path="/")
    return response