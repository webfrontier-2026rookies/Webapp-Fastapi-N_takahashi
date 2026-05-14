from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import Todo, Tag, TodoTag
from app.schemas import TodoCreate, TodoUpdate
from app import crud

# アプリ起動時にPostgreSQLにテーブルを作成する
Base.metadata.create_all(bind=engine,checkfirst=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def read_root(request: Request):
    db = next(get_db())
    todo_list = db.query(Todo).all()
    return templates.TemplateResponse(
        request=request,
        name="todo_list.html",
        context={"todo_list": todo_list}
    )

@app.get("/todo")
async def get_todo_list(request: Request):
    db = next(get_db())
    todo_list = db.query(Todo).all()
    return templates.TemplateResponse(
        request=request,         
        name="todo_list.html",  
        context={"todo_list": todo_list}    
    )

@app.get("/todo/{todo_title}")
async def get_todo_detail(request: Request, todo_title: str, db: Session = Depends(get_db)):
        todo_data = crud.get_todo_by_title(db, todo_title)

        return templates.TemplateResponse(
            request=request,
            name="todo_detail.html",
            context={"todo": todo_data}
        )

@app.get("/tag")
async def get_tag_list(request: Request):
    tag_list = [
        {
            "id": 1,
            "title": "散歩",
            "created_at": "2025-12-15"
        },
        {
            "id": 2,
            "title": "買い物",
            "created_at": "2025-12-16"
        }
    ]
    return templates.TemplateResponse(
        request=request,         
        name="tag_list.html",  
        context={"tag_list": tag_list}
    )

@app.get("/tag/{tag_title}")
async def get_tag_detail(request: Request, tag_title: str):
    tag_data = {
        "title": tag_title,
        "created_at": "2025-12-15",
        "description": "これはサンプルの詳細説明です。",
        "usage": "これはサンプルの使用方法です。"
    }

    return templates.TemplateResponse(
        request=request,
        name="tag_detail.html",
        context={"tag": tag_data}
    )