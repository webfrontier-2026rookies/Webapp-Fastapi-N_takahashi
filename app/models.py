from sqlalchemy.orm import Mapped, mapped_column, Relationship
from sqlalchemy import String,Boolean,DateTime,Text
from app.detabase import Base

class Todo(Base):
    __tablename__ = "todo"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200),index=True)
    created_at: Mapped[DateTime] = mapped_column(default=DateTime.now,index=True)
    description: Mapped[Text] = mapped_column()
    due_date: Mapped[DateTime] = mapped_column(index=True)
    status: Mapped[Boolean] = mapped_column(default=False)
    tag: Mapped[str] = mapped_column(String(50), index=True)
    link: Mapped[str | None] = mapped_column(index=True)
    memo: Mapped[Text | None] = mapped_column()
    tags: Mapped[list["Tag"]] = Relationship(
        secondary="todo_tag", # 中間テーブル経由で取得
        back_populates="todo"
    )

class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200),index=True)
    created_at: Mapped[DateTime] = mapped_column(index=True)
    description: Mapped[Text] = mapped_column()
    usage: Mapped[Text | None] = mapped_column(Text, index=True)
    todos: Mapped[list["Todo"]] = Relationship(
        secondary="todo_tag", # 中間テーブル経由で取得
        back_populates="tag"
    )


class TodoTag(Base):
    __tablename__ = "todo_tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    todo_id: Mapped[int] = mapped_column(String(200), index=True)
    tag_id: Mapped[int] = mapped_column(String(200), index=True)