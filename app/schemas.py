from pydantic import BaseModel, ConfigDict
from typing import Optional

# データの受け取り用スキーマ
class TodoBase(BaseModel):
    title: str
    description: str
    

class TodoCreate(TodoBase):
    created_at: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[bool] = False
    tag: Optional[str] = None
    link: Optional[str] = None
    memo: Optional[str] = None

# DBから取得したデータの返し用スキーマ
class Todo(TodoBase):
    id: int
    created_at: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[bool] = False
    tag: Optional[str] = None
    link: Optional[str] = None
    memo: Optional[str] = None

    # SQLAlchemyのモデルをPydanticで使うための設定
    model_config = ConfigDict(from_attributes=True)

# 更新用スキーマ
class TodoUpdate(TodoBase):
    title: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[bool] = None
    tag: Optional[str] = None
    link: Optional[str] = None
    memo: Optional[str] = None