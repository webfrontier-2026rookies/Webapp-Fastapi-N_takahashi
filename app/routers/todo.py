from fastapi import FastAPI, Request, Depends, Form, HTTPException, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import TodoCreate
from app import crud, models
from datetime import datetime
import logging
from pydantic import HttpUrl, ValidationError
from typing import Optional
import shutil
from app.schemas import TodoWithTagUpdate
from app.routers.account import get_current_user
import secrets

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

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/todo")

@app.on_event("startup")
def on_startup():
    check_disk_space()

router = APIRouter()

# todo一覧表示
@router.get("/api/todo", response_class=HTMLResponse)
async def read_root(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    completed: bool | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    csrf_token = secrets.token_urlsafe(32)

    if isinstance(current_user, RedirectResponse):
        return current_user
    
    query = db.query(models.Todo).filter(models.Todo.username == current_user.username)

    if completed is not None:
        query = query.filter(models.Todo.status == completed)

    if q:
        safe_q = escape_like(q)
        search_param = f"%{safe_q}%"
        query = query.filter(
            models.Todo.title.ilike(search_param, escape="\\") |
            models.Todo.description.ilike(search_param, escape="\\")
        )

    query = query.order_by(models.Todo.created_at.asc())

    total_count = query.count()

    query = query.offset(skip).limit(limit)

    todo_list = query.all()

    active_todos = [t for t in todo_list if not t.status]
    completed_todos = [t for t in todo_list if t.status]

    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
    current_page = (skip // limit) + 1

    response = templates.TemplateResponse(
        request=request,
        name="todo_list.html",
        context={
            "request": request,
            "todo_list": todo_list,
            "active_todos": active_todos,
            "completed_todos": completed_todos,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": current_page,
            "current_limit": limit,
            "current_skip": skip,
            "search_param": q or "",
            "csrf_token": csrf_token,
        },
    )

    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        path="/"
    )
    return response

# todo詳細表示
@router.get("/api/todo/{todo_id}", response_class=HTMLResponse)
async def get_todo_detail(request: Request, todo_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    todo_data = db.query(models.Todo).filter(
        models.Todo.id == todo_id,
        models.Todo.username == current_user.username).first()
    
    #todoデータが存在しない場合のエラーハンドリング
    if todo_data is None:
        logger.error(f"【Todoデータエラー】ID {todo_id} のTodoデータが見つからないか、アクセス権がありません。")
        raise HTTPException(status_code=404, detail="Todoデータは存在しません")
    
    return templates.TemplateResponse(
        request=request,
        name="todo_detail.html",
        context={"todo": todo_data}
    )

# todo作成フォーム表示用
@router.get("/todo/create")
async def show_todo_form(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    tags = db.query(models.Tag).order_by(models.Tag.title).all()
    return templates.TemplateResponse(
        request=request, name="todo_create.html", context={"tags": tags},
    )

# todo作成処理
@router.post("/api/todo")
async def post_todo_create(
    request: Request,
    title: str = Form(...),
    due_date: datetime =  Form(...), 
    description: str = Form(...),
    status: Optional[str] = Form(None),
    link: str = Form(None),
    memo: str = Form(None),
    db: Session = Depends(get_db),
    tag_ids: list[int] = Form(default=[]),
    current_user: models.User = Depends(get_current_user)
):
    if isinstance(current_user, RedirectResponse):
        return current_user

    #期限が過去の日付のときのエラー文
    if due_date < datetime.now():
        logger.warning(f"【期限エラー】過去の日付が入力されました: {due_date}")
        raise HTTPException(status_code=400, detail="期限は未来の日付を指定してください")
    
    #必須項目が入力されていないときのエラー文
    if not title or not description or not due_date or status is None or not tag_ids:
        logger.error("入力されていない項目があります。") 

        raise HTTPException(status_code=400, detail="必須項目が入力されていません")
    
    #URLがhttp;//またはhttps://で始まる形式でないときのエラー文
    if link:
        try:
            HttpUrl(link)
        except ValidationError:
            logger.warning(f"【URL形式エラー】不正なURL形式です: {link}")
            raise HTTPException(status_code=400, detail="URL形式が不正です")

    is_completed = True if status == "true" else False

    todo_in = TodoCreate(
        title=title,
        description=description,
        status=is_completed,
        tag_ids=tag_ids,
        link=link,
        memo=memo,
        due_date=due_date 
    )

    logger.debug(f"【デバッグ】画面からPOSTされた直後の生の辞書データ: {todo_in.model_dump()}")

    #どこまで進んだかのデバッグ文
    logger.debug("【デバッグ】これよりデータベースへの保存処理を開始します...")
    
    #todo作成の完了のログ
    logger.info(f"Todoが作成されました。タイトル: {todo_in.title}, 作成日時: {datetime.now()}, 詳細: {todo_in.description}, 期限: {todo_in.due_date}, タグ: {todo_in.tag_ids}, リンク: {todo_in.link}, メモ: {todo_in.memo}")
    crud.create_todo_with_tags(db=db, todo_data=todo_in, tag_ids=tag_ids, username=current_user.username)
    return RedirectResponse(url="/api/todo", status_code=303)

# todoステータス変更処理
@router.post("/api/todo/{todo_id}/toggle")
async def toggle_todo_status(
    todo_id: int,
    status: Optional[str] = Form(...),
    db: Session = Depends(get_db)
):
    db_todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    db_todo.status = (status == "true")
    db.commit()
    return RedirectResponse(url="/api/todo", status_code=303)


# todo削除処理
@router.delete("/api/todo/{todo_id}")  
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    crud.delete_todo(db, todo_id)
    #todo削除の完了のログ
    logger.info(f"Todo(ID: {todo_id})が削除されました。")
    return {"status": "success", "message": "Todo deleted successfully"}


#todo更新画面表示
@router.get("/todo/{todo_id}/edit")
async def show_todo_update(todo_id: int, request: Request, db: Session = Depends(get_db)):
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="TODOが見つかりません")
        
    tags = db.query(models.Tag).order_by(models.Tag.title).all() 
    
    return templates.TemplateResponse(
        request=request, 
        name="todo_update.html",  
        context={"request": request, "todo": todo, "tags": tags} 
    )


#todo更新処理

@router.put("/api/todo/{todo_id}")
async def update_todo_with_tag(
    todo_id: int, 
    data: TodoWithTagUpdate,  
    db: Session = Depends(get_db)
):
    db_todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    tags = db.query(models.Tag).filter(models.Tag.id.in_(data.tag_ids)).all()
    if not db_todo:
        raise HTTPException(status_code=404, detail="TODOが見つかりません")
    
    db_todo.title = data.title
    db_todo.description = data.description
    db_todo.due_date = data.due_date
    db_todo.tags = tags
    db.commit()
    db.refresh(db_todo)
    
    return {"status": "success", "message": "TODOとタグの更新が完了しました"}