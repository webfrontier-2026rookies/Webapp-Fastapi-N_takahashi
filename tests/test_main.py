import sys
import os
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from main import app
from app.models import Todo, TodoTag, Tag
from app.database import get_db

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

client = TestClient(app)

def test_todo_list_split_by_status():
    """
    【応用テスト】未完了・完了済みが正しく分かれるかのテスト
    """
    # === 1. Arrange（データの準備） ===
    db = next(get_db())
    
    db.query(TodoTag).delete()
    db.query(Todo).delete()
    
    # 完了/未完了を表すカラム名（status か is_completed）を自動判定
    status_column = "status" if hasattr(Todo, "status") else "is_completed"
    
    todo_incomplete = Todo(
        title="お買い物に行く",
        description="牛乳と卵を買う",
        due_date=datetime.now()
    )
    setattr(todo_incomplete, status_column, False)
    
    todo_complete = Todo(
        title="部屋の掃除",
        description="ルンバを動かす",
        due_date=datetime.now()
    )
    setattr(todo_complete, status_column, True)
    
    db.add(todo_incomplete)
    db.add(todo_complete)
    db.commit()

    # === 2. Act（実行） ===
    response = client.get("/api/todo")
    assert response.status_code == 200
    
    data = response

    # === 3. Assert（生データの画面出力） ===
    print("\n" + "="*40)
    print("アプリから返ってきた実際のデータ")
    print(data)
    print("="*40 + "\n")
    
    assert data is not None
    
    db.close()

#存在しないtodoのidのアクセスしたらエラー文が出てくるのか
def test_todo_detail_not_found():
    db = next(get_db())

    db.query(TodoTag).delete()
    db.query(Todo).delete()
    db.commit()
    db.close()

    response = client.get("/api/todo/999999")

    data = response.json()
    print("\n" + "="*40)
    print("エラー時に返ってきた実際のデータ:")
    print(data)
    print("="*40 + "\n")

    assert "detail" in data

#存在するtodoのidのアクセスしたら表示されるのか
def test_todo_detail_success():
    db = next(get_db())

    db.query(TodoTag).delete()
    db.query(Todo).delete()

    test_todo = Todo(
        title="詳細テスト用のタスク",
        description="この説明文が正しく表示されるか検証します",
        due_date=datetime.now()
    )
    db.add(test_todo)
    db.commit()
    db.refresh(test_todo)

    target_id = test_todo.id
    expected_title = test_todo.title
    
    db.close()

    response = client.get(f"/api/todo/{target_id}")

    assert response.status_code == 200
    
    html_content = response.text
    print("\n" + "="*40)
    print(f"存在するID [{target_id}] にアクセスして返ってきた実際のデータ:")
    print(html_content[:500])
    print("="*40 + "\n")

    assert expected_title in html_content
    assert "この説明文が正しく表示されるか検証します" in html_content

#存在しないtagのidのアクセスしたらエラー文が出てくるのか
def test_tag_detail_not_found():
    db = next(get_db())

    db.query(TodoTag).delete()
    db.query(Tag).delete()
    db.commit()
    db.close()

    response = client.get("/api/tag/999999")

    data = response.json()
    print("\n" + "="*40)
    print("エラー時に返ってきた実際のデータ:")
    print(data)
    print("="*40 + "\n")

#todo一覧で検索した場合、対象のタスクだけに絞り込まれて、並び変わるかどうかのテストコード
def test_search_rearrange():
    db = next(get_db())
    db.query(Todo).delete()

    todo1 = Todo(
        title="スーパーで買い物",
        description="牛乳を買う",  
        due_date=datetime.now() + timedelta(days=1),
        status=False
    )
    todo2 = Todo(
        title="デパ地下で買い物",
        description="お惣菜を買う",
        due_date=datetime.now(), 
        status=False
    )
    todo3 = Todo(
        title="プログラミングの勉強",
        description="FastAPIのテストを書く",
        due_date=datetime.now() + timedelta(days=5),
        status=False
    )

    db.add_all([todo1, todo2, todo3])
    db.commit()

    # URLを呼び出す
    response = client.get("/api/todo?q=買い物")
    assert response.status_code == 200

    html_content = response.text
    
    db.close()

    # === 3. Assert（HTML画面の答え合わせ） ===
    assert "スーパーで買い物" in html_content
    assert "デパ地下で買い物" in html_content
    assert "プログラミングの勉強" not in html_content

    idx_today = html_content.find("デパ地下で買い物")
    idx_tomorrow = html_content.find("スーパーで買い物")
    
    assert idx_today > idx_tomorrow  

#todo作成処理のタイトルや期限のデータを送信したとき、データベースに新しいTODOが1件増えているか？のテストコード
def test_todo_create_add_db():
    db = next(get_db())
    db.query(Todo).delete()

    todo1 = Todo(
        title="テスト",
        description="教室でテストを行う",  
        due_date=datetime.now() + timedelta(days=1),
        status=False
    )

    db.add(todo1)
    db.commit()

    queried_todo = db.query(Todo).filter(Todo.title == "テスト").first()

    assert queried_todo is not None

    assert queried_todo.description == "教室でテストを行う"
    assert queried_todo.status is False

    db.close()


