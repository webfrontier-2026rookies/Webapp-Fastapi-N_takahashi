from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.schemas import TodoCreate,  TagCreate
from app import crud, models
from datetime import datetime

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

# todo一覧表示
@app.get("/api/todo", response_class=HTMLResponse)
async def read_root(request: Request, skip: int = 0, limit: int = 10, completed: bool = None, db: Session = Depends(get_db), q: str = None,):
    query = db.query(models.Todo)
    
    if completed is not None:
        query = query.filter(models.Todo.status == completed)

    if q:
        query = query.filter(
            (models.Todo.title.icontains(q)) | (models.Todo.description.icontains(q))
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

# todo詳細表示
@app.get("/api/todo/{todo_id}", response_class=HTMLResponse)
async def get_todo_detail(request: Request, todo_id: int, db: Session = Depends(get_db)):
    todo_data = crud.get_todo_by_id(db, todo_id)
    
    if todo_data is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return templates.TemplateResponse(
        request=request,
        name="todo_detail.html",
        context={"todo": todo_data}
    )

# todo作成フォーム表示用
@app.get("/todo/create", response_class=HTMLResponse)
async def show_todo_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="todo_create.html"
    )

# tag一覧表示
@app.get("/api/tag", response_class=HTMLResponse)
async def get_tag_list(request: Request, skip: int = 0, limit: int = 10, q: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Tag)
    if q:
        search_param = f"%{q}%"
        query = query.filter(
            (models.Tag.title.ilike(search_param)) | (models.Tag.description.ilike(search_param))
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
            "search_param": q or ""
        }
    )

# tag詳細表示
@app.get("/api/tag/{tag_id}", response_class=HTMLResponse)
async def get_tag_detail(request: Request, tag_id: int, db: Session = Depends(get_db)):
    tag_data = crud.get_tag_by_id(db, tag_id)
    
    if tag_data is None:
        raise HTTPException(status_code=404, detail="Tag not found")
        
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

# todoステータス変更処理
@app.post("/api/todo/{todo_id}/toggle")
async def toggle_todo_status(
    todo_id: int,
    status: str = Form(...),
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
    tag_in = TagCreate(
        title=title,
        created_at=created_at,
        description=description,
        usage=usage
    )
    crud.create_tag(db=db, tag=tag_in)
    return RedirectResponse(url="/api/tag", status_code=303)

# tag削除処理
@app.delete("/api/tag/{tag_id}")  
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    crud.delete_tag(db, tag_id)
    return {"status": "success", "message": "Deleted successfully"}


