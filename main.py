from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.schemas import TodoCreate
from app import crud, models
from datetime import datetime

# 起動時にテーブル作成
Base.metadata.create_all(bind=engine, checkfirst=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# データベースセッションの依存関係（一元化）
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. todo一覧表示
@app.get("/api/todo", response_class=HTMLResponse)
async def read_root(request: Request, skip: int = 0, limit: int = 10, completed: bool = None, db: Session = Depends(get_db), q: str = None,):
    query = db.query(models.Todo)
    
    if completed is not None:
        query = query.filter(models.Todo.status == completed)

    if q:
        query = query.filter(
            (models.Todo.title.contains(q)) | (models.Todo.description.contains(q))
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
            "search_query": q or ""
        }
    )

# 2. todo作成フォーム表示用
@app.get("/todo/create", response_class=HTMLResponse)
async def show_todo_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="todo_create.html"
    )

# 3. todo詳細表示
@app.get("/api/todo/{todo_id}", response_class=HTMLResponse)
async def get_todo_detail(request: Request, todo_id: int, db: Session = Depends(get_db)):
    todo_data = crud.get_todo(db, todo_id)
    if todo_data is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return templates.TemplateResponse(
        request=request,
        name="todo_detail.html",
        context={"todo": todo_data}
    )

# todo作成処理
@app.post("/api/todo") 
async def post_todo_create(
    title: str = Form(...),
    due_date: datetime =  Form(...), 
    description: str = Form(...),
    status: str = Form("false"),  
    tag: str = Form(""),    
    link: str = Form(None),
    memo: str = Form(None),
    db: Session = Depends(get_db),
):
    is_completed = True if status == "完了" else False
    
    todo_in = TodoCreate(
        title=title,
        description=description,
        status=is_completed,
        tag=tag,
        link=link,
        memo=memo,
        due_date=due_date 
    )
    
    crud.create_todo(db=db, todo=todo_in)
    
    return RedirectResponse(url="/api/todo", status_code=303)

# 5. todo削除処理
@app.post("/api/todo/{todo_id}")  
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    crud.delete_todo(db, todo_id)
    return RedirectResponse(url="/api/todo", status_code=303)

# 6. tag一覧表示
@app.get("/api/tag", response_class=HTMLResponse)
async def get_tag_list(request: Request, skip: int = 0, limit: int = 10, q: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Tag)

    if q:
        query = query.filter(
            (models.Tag.title.contains(q)) | (models.Tag.description.contains(q))
        )

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
            "search_query": q or ""
        }
    )

# 7. tag詳細表示
@app.get("/api/tag/{tag_id}", response_class=HTMLResponse)
async def get_tag_detail(request: Request, tag_id: int):
    tag_data = {
        "id": tag_id,
        "title": "sample tag",
        "created_at": "2025-12-15",
        "description": "これはサンプルの詳細説明です。",
        "usage": "これはサンプルの使用方法です。"
    }
    return templates.TemplateResponse(
        request=request,
        name="tag_detail.html",
        context={"tag": tag_data}
    )