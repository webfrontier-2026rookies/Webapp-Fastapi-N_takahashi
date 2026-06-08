from fastapi import FastAPI, Response
import os
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import account, todo, tag 
import secrets
from contextlib import asynccontextmanager
# main.py
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.database import  limiter

# 環境変数の読み込み
ENV = os.getenv("ENVIRONMENT", "development")
ALLOWED_HOSTS = [h for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h]
ALLOWED_ORIGINS = [o for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o]
# ----------------------------------------------------
# 🛡️ 1. 起動時に「1回だけ」安全に実行されるエリアを定義
# ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
# ----------------------------------------------------
# 🚀 2. FastAPI本体の起動（lifespanをここで1回だけ渡す！）
# ----------------------------------------------------
app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# ----------------------------------------------------
# 🔒 3. セキュリティ・ミドルウェア設定
# ----------------------------------------------------
if ENV == "production":
    if not ALLOWED_HOSTS:
        raise RuntimeError("ALLOWED_HOSTS must be set in production")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

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
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "connect-src 'self' https://cdn.jsdelivr.net; " # 👈【追加】裏での通信もjsdelivrを許可する！
            "frame-ancestors 'none'"
        )
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ----------------------------------------------------
# 🔗 4. 各ルーターをアプリに合体（登録順序を最適化！）
# ----------------------------------------------------
app.include_router(account.router) 
app.include_router(todo.router)
app.include_router(tag.router)

# ----------------------------------------------------
# ⚙️ 5. 各種共通エンドポイント
# ----------------------------------------------------

@app.get("/api/init-session")
def init_session(response: Response):
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        samesite="lax",
        path="/" 
    )
    return {"status": "session_initialized"}

