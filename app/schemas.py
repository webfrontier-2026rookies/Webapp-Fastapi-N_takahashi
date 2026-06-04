from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from pydantic import HttpUrl
import secrets
from fastapi import HTTPException, Request, status


# データの受け取り用スキーマ
class TodoBase(BaseModel):
    title: str
    description: str
    
class TodoCreate(TodoBase):
    due_date: Optional[datetime] = None
    status: bool = False
    tag_ids: list[int] = []
    link: Optional[HttpUrl] = None
    memo: Optional[str] = None

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[bool] = None
    tag_ids: list[int] = []
    link: Optional[HttpUrl] = None
    memo: Optional[str] = None

# DBから取得したデータの返し用スキーマ
class Todo(TodoBase):
    id: int
    created_at: datetime
    due_date: datetime
    status: bool
    tag_ids: list[int] = []
    link: Optional[HttpUrl] = None
    memo: Optional[str] = None

    # SQLAlchemyのモデルをPydanticで使うための設定
    model_config = ConfigDict(from_attributes=True)

# タグのスキーマ
class TagBase(BaseModel):
    title: str
    description: str

class TagCreate(TagBase):
    usage: Optional[str] = None

class TagUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    usage: Optional[str] = None

# DBから取得したデータの返し用スキーマ
class Tag(TagBase):
    id: int
    created_at: datetime
    usage: Optional[str] = None

    # SQLAlchemyのモデルをPydanticで使うための設定
    model_config = ConfigDict(from_attributes=True)

class TodoWithTagUpdate(BaseModel):
    title: str
    description: str
    due_date: Optional[datetime] = None
    tag_ids: list[int] = []

async def verify_csrf_token(request: Request):
    # 1. Cookie からトークンを取得
    cookie_token = request.cookies.get("csrf_token")
    
    # 2. フォームデータを非同期で解析して取得
    form_data = await request.form()
    
    # 3. リクエストヘッダー、またはフォームデータ（HTMLのinput）からトークンを取得
    header_token = request.headers.get("X-CSRF-Token") or form_data.get("X-CSRF-Token")
    
    # 4. どちらかが欠けていたら即座にアウト
    if not cookie_token or not header_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRFトークンが見つかりません。"
        )
    
    # 5. secrets.compare_digest で安全に検証
    if not secrets.compare_digest(cookie_token, header_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRFトークンが不正です。"
        )
        
    return True