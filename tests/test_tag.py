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

#tagの一覧表示ができるかどうかのテストコード
def test_tag_list():
    db = next(get_db())
    db.query(TodoTag).delete()
    db.query(Tag).delete()
    
    test_tag = Tag(
        title="一覧表示のテスト用TAG",
        description="このTAGが画面やAPIから見えれば合格です",
        usage="使用方法"
    )
    db.add(test_tag)
    db.commit()

    response = client.get("/api/tag")

    assert response.status_code == 200
    
    assert "一覧表示のテスト用TAG" in response.text

    db.close()

#tagの詳細表示ができるかどうかのテストコード
def test_todo_detail_page():
    db = next(get_db())
    db.query(TodoTag).delete()
    db.query(Tag).delete()

    test_tag = Tag(
        title="詳細表示のテスト用TAG",
        description="このTAGが画面やAPIから見えれば合格です",
        usage="テスト"
    )

    db.add(test_tag)
    db.commit()
    db.refresh(test_tag) 

    response = client.get(f"/api/tag/{test_tag.id}")

    assert response.status_code == 200

#tagの削除ができるかどうかのテストコード
def test_tag_delete():
    db = next(get_db())
    db.query(Tag).delete()

    tag = Tag(
        title="todo削除テスト",
        usage="テスト確認の際",
        description="削除テスト確認", 
    )

    db.add(tag)
    db.commit()

    todo_id = tag.id
    db.close()

    response = client.delete(f"/api/tag/{todo_id}")

    assert response.status_code == 200

    new_db = next(get_db())
    deleted_tag = new_db.query(Todo).filter(Todo.id == todo_id).first()

    assert deleted_tag is None

    new_db.close()

