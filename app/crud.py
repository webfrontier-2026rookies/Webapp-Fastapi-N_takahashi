from sqlalchemy.orm import Session
from app.models import Todo, Tag, TodoTag
from app.schemas import TodoCreate, TodoUpdate
from app import schemas
from datetime import datetime

def create_todo(db: Session, todo: TodoCreate):
    db_todo = Todo(
        title=todo.title,
        description=todo.description,
        due_date=todo.due_date,
        status=todo.status,
        tag=todo.tag,
        link=todo.link,
        memo=todo.memo
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def get_todo(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Todo).offset(skip).limit(limit).all()

def update_todo(db: Session, todo_id: int, todo_data: TodoUpdate):
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo:
        db_todo.title = todo_data.title
        db_todo.created_at = todo_data.created_at
        db_todo.description = todo_data.description
        db_todo.due_date = todo_data.due_date
        db_todo.status = todo_data.status
        db_todo.tag = todo_data.tag
        db_todo.link = todo_data.link
        db_todo.memo = todo_data.memo
        db.commit()
        db.refresh(db_todo)
    return db_todo

def delete_todo(db: Session, todo_id: int):
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo:
        db.delete(db_todo)
        db.commit()
    return db_todo

def create_tag(db: Session, tag: str):
    db_tag = Tag(
        title=tag.title,
        created_at=tag.created_at,
        description=tag.description,
        usage=tag.usage
    )
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def create_todo_with_tags(db: Session, todo_data: schemas.TodoCreate, tag_ids: list[int]):
    # 1. Todo 本体を作成
    db_todo = Todo(
        title=todo_data.title, 
        description=todo_data.description
    )
    db.add(db_todo)
    db.flush()

    #中間テーブルにデータを追加
    for tag_id in tag_ids:
        db_todo_tag = TodoTag(todo_id=db_todo.id, tag_id=tag_id)
        db.add(db_todo_tag)
    
    db.commit()
    db.refresh(db_todo)
    return db_todo

def get_todo_by_title(db: Session, todo_title: str):
    return db.query(Todo).filter(Todo.title == todo_title).first()

# todo削除
def delete_todo(db: Session, todo_id: int):
    # 1. 削除対象のデータを取得
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    
    # 2. データが存在すれば削除してコミット
    if db_todo:
        db.delete(db_todo)
        db.commit()
        return True
    return False