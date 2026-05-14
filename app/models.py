from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, Text, func, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Todo(Base):
    __tablename__ = "todo"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    description: Mapped[str] = mapped_column(Text) 
    due_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[bool] = mapped_column(Boolean, default=False) 
    tag: Mapped[str] = mapped_column(String(50), index=True)
    link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    memo: Mapped[Optional[str]] = mapped_column(Text, nullable=True) 
    
    tags: Mapped[List["Tag"]] = relationship(
        secondary="todo_tag",
        back_populates="todos"
    )

class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    description: Mapped[str] = mapped_column(Text)
    usage: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    
    todos: Mapped[List["Todo"]] = relationship(
        secondary="todo_tag",
        back_populates="tags"
    )

class TodoTag(Base):
    __tablename__ = "todo_tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    todo_id: Mapped[int] = mapped_column(ForeignKey("todo.id"), index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tag.id"), index=True)