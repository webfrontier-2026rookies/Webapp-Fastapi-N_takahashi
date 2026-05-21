from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas import TodoCreate,  TagCreate, TodoUpdate, TagUpdate
from app import crud, models
from datetime import datetime
import logging
from pydantic import HttpUrl, ValidationError
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# データベースセッションの依存関係（一元化）
def get_db():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        yield db
    #データベースの接続エラー時のエラーハンドリング
    except OperationalError as e:
        logger.fatal(f"【データベース接続失敗】DBサーバーに接続できませんでした。エラー詳細: {e}")
        raise HTTPException(status_code=500, detail="データベース接続エラー")
    finally:
        db.close()
    

# todo一覧表示
@app.get("/api/todo", response_class=HTMLResponse)
async def read_root(request: Request, skip: int = 0, limit: int = 10, completed: bool = None, db: Session = Depends(get_db), q: str = None,):

    #todo一覧表示の完了のログ
    logger.info("【アクセス】 Todo一覧ページが表示されました。")

    query = db.query(models.Todo)

    if completed is not None:
        query = query.filter(models.Todo.status == completed)

    #キーワードの検索
    if q:
        search_param = f"%{q}%"
        query = query.filter(
            (models.Todo.title.ilike(search_param)) | (models.Todo.description.ilike(search_param))
        )
    
    #検索成功のログ
    logger.info(f"【Todo検索成功】キーワード '{q}' でTodoの検索が成功しました。")

    
    #作成日時の昇順で並び替え
    query = query.order_by(models.Todo.created_at.asc())

    #未完了の表
    active_todos = (
        db.query(models.Todo)
        .options(joinedload(models.Todo.tags))  
        .filter(models.Todo.status == False)
        .order_by(models.Todo.created_at.asc())
        .all()
    )
    #完了済みの表
    completed_todos = (
        db.query(models.Todo)
        .options(joinedload(models.Todo.tags))
        .filter(models.Todo.status == True)
        .order_by(models.Todo.created_at.asc())
        .all()
    )

    total_count = query.count()
        
    todo_list = query.offset(skip).limit(limit).all()
    
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
    current_page = (skip // limit) + 1
    
    return templates.TemplateResponse(
        request=request,
        name="todo_list.html",
        context={
            "todo_list": todo_list,
            "current_limit": limit,
            "current_skip": skip,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": current_page,
            "search_param": q or "",
            "active_todos": active_todos,
            "completed_todos": completed_todos,
        }
    )

# todo詳細表示
@app.get("/api/todo/{todo_id}", response_class=HTMLResponse)
async def get_todo_detail(request: Request, todo_id: int, db: Session = Depends(get_db)):
    todo_data = crud.get_todo_by_id(db, todo_id=todo_id)
    
    #todoデータが存在しない場合のエラーハンドリング
    if todo_data is None:
        logger.error(f"【Todoデータエラー】ID {todo_id} のTodoデータが見つかりませんでした。")
        raise HTTPException(status_code=404, detail="Todoデータは存在しません")
    return templates.TemplateResponse(
        request=request,
        name="todo_detail.html",
        context={"todo": todo_data}
    )

# todo作成フォーム表示用
@app.get("/todo/create")
async def show_todo_form(request: Request, db: Session = Depends(get_db)):
    tags = db.query(models.Tag).order_by(models.Tag.title).all()
    return templates.TemplateResponse(
        request=request, name="todo_create.html", context={"tags": tags},
    )


# tag一覧表示
@app.get("/api/tag", response_class=HTMLResponse)
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
@app.get("/api/tag/{tag_id}", response_class=HTMLResponse)
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
        name="tag_detail.html",
        context={"tag": tag_data}
    )

# tag作成フォーム表示用
@app.get("/tag/create", response_class=HTMLResponse)
async def show_tag_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="tag_create.html"
    )

# todo作成処理
@app.post("/api/todo") 
async def post_todo_create(
    title: str = Form(...),
    due_date: datetime =  Form(...), 
    description: str = Form(...),
    status: Optional[str] = Form(None),
    link: str = Form(None),
    memo: str = Form(None),
    db: Session = Depends(get_db),
    tag_ids: list[int] = Form(default=[]),
):
    
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
    
    #todo作成の完了のログ
    logger.info(f"Todoが作成されました。タイトル: {todo_in.title}, 作成日時: {datetime.now()}, 詳細: {todo_in.description}, 期限: {todo_in.due_date}, タグ: {todo_in.tag_ids}, リンク: {todo_in.link}, メモ: {todo_in.memo}")
    crud.create_todo_with_tags(db=db, todo_data=todo_in, tag_ids=tag_ids)
    return RedirectResponse(url="/api/todo", status_code=303)

# todoステータス変更処理
@app.post("/api/todo/{todo_id}/toggle")
async def toggle_todo_status(
    todo_id: int,
    status: bool = Form(...),
    db: Session = Depends(get_db)
):
    db_todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    db_todo.status = (status == "true")
    db.commit()
    return RedirectResponse(url="/api/todo", status_code=303)


# todo削除処理
@app.delete("/api/todo/{todo_id}")  
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    crud.delete_todo(db, todo_id)
    #todo削除の完了のログ
    logger.info(f"Todo(ID: {todo_id})が削除されました。")
    return {"status": "success", "message": "Todo deleted successfully"}


# tag作成処理
@app.post("/api/tag") 
async def post_tag_create(
    title: str = Form(...),
    created_at: datetime = Form(None),
    description: str = Form(...),
    usage: str = Form(None),
    db: Session = Depends(get_db),
):
    #必須項目が入力されていないときのエラー文
    if not title or not description or not created_at:
        logger.error("入力されていない項目があります。") 

        raise HTTPException(status_code=400, detail="必須項目が入力されていません")
    tag_in = TagCreate(
        title=title,
        created_at=created_at,
        description=description,
        usage=usage
    )
    logger.info(f"Tagが作成されました。タイトル: {tag_in.title}, 作成日時: {datetime.now()}, 詳細: {tag_in.description}, 使用方法: {tag_in.usage}")
    crud.create_tag(db=db, tag=tag_in)
    return RedirectResponse(url="/api/tag", status_code=303)

# tag削除処理
@app.delete("/api/tag/{tag_id}")  
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    crud.delete_tag(db, tag_id)
    return {"status": "success", "message": "Deleted successfully"}

#todo更新処理
@app.put("/api/todo/{todo_id}")
async def update_todo(
    todo_id: int,
    title: str = Form(...),
    due_date: datetime = Form(...),
    description: str = Form(...),
    status: Optional[str] = Form(None),
    tag: str = Form(""),
    link: str = Form(None),
    memo: str = Form(None),
    db: Session = Depends(get_db)
):
    
    todo_in = TodoUpdate(
        title=title,
        description=description,
        status=status,
        tag=tag,
        link=link,
        memo=memo,
        due_date=due_date
    )
    
    crud.update_todo(db=db, todo_id=todo_id, todo=todo_in)

    if update_todo is None:
        logger.error(f"【Todo更新エラー】ID {todo_id} のTodoデータが見つかりませんでした。")
        raise HTTPException(status_code=404, detail="Todoが見つかりませんでした。")
    
    return RedirectResponse(url="/api/todo", status_code=303
)

#tag更新処理
@app.put("/api/tag/{tag_id}")
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