from fastapi import FastAPI, Request, Depends, Form, HTTPException, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import  TagCreate
from app import crud, models
from datetime import datetime
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import shutil
from app.schemas import TagUpdate
from app.routers.account import get_current_user

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

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/tag")

@app.on_event("startup")
def on_startup():
    check_disk_space()

router = APIRouter(tags=["タグ管理"])

#tag一覧表示
@router.get("/api/tag", response_class=HTMLResponse)
async def get_tag_list(
    request: Request, 
    skip: int = 0, 
    limit: int = 10, 
    q: str = None, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):

    if isinstance(current_user, RedirectResponse):
        return current_user
    
    query = db.query(models.Tag).filter(models.Tag.username == current_user.username)

    if q:
        search_param = f"%{q}%"
        query = query.filter(
            (models.Tag.title.ilike(search_param)) | (models.Tag.description.ilike(search_param))
        )
        logger.info(f"【タグ検索成功】キーワード '{q}' でタグの検索が成功しました。")
    else:
        logger.info("【アクセス】 タグ一覧ページが表示されました。")

    query = query.order_by(models.Tag.created_at.asc())

    total_count = query.count()

    query = query.offset(skip).limit(limit)

    tag_list = query.all()
        
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
    current_page = (skip // limit) + 1
    
    return templates.TemplateResponse(
        request=request,
        name="tag_list.html",
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
async def get_tag_detail(request: Request, tag_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    tag_data = db.query(models.Tag).filter(models.Tag.id == tag_id, models.Tag.username == current_user.username).first()
    #tag詳細表示の完了のログ

    #tagデータが存在しない場合のエラーハンドリング
    if tag_data is None:
        logger.error(f"【Tagデータエラー】ID {tag_id} のTagデータが見つかりませんでした。")
        raise HTTPException(status_code=404, detail="Tagデータは存在しません")
    
    logger.info(f"【アクセス】タグ詳細ページ(ID: {tag_id})が表示されました。")
        
    return templates.TemplateResponse(
        request=request,
        name="tag_detail.html",
        context={"tag": tag_data}
    )

# tag作成フォーム表示用
@router.get("/tag/create", response_class=HTMLResponse)
async def show_tag_form(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    return templates.TemplateResponse(
        request=request,
        name="tag_create.html"
    )

#tag作成処理
@router.post("/api/tag") 
async def post_tag_create(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    usage: str = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if isinstance(current_user, RedirectResponse):
        return current_user
        
    # 必須項目が入力されていないときのエラー文
    if not title or not description:
        logger.error("入力されていない項目があります。") 
        raise HTTPException(status_code=400, detail="必須項目が入力されていません")
        
    tag_in = TagCreate(
        title=title,
        description=description,
        usage=usage,
        username=current_user.username
    )
    
    logger.info(f"Tagが作成されました。タイトル: {tag_in.title}, 作成日時: {datetime.now()}, 詳細: {tag_in.description}, 使用方法: {tag_in.usage}")
    crud.create_tag(db=db, tag=tag_in, username=current_user.username)
    
    return RedirectResponse(url="/api/tag", status_code=303)

#tag削除処理
@router.delete("/api/tag/{tag_id}")  
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    crud.delete_tag(db, tag_id)
    return {"status": "success", "message": "Deleted successfully"}

#tag更新画面表示
@router.get("/tag/{tag_id}/edit")
async def show_todo_update(tag_id: int, request: Request, db: Session = Depends(get_db)):
    tag_data = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if not tag_data:
        raise HTTPException(status_code=404, detail="TAGが見つかりません")
        
    return templates.TemplateResponse(
        request=request, 
        name="tag_update.html", 
        context={"request": request, "tag": tag_data} 
    )

#tag更新処理
@router.put("/api/tag/{tag_id}")
async def update_tag(
    tag_id: int, 
    data: TagUpdate,  
    db: Session = Depends(get_db)
):
    update_tag = crud.update_tag(db,tag_id,data)

    if not update_tag:
        raise HTTPException(status_code=404, detail="TAGが見つかりません")
    
    return {"status": "success", "message": "タグの更新が完了しました"}