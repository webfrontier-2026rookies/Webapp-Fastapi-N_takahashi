import sys
import os

from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from main import app
from app.models import Tag, TodoTag
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
    db.query(Tag).delete()
    
    test_tag = Tag(
        title="一覧表示のテスト用TAG",
        description="このTAGが画面やAPIから見えれば合格です",
        usage="aiueo",
        username=2525,
    )
    db.add(test_tag)
    db.commit()

    response = client.get("/api/tag")

    assert response.status_code == 200

    db.close()

#tagの作成ができるかどうかのテストコード
def test_tag_create():
    db = next(get_db())
    db.query(TodoTag).delete()
    db.query(Tag).delete()

    tag = Tag(
        title="プログラミングのテスト",
        description="FastAPIの勉強を書く", 
        username=2525,
        usage="wwwww"
    )

    db.add(tag)
    db.commit()

    response = client.post("/api/tag", data={"title": "プログラミングの勉強","description": "FastAPIのテストを書く","usage": "wwwww"})   
    assert response.status_code == 200

    db.close()