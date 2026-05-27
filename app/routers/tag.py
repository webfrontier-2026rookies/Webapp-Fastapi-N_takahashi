from fastapi import FastAPI, Request, Depends, Form, HTTPException, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import  TagCreate,  TagUpdate
from app import crud, models
from datetime import datetime
import logging
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database import engine
import shutil

#ディスク容量が10%を下回っているときの警告ログ
def check_disk_space():
    total, used,free = shutil.disk_usage("/")
    free_percentage = (free/total) * 100
    if free_percentage < 10:
        logger.warning(f"【ディスク容量警告】ディスクの空き容量が10%を下回っています。現在の空き容量: {free_percentage:.2f}%")

#独自のIP取得の関数
def get_real_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

limiter = Limiter(key_func=get_remote_address)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def on_startup():
    check_disk_space()

router = APIRouter()

@router.get("/api/tag", response_class=HTMLResponse)
async def get_tag_list(request: Request, skip: int = 0, limit: int = 10, q: str = None, db: Session = Depends(get_db)):
    #tag一覧表示の完了のログ
    logger.info("【アクセス】 タグ一覧ページが表示されました。")

    query = db.query(models.Tag)

    #キーワード検索
    if q:
        search_param = f"%{q}%"
        query = query.filter(
            (models.Tag.title.ilike(search_param)) | (models.Tag.description.ilike(search_param))
        )

    #検索成功のログ
    logger.info(f"【タグ検索成功】キーワード '{q}' でタグの検索が成功しました。")

    
    #作成日時の昇順で並び替え
    query = query.order_by(models.Tag.created_at.asc())

    total_count = query.count()

    tag_list = query.offset(skip).limit(limit).all()
        
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
    current_page = (skip // limit) + 1
    
    return templates.TemplateResponse(
        request=request,
        name="tag/tag_list.html",
        context={
            "tag_list": tag_list,
            "current_limit": limit,
            "current_skip": skip,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": current_page,
            "search_param": q or ""
        }
    )

# tag詳細表示
@router.get("/api/tag/{tag_id}", response_class=HTMLResponse)
async def get_tag_detail(request: Request, tag_id: int, db: Session = Depends(get_db)):

    #tag詳細表示の完了のログ
    logger.info(f"【アクセス】タグ詳細ページ(ID: {tag_id})が表示されました。")

    tag_data = crud.get_tag_by_id(db, tag_id)
    
    #tagデータが存在しない場合のエラーハンドリング
    if tag_data is None:
        logger.error(f"【Tagデータエラー】ID {tag_id} のTagデータが見つかりませんでした。")
        raise HTTPException(status_code=404, detail="Tagデータは存在しません")
        
    return templates.TemplateResponse(
        request=request,
        name="tag/tag_detail.html",
        context={"tag": tag_data}
    )

# tag作成フォーム表示用
@router.get("/tag/create", response_class=HTMLResponse)
async def show_tag_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="tag/tag_create.html"
    )

# tag作成処理
@router.post("/api/tag") 
async def post_tag_create(
    title: str = Form(...),
    description: str = Form(...),
    usage: str = Form(None),
    db: Session = Depends(get_db),
):
    #必須項目が入力されていないときのエラー文
    if not title or not description:
        logger.error("入力されていない項目があります。") 

        raise HTTPException(status_code=400, detail="必須項目が入力されていません")
    tag_in = TagCreate(
        title=title,
        description=description,
        usage=usage
    )
    logger.info(f"Tagが作成されました。タイトル: {tag_in.title}, 作成日時: {datetime.now()}, 詳細: {tag_in.description}, 使用方法: {tag_in.usage}")
    crud.create_tag(db=db, tag=tag_in)
    return RedirectResponse(url="/api/tag", status_code=303)

#tag削除処理
@router.delete("/api/tag/{tag_id}")  
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    crud.delete_tag(db, tag_id)
    return {"status": "success", "message": "Deleted successfully"}

#tag更新処理
@router.put("/api/tag/{tag_id}")
async def update_tag(
    tag_id: int,
    title: str = Form(...),
    created_at: datetime = Form(None),
    description: str = Form(...),
    usage: str = Form(None),
    db: Session = Depends(get_db)
):
    tag_in = TagUpdate(
        title=title,
        created_at=created_at,
        description=description,
        usage=usage
    )
    logger.info(f"Tagが更新されました。タイトル: {tag_in.title}, 作成日時: {datetime.now()}, 詳細: {tag_in.description}, 使用方法: {tag_in.usage}")
    crud.update_tag(db=db, tag_id=tag_id, tag=tag_in)

    if update_tag is None:
        logger.error(f"【Tag更新エラー】ID {tag_id} のTagデータが見つかりませんでした。")
        raise HTTPException(status_code=404, detail="Tagが見つかりませんでした。")
    
    return RedirectResponse(url="/api/tag", status_code=303
)

#アプリ起動完了のログ
logger.info("アプリが起動しました。データベース接続も成功しています。")