from pydantic import BaseModel, ConfigDict
from typing import Optional

# データの受け取り用スキーマ
class TodoBase(BaseModel):
    title: str
    description: str

class TodoCreate(TodoBase):
    pass

# DBから取得したデータの返し用スキーマ
class Todo(TodoBase):
    id: int
    
    # SQLAlchemyのモデルをPydanticで使うための設定
    model_config = ConfigDict(from_attributes=True)

# 更新用スキーマ
class TodoUpdate(TodoBase):
    title: Optional[str] = None
    description: Optional[str] = None