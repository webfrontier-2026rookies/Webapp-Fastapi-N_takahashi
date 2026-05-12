from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def read_root(request: Request):
    todo_list = [
        {
            "id": 1, 
            "title": "買い物", 
            "description": "卵と牛乳を買う", 
            "due_date": "2026-05-12", 
            "status": "未完了", 
            "tag": "生活"
        },
        {
            "id": 2, 
            "title": "FastAPIの勉強", 
            "description": "Jinja2のテンプレートをマスターする", 
            "due_date": "2026-05-13", 
            "status": "進行中", 
            "tag": "学習"
        }
    ]

    return templates.TemplateResponse(
        request=request,         
        name="todo_list.html",  
        context={"todo_list": todo_list}    
    )

@app.get("/todo/{todo_title}")
async def get_todo_detail(request: Request, todo_title: str):
    todo_data = {
        "title": todo_title,
        "created_at": "2026-05-10",
        "description": "これはサンプルの詳細説明です。",
        "due_date": "2026-05-20",
        "status": "進行中",
        "tag": "仕事",
        "link": "https://example.com",
        "memo": "これはサンプルのメモです。"
    }

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