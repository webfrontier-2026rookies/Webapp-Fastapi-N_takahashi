import sys
import os

from fastapi.testclient import TestClient
from main import app
from app.models import Todo, TodoTag, Tag
from app.database import get_db

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

client = TestClient(app)

#tagを作成できるかのテストコード作成
def test_tag_create():
    db = next(get_db())
    db.query(Todo).delete()

    tag = Tag(
        title="タグ作成テスト",
        usage="テストするとき",
        description="タグ作成テスト確認", 
    )

    db.add(tag)
    db.commit()

    response = client.post("/api/tag", data={"title": "タグ作成テスト", "description": "タグ作成テスト確認", "usage": "テストするとき"})   
    assert response.status_code == 200

    db.close()