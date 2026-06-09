import sys
import os

from fastapi.testclient import TestClient
from main import app
from app.models import User
from app.database import get_db
from passlib.context import CryptContext
from app.schemas import verify_csrf_token

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

client = TestClient(app)

TEST_USERNAME = os.getenv("TEST_USERNAME")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


# アカウント登録ができるかどうかのテストコード
app.dependency_overrides[verify_csrf_token] = lambda: None

TEST_USERNAME = os.getenv("TEST_USERNAME")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")


# アカウント登録ができるかどうかのテストコード
def test_account_register():
    db = next(get_db())
    try:
        # 登録するusernameと同じものを削除
        db.query(User).filter(User.username == TEST_USERNAME).delete()
        db.commit()
    finally:
        db.close()
    
    register_data = {
        "username": TEST_USERNAME,
        "hashed_password": TEST_PASSWORD  # password から hashed_password に戻します
    }
    
    response = client.post("/account/register", data=register_data)

    if response.status_code == 422:
        print("\n==================================================")
        print("FastAPIから返ってきた本当のエラー内容はこちら：")
        print(response.json())
        print("==================================================")

    assert response.status_code in [200, 303]
    print("\n✨ アカウント登録成功（ログイン画面へリダイレクト）！")

    app.dependency_overrides.clear()

# # ログインできるかどうかのテストコード
def test_login_success():
    db = next(get_db())
    try:
        db.query(User).filter(User.username == TEST_USERNAME).delete()
        
        db_hash = pwd_context.hash(TEST_PASSWORD)
        test_user = User(username=TEST_USERNAME, hashed_password=db_hash)
        
        db.add(test_user)
        db.commit()
    finally:
        db.close() 

    dummy_csrf = "login_csrf_123"

    login_data = {
        "username": TEST_USERNAME,
        "hashed_password": TEST_PASSWORD
    }

    test_cookies = {"csrf_token": dummy_csrf}
    test_headers = {"X-CSRF-Token": dummy_csrf}

    response = client.post("/account/login", data=login_data, headers=test_headers, cookies=test_cookies)

    assert response.status_code in [200, 303]
    print("\n✨ ログイン成功！")