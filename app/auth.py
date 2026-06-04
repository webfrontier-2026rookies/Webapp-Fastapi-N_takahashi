from jose import jwt
import os
from datetime import datetime, timedelta, timezone

SECRET_KEY = os.getenv("SECRET_KEY_JWT")

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30

#JWTの作成
def create_access_token(data: dict, expires_delta: timedelta = None):
    #元のデータを傷つけないためコピー
    copy_data = data.copy()

    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    copy_data["exp"] = expire
    return jwt.encode(copy_data, SECRET_KEY, algorithm=ALGORITHM)

#JWTの検証
def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("username")
    except Exception:
        return None
    

