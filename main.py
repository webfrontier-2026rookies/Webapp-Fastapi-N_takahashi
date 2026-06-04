from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app import models
import os
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.routers import account, todo, tag # インポートをスッキリ1箇所に統合
import secrets
from contextlib import asynccontextmanager

# ----------------------------------------------------
# 🛡️ 1. 起動時に「1回だけ」安全に実行されるエリアを定義
# ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ワーカーが何人同時に立ち上がろうが、ここなら100%安全に1回だけテーブルが作られます！
    models.Base.metadata.create_all(bind=engine)
    yield

# ----------------------------------------------------
# 🚀 2. FastAPI本体の起動（lifespanをここで1回だけ渡す！）
# ----------------------------------------------------
app = FastAPI(lifespan=lifespan)

# 静的ファイル（CSSなど）の読み込み設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# ----------------------------------------------------
# 🔒 3. セキュリティ・ミドルウェア設定
# ----------------------------------------------------
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
ALLOWED_HOSTS = os.getenv("ENVIRONMENT", "development")
ENV = os.getenv("ENVIRONMENT", "development")

if ENV == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "frame-ancestors 'none'"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ----------------------------------------------------
# 🔗 4. 各ルーターをアプリに合体（登録順序を最適化！）
# ----------------------------------------------------
app.include_router(account.router)  # ログイン関連を最優先に
app.include_router(todo.router)
app.include_router(tag.router)

# ----------------------------------------------------
# ⚙️ 5. 各種共通エンドポイント
# ----------------------------------------------------
# 💡 URLの衝突を防ぐため、生存確認用URLを /api/health に変更しました！
@app.get("/api/health")
def health_check():
    return {"status": "running", "message": "FastAPIアプリは正常に起動しています"}

@app.exception_handler(CsrfProtectError)
async def csrf_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

@app.get("/api/init-session")
def init_session(response: Response):
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        samesite="lax",
        path="/" # 👈 Cookieの有効範囲を全体に広げてすれ違いを防止！
    )
    return {"status": "session_initialized"}