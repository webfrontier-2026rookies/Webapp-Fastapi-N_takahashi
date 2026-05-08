from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi import templates

app = FastAPI()

template = Jinja2Templates(directory= "templates")

@app.get("/search")
async def get_todo_list(request: Request, keyword: str = None):
    all_todos = [
        {"id": 1, "task": "Gitの勉強", "status": "完了"},
        {"id": 2, "task": "FastAPIの検索実装", "status": "進行中"},
        {"id": 3, "task": "HTMLテンプレート作成", "status": "未着手"},
        {"id": 4, "task": "Jinja2の練習", "status": "未着手"},
    ]

    if keyword: 
        display_todos = [todo for todo in all_todos if keyword.lower() in  todo["task"].lower()]
    else:
        display_todos = all_todos
    
    return templates.TemplateResponse("todo_list.html", {
        "request": request,
        "todos": display_todos,#絞り込んだ後のリストを渡す
        "keyword": keyword#検索窓に値を残すために渡す
    })