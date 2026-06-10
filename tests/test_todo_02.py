import sys
import os

from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from main import app
from app.models import Todo, TodoTag,User
from app.database import get_db
from app.auth import create_access_token

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

client = TestClient(app)

#todoの一覧表示ができるかどうかのテストコード
def test_todo_list():
    username = os.getenv("TEST_USERNAME")
    
    db = next(get_db())
    try:
        db.query(TodoTag).delete()
        db.query(Todo).delete()
        db.query(User).delete()
        
        test_todo = Todo(
            title="一覧表示のテスト用TODO",
            description="このTODOが画面やAPIから見えれば合格です",
            due_date=datetime.now(),
            status=False,
            username=username,
        )
        db.add(test_todo)
        db.commit()

        real_jwt = create_access_token(data={"username": username})
        test_cookies = {
            "access_token": real_jwt
        }
        
        response = client.get("/api/todo", cookies=test_cookies)

        assert response.status_code == 200
        print("\n✨ TODO一覧表示のテスト成功！")

    finally:
        db.close()

#todoの検索ができるかどうかのテストコード
def test_todo_search():
    db = next(get_db())
    try:
        db.query(TodoTag).delete()
        db.query(Todo).delete()

        todo1 = Todo(
            title="検索の検証用のtodo",
            description="todo検索のテストコード用のtodo",
            due_date=datetime.now(),
            status=False,
            link="https://calendar.google.com/calendar/u/0/r",
            memo="qqqq",
            username="2525"
        )

        todo2 = Todo(
            title="技術勉強",
            description="技術勉強用のテストコード",
            due_date=datetime.now()+ timedelta(days=4),
            status=True,
            link="https://calendar.google.com/calendar/u/0/r",
            memo="eeeeee",
            username=2525
        )

        todo3 = Todo(
            title="夕飯用の買い出し",
            description="今夜の夕飯の買い出し",
            due_date=datetime.now()+ timedelta(days=2),
            status=False,
            link="https://meet.google.com/att-diiz-edw",
            memo="iiii",
            username=2525
        )

        db.add_all([todo1,todo2,todo3])
        db.commit()

        response = client.get("/api/todo?q=買い出し")

        assert response.status_code == 200
        print("検索成功")

    finally:
        db.close()

#todoの並び替えができるかどうかのテストコード
def test_todo_sort():
    db = next(get_db())

    try:
        db.query(TodoTag).delete()
        db.query(Todo).delete()

        todo1 = Todo(
            title="スーパーで買い物",
            description="牛乳を買う",  
            due_date=datetime.now() + timedelta(days=1),
            status=True,
            username="note"
        )
        todo2 = Todo(
            title="デパ地下で買い物",
            description="お惣菜を買う",
            due_date=datetime.now(), 
            status=False,
            username="note"
        )
        todo3 = Todo(
            title="プログラミングの勉強",
            description="FastAPIのテストを書く",
            due_date=datetime.now() + timedelta(days=5),
            status=False,
            username="note"
        )

        db.add_all([todo1, todo2, todo3])
        db.commit()

        test_cookies = {
            "access_token": create_access_token(data={"username": "note"})
        }

        response = client.get("/api/todo?q=買い物",cookies=test_cookies)
        assert response.status_code == 200

        html_content = response.text

        assert "スーパーで買い物" in html_content
        assert "デパ地下で買い物" in html_content
        assert "プログラミングの勉強" not in html_content

        idx_today = html_content.find("デパ地下で買い物")
        idx_tomorrow = html_content.find("スーパーで買い物")
        
        assert idx_today < idx_tomorrow

    finally:
        db.close()

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

#todoの更新ができるかどうかのテストコード作成
def test_todo_update():
    db = next(get_db())
    db.query(TodoTag).delete()
    db.query(Todo).delete()

    test_todo = Todo(
        title="更新前のTODO",
        description="これから更新されます",
        due_date=datetime.now(),
        status=False,
        username="kiki",
    )
    db.add(test_todo)
    db.commit()

    response = client.put(
        f"/api/todo/{test_todo.id}",
        json={
            "title": "更新後のTODOタイトル",
            "description": "無事に更新されました",
            "tag_id": 1
        }
    )
    assert response.status_code == 200

    db.refresh(test_todo)
    assert test_todo.title == "更新後のTODOタイトル"
    assert test_todo.description == "無事に更新されました"

    db.close()

#todoの削除ができるかどうかのテストコード
def test_tag_delete():
    db = next(get_db())
    db.query(Todo).delete()

    todo = Todo(
        title="todo削除テスト",
        due_date=datetime.now() + timedelta(days=6),
        status=False,
        description="削除テスト確認", 
        username="kiki",
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

#todoの詳細表示ができるかどうかのテストコード
def test_todo_detail_page():
    db = next(get_db())

    test_todo = Todo(
        title="詳細表示のTODO",
        description="このが画面やAPIから見えれば合格です",
        due_date=datetime.now() + timedelta(days=3),
        status=False,
        username=2525,
        link="https://meet.google.com/att-diiz-edw",
        memo="rrrr"
    )

    db.add(test_todo)
    db.commit()
    db.refresh(test_todo) 

    response = client.get(f"/api/todo/{test_todo.id}")

    assert response.status_code == 200

#todoの作成フォームが表示できるかどうかのテストコード
def test_todo_create_page():
    response = client.get("/todo/create")

    assert response.status_code == 200

#todoの更新画面表示ができるかどうかのテストコード
def test_todo_update_page():
    db = next(get_db())
    
    try:
        db.query(TodoTag).delete()
        db.query(Todo).delete()
        
        test_todo = Todo(
            title="編集画面テスト用のTODO",
            description="このTODOを編集します",
            due_date=datetime.now(),
            status=False,
            username="note"
        )
        db.add(test_todo)
        db.commit()
        db.refresh(test_todo) 
        
        target_id = test_todo.id 

    finally:
        db.close()

    response = client.get(f"/todo/{target_id}/edit")

    assert response.status_code == 200
    print("更新画面表示成功")