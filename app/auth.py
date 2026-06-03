from jose import jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY_JWT")

ALGORITHM = "HS256"

#JWTの作成
def create_access_token(data: dict):
    #元のデータを傷つけないためコピー
    copy_data = data.copy()
    encoded_jwt = jwt.encode(copy_data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#JWTの検証
def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("username")
    except Exception:
        return None
