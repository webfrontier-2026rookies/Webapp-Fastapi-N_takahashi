from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- トップページ (/) 用の道 ---
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,         
        name="todo_list.html",  
        context={"todos": []}    
    )

