from pydantic import BaseModel, ConfigDict
from typing import Optional, Union
from datetime import datetime
from pydantic import HttpUrl
from pydantic_settings import BaseSettings
import os

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
    due_date: Optional[Union[datetime, str]] = None
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
    tag_id: int  

class CsrfSettings(BaseSettings):
    secret_key: str = os.getenv("CSRF_SECRET")
    cookie_samesite: str = "lax"
    cookie_secure: bool = True

