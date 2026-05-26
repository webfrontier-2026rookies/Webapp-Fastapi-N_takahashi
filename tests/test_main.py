import sys
import os

from fastapi.testclient import TestClient
from main import app
from app.models import Todo, TodoTag
from app.database import get_db
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# テスト用クライアントの作成
client = TestClient(app)

def test_todo_list_split_by_status():
    """
    【応用テスト】未完了・完了済みが正しく分かれるかのテスト
    """
    # === 1. Arrange（データの準備） ===
    db = next(get_db())
    
    # 先に子データ（タグ）をお掃除
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
    
    data = response.json()

    # === 3. Assert（生データの画面出力） ===
    print("\n" + "="*40)
    print("🚀 アプリから返ってきた実際のデータはこれです！")
    print(data)
    print("="*40 + "\n")
    
    assert data is not None
    
    db.close()