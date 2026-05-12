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
        "description": "これはサンプルの詳細説明です。",
        "due_date": "2026-05-20",
        "status": "進行中",
        "tag": "仕事"
    }

    return templates.TemplateResponse(
        request=request,
        name="todo_detail.html",
        context={"todo": todo_data}
    )