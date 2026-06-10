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

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def test_account_register():
    app.dependency_overrides[verify_csrf_token] = lambda: None
    db = next(get_db())

    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")

    try:
        #同じusernameを削除
        db.query(User).filter(User.username == username).delete()
        db.commit()
    finally:
        db.close()
    
    register_data = {
        "username": username,
        "hashed_password": password
    }
    
    response = client.post("/account/register", data=register_data)

    assert response.status_code in [200, 303]
    print("アカウント登録のテスト成功！")
    app.dependency_overrides.clear()


def test_login():
    db = next(get_db())

    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")
    
    try:
        db.query(User).filter(User.username == username).delete()
        db_hash = pwd_context.hash(password)
        test_user = User(username=username, hashed_password=db_hash)
        db.add(test_user)
        db.commit()
    finally:
        db.close() 

    dummy_csrf = "login_csrf_123"
    login_data = {
        "username": username,
        "hashed_password": password
    }

    test_cookies = {"csrf_token": dummy_csrf}
    test_headers = {"X-CSRF-Token": dummy_csrf}

    response = client.post("/account/login", data=login_data, headers=test_headers, cookies=test_cookies)

    assert response.status_code in [200, 303]
    print("ログインのテスト成功！")


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
    
    assert response.status_code in [200, 303]
    assert "access_token" not in response.cookies or response.cookies.get("access_token") == ""
    print("ログアウトのテスト成功！")