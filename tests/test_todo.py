import sys
import os
from datetime import datetime

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
    
    db.query(TodoTag).delete()
    db.query(Todo).delete()

    # 💡 タグの指定（tag_ids="テスト" など）を完全に削除して、純粋なTODOモデルの項目だけにします
    todo = Todo(
        title="todoの追加テスト",
        description="todoの追加テストができるかどうかの確認",
        due_date=datetime.now(),
        status=False,
    )

    db.add(todo)
    db.commit()

    # 💡 ここでAPIを叩くときは、ルーター側のPydanticが「tag_id」や「tag_ids」を求めている可能性があるので、もし422エラーが出たらここにデータを追加します
    response = client.post(
        "/api/todo",
        json={
            "title": "todoの追加テスト",
            "description": "todoの追加テストができるかどうかの確認",
        }
    )   

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
        status=False,
    )
    db.add(test_todo)
    db.commit()

    # 1. 画面用のURLをGETで叩く
    response = client.get("/api/todo")

    # 2. ステータスコードが 200 OK かチェック
    assert response.status_code == 200
    
    # 3. ❌ response.json() は絶対に使わない！
    # ⭕ 代わりに、返ってきたHTMLの文字（text）の中に、さっき入れたタイトルが含まれているか検証する
    assert "一覧表示のテスト用TODO" in response.text

    db.close()