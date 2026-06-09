import sys
import os

from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from main import app
from app.models import Todo, TodoTag
from app.database import get_db

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

client = TestClient(app)

#todoの一覧表示ができるかどうかのテストコード
def test_todo_list():
    db = next(get_db())
    db.query(TodoTag).delete()
    db.query(Todo).delete()
    
    test_todo = Todo(
        title="一覧表示のテスト用TODO",
        description="このTODOが画面やAPIから見えれば合格です",
        due_date=datetime.now(),
        status=False,
        username=2525,
    )
    db.add(test_todo)
    db.commit()

    response = client.get("/api/todo")

    assert response.status_code == 200

    db.close()

#todoの検索ができるかどうかのテストコード

#todoの作成ができるかどうかのテストコード
def test_todo_create():
    db = next(get_db())
    db.query(TodoTag).delete()
    db.query(Todo).delete()

    todo = Todo(
        title="プログラミングの勉強",
        due_date=datetime.now() + timedelta(days=5),
        description="FastAPIのテストを書く", 
        status=True,
        username="kiki",
        link="https://calendar.google.com/calendar/u/0/r",
        memo="aaaaaa",
    )

    db.add(todo)
    db.commit()

    response = client.post("/api/todo", data={"title": "プログラミングの勉強","description": "FastAPIのテストを書く","due_date": datetime.now() + timedelta(days=5),"status": True, "link": "https://calendar.google.com/calendar/u/0/r", "memo": "aaaaaa"})   
    assert response.status_code == 200

    db.close()