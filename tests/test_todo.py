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

#todoリストを作成できるかのテストコード作成
def test_todo_create():
    db = next(get_db())
    db.query(Todo).delete()

    todo = Todo(
        title="プログラミングの勉強",
        due_date=datetime.now() + timedelta(days=5),
        description="FastAPIのテストを書く", 
        status=False
    )

    db.add(todo)
    db.commit()

    response = client.post("/api/tag",data={"title": "プログラミングの勉強","description": "FastAPIのテストを書く","due_date": datetime.now() + timedelta(days=5),"status": False})   
    assert response.status_code == 200

    db.close()

#todoの一覧表示ができるかどうかのテストコード
def test_todo_list():
    db = next(get_db())
    db.query(TodoTag).delete()
    db.query(Todo).delete()
    
    test_todo = Todo(
        title="一覧表示のテスト用TODO",
        description="このTODOが画面やAPIから見えれば合格です",
        due_date=datetime.now(),
        status=False
    )
    db.add(test_todo)
    db.commit()

    response = client.get("/api/todo")

    assert response.status_code == 200
    
    assert "一覧表示のテスト用TODO" in response.text

    db.close()

#todoの詳細表示ができるかどうかのテストコード
def test_todo_detail_page():
    db = next(get_db())
    db.query(TodoTag).delete()
    db.query(Todo).delete()

    test_todo = Todo(
        title="詳細表示のテスト用TODO",
        description="このTODOが画面やAPIから見えれば合格です",
        due_date=datetime.now() + timedelta(days=5),
        status=False
    )

    db.add(test_todo)
    db.commit()
    db.refresh(test_todo) 

    response = client.get(f"/api/todo/{test_todo.id}")

    assert response.status_code == 200

#todoの削除ができるかどうかのテストコード
def test_tag_delete():
    db = next(get_db())
    db.query(Todo).delete()

    todo = Todo(
        title="todo削除テスト",
        due_date=datetime.now() + timedelta(days=6),
        status=False,
        description="削除テスト確認", 
    )

    db.add(todo)
    db.commit()

    todo_id = todo.id
    db.close()

    response = client.delete(f"/api/todo/{todo_id}")

    assert response.status_code == 200

    new_db = next(get_db())
    deleted_tag = new_db.query(Todo).filter(Todo.id == todo_id).first()

    assert deleted_tag is None

    new_db.close()

#todoの更新ができるかどうかのテストコード作成
def test_todo_update():
    # 1. データベースの準備
    db = next(get_db())
    db.query(TodoTag).delete()
    db.query(Todo).delete()

    test_todo = Todo(
        title="更新前のTODO",
        description="これから更新されます",
        due_date=datetime.now(),
        status=False,
    )
    db.add(test_todo)
    db.commit()

    # 2. 更新APIを叩く
    # 💡 URLを「test_todo.id」にし、引数を必ず「json=」にします！
    response = client.put(
        f"/api/todo/{test_todo.id}",
        json={
            "title": "更新後のTODOタイトル",
            "description": "無事に更新されました",
            "tag_id": 1
        }
    )

    print("\n🔥 FastAPIからのダメ出し内容（更新）:", response.json())
    assert response.status_code == 200

    # 3. DBの最終チェック
    db.refresh(test_todo)
    assert test_todo.title == "更新後のTODOタイトル"
    assert test_todo.description == "無事に更新されました"

    db.close()