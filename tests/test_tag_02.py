import sys
import os

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

#tagの更新ができるかどうかのテストコード作成
def test_todo_update():
    db = next(get_db())
    db.query(TodoTag).delete()
    db.query(Tag).delete()

    test_tag = Tag(
        title="更新前のTAG",
        description="これから更新されます",
        usage="yyyy",
        username="kiki",
    )
    db.add(test_tag)
    db.commit()

    response = client.put(
        f"/api/tag/{test_tag.id}",
        json={
            "title": "更新後のTODOタイトル",
            "description": "無事に更新されました",
            "usage": "iiiii",
        }
    )
    assert response.status_code == 200

    db.refresh(test_tag)
    assert test_tag.title == "更新後のTODOタイトル"
    assert test_tag.description == "無事に更新されました"
    assert test_tag.usage == "iiiii"

    db.close()

#tagの削除ができるかどうかのテストコード
def test_tag_delete():
    db = next(get_db())
    db.query(Tag).delete()

    tag = Tag(
        title="todo削除テスト",
        usage="テスト確認の際",
        description="削除テスト確認", 
        username="kiki",
    )

    db.add(tag)
    db.commit()

    tag_id = tag.id
    db.close()

    response = client.delete(f"/api/tag/{tag_id}")

    assert response.status_code == 200

    new_db = next(get_db())
    deleted_tag = new_db.query(Tag).filter(Tag.id == tag_id).first()

    assert deleted_tag is None

    new_db.close()

#tagの詳細表示ができるかどうかのテストコード
def test_todo_detail_page():
    db = next(get_db())
    db.query(TodoTag).delete()
    db.query(Tag).delete()

    test_tag = Tag(
        title="詳細表示のテスト用TAG",
        description="このTAGが画面やAPIから見えれば合格です",
        usage="テスト",
        username=2525
    )

    db.add(test_tag)
    db.commit()
    db.refresh(test_tag) 

    response = client.get(f"/api/tag/{test_tag.id}")

    assert response.status_code == 200