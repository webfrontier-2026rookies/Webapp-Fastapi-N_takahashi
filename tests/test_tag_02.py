import sys
import os

from fastapi.testclient import TestClient
from main import app
from app.models import Tag, TodoTag
from app.database import get_db
from app.auth import create_access_token

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

#tagの検索ができるかどうかのテストコード
def test_todo_search():
    db = next(get_db())
    try:
        db.query(TodoTag).delete()
        db.query(Tag).delete()

        tag1 = Tag(
            title="検索の検証用のtag",
            description="tag検索のテストコード用のtag",
            usage="ooooo",
            username="2525"
        )

        tag2 = Tag(
            title="技術勉強",
            description="技術勉強用のテストコード",
            usage="uuuu",
            username=2525
        )

        tag3 = Tag(
            title="夕飯用の買い出し",
            description="今夜の夕飯の買い出し",
            usage="yyyy",
            username=2525
        )

        db.add_all([tag1,tag2,tag3])
        db.commit()

        response = client.get("/api/tag?q=勉強")

        assert response.status_code == 200
        print("検索成功")

    finally:
        db.close()

#tagの並び替えができるかどうかのテストコード
def test_tag_sort():
    db = next(get_db())

    try:
        db.query(TodoTag).delete()
        db.query(Tag).delete()

        tag1 = Tag(
            title="スーパーで買い物",
            description="牛乳を買う",  
            usage="本日中に買い物をすること",
            username="note"
        )
        tag2 = Tag(
            title="デパ地下で買い物",
            description="お惣菜を買う",
            usage="買い物をすること",
            username="note"
        )
        tag3 = Tag(
            title="プログラミングの勉強",
            description="FastAPIのテストを書く",
            usage="テスト用の勉強",
            username="note"
        )

        db.add_all([tag1, tag2, tag3])
        db.commit()

        test_cookies = {
            "access_token": create_access_token(data={"username": "note"})
        }

        response = client.get("/api/tag?q=買い物",cookies=test_cookies)
        assert response.status_code == 200

        html_content = response.text

        assert "スーパーで買い物" in html_content
        assert "デパ地下で買い物" in html_content
        assert "プログラミングの勉強" not in html_content

        idx_today = html_content.find("デパ地下で買い物")
        idx_tomorrow = html_content.find("スーパーで買い物")
        
        assert idx_today > idx_tomorrow

    finally:
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

#tagの作成フォームが表示できるかどうかのテストコード
def test_todo_create_page():
    response = client.get("/tag/create")

    assert response.status_code == 200

    print("作成フォーム表示成功")

#tagの更新画面表示ができるかどうかのテストコード
def test_todo_update_page():
    db = next(get_db())
    
    try:
        db.query(TodoTag).delete()
        db.query(Tag).delete()
        
        test_tag = Tag(
            title="編集画面テスト用のTAG",
            description="このTODOを編集します",
            usage="ttttt",
            username="note"
        )
        db.add(test_tag)
        db.commit()
        db.refresh(test_tag) 
        
        target_id = test_tag.id 

    finally:
        db.close()

    response = client.get(f"/tag/{target_id}/edit")

    assert response.status_code == 200
    print("更新画面表示成功")