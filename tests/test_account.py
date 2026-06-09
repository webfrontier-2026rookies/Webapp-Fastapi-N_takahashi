import sys
import os

from fastapi.testclient import TestClient
from main import app
from app.models import User
from app.database import get_db
from app.auth import create_access_token

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

client = TestClient(app)

#アカウント登録ができるかどうかのテストコード
def test_account_register():
    db = next(get_db())
    
    try:
        #登録するusernameと同じものを削除
        db.query(User).filter(User.username == "aiueo").delete()
        db.commit()
    finally:
        db.close()
    
    #本番のロジック（verify_access_token）を突破するための有効なJWTをその場で生成
    real_jwt = create_access_token(data={"username": "note"})

    #本番のCSRF検証（verify_csrf_token）を突破するためのダミーの共通文字列
    dummy_csrf = "perfect_match_csrf_token_123"

    register_data = {
        "username": "aiueo",
        "hashed_password": "mamoru" 
    }

    #本番コードが探しているクッキー名をセット
    test_cookies = {
        "access_token": real_jwt,
        "csrf_token": dummy_csrf
    }

    #本番コードが探しているヘッダー名に、上のクッキーと同じ文字列をセット
    test_headers = {
        "X-CSRF-Token": dummy_csrf 
    }
    
    response = client.post("/account/register", data=register_data,headers=test_headers,cookies=test_cookies)

    assert response.status_code == 200
    
    print("登録成功")