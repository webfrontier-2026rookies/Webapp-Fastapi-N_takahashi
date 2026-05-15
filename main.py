from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import Todo
from app.schemas import TodoCreate
from app import crud
from app import schemas

# 起動時にテーブル作成
Base.metadata.create_all(bind=engine, checkfirst=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Todo一覧表示
@app.get("/api/todo")
async def read_root(request: Request, skip: int = 0, limit: int = 100, completed: bool = None):
    db = next(get_db())
    todo_list = db.query(Todo)
    if completed is not None:
        todo_list = todo_list.filter(Todo.status == completed)
    todo_list = todo_list.offset(skip).limit(limit).all()
    return templates.TemplateResponse(
        request=request,
        name="todo_list.html",
        context={"todo_list": todo_list}
    )

# todo作成フォーム表示用
@app.get("/api/todo")
async def show_todo_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="todo_create.html"
    )

# Todo詳細表示
@app.get("/api/todo/{todo_id}")
async def get_todo_detail(request: Request, todo_id: int, db: Session = Depends(get_db)):
    todo_data = crud.get_todo_by_id(db, todo_id)
    return templates.TemplateResponse(
        request=request,
        name="todo_detail.html",
        context={"todo": todo_data}
    )

# Todo作成処理
@app.post("/todo") 
async def post_todo_create(
    title: str = Form(...),
    description: str = Form(...),
    status: str = Form("false"),  # HTMLのselectから送られるのは文字列なのでstrで受ける
    tag: str = Form(""),          # デフォルト値を空文字にする
    link: str = Form(None),
    memo: str = Form(None),
    db: Session = Depends(get_db),
):

    is_completed = True if status.lower() == "true" else False

    todo_create = TodoCreate(
        title=title,
        description=description,
        status=is_completed,
        tag=tag,
        link=link,
        memo=memo
    )

    created_todo = crud.create_todo(db, todo_create)
    
    # 成功したら一覧画面へリダイレクトさせるのが一般的です
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


@app.get("/api/tag")
async def get_tag_list(request: Request, skip: int = 0, limit: int = 100):
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

@app.get("/api/tag/{tag_id}")
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