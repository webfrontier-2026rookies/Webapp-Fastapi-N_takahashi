import sys
import os

from fastapi.testclient import TestClient
from main import app
from app.models import User
from app.database import get_db
from app.schemas import verify_csrf_token 
from passlib.context import CryptContext

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

client = TestClient(app)

TEST_USERNAME = "test_user_999"
TEST_PASSWORD = "password123"
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

#アカウント登録のテストコード
def test_account_register():
    app.dependency_overrides[verify_csrf_token] = lambda: None

    db = next(get_db())
    try:
        db.query(User).filter(User.username == TEST_USERNAME).delete()
        db.commit()
    finally:
        db.close()
    
    register_data = {
        "username": TEST_USERNAME,
        "hashed_password": TEST_PASSWORD
    }
    
    response = client.post("/account/register", data=register_data)

    assert response.status_code in [200, 303]
    print("\n✨ アカウント登録のテスト成功！")
    app.dependency_overrides.clear()

#ログインができるかどうかのテストコード
def test_login():
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
    print("\n✨ ログインのテスト成功！")

#ログアウトできるかのテストコード
def test_logout():
    dummy_csrf = "logout_csrf_token_999"
    test_cookies = {
        "access_token": "dummy_logged_in_jwt_token",
        "csrf_token": dummy_csrf
    }
    test_headers = {
        "X-CSRF-Token": dummy_csrf
    }
    
    response = client.post("/account/logout", headers=test_headers, cookies=test_cookies)
    
    assert response.status_code == 200
    assert "access_token" not in response.cookies or response.cookies.get("access_token") == ""
    print("\n✨ ログアウトのテスト成功！")