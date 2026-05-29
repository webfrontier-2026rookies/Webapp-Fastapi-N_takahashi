from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import todo, tag
from app.database import engine
from app import models
import os
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.routers import account

#起動時にデータベースのテーブルを自動作成する
models.Base.metadata.create_all(bind=engine)

# 🚀 FastAPI本体の起動
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

#CORS設定
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

#TODOとタグの部品をアプリにガッチャンコ
app.include_router(todo.router)
app.include_router(tag.router)

#ルートURL（生存確認用）
@app.get("/api/todo")
def read_root():
    return {"status": "running", "message": "FastAPIアプリは正常に起動しています"}

@app.exception_handler(CsrfProtectError)
async def csrf_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

app.include_router(account.router)