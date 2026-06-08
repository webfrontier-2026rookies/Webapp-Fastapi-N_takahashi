from sqlalchemy.orm import Session
from app.models import Todo, Tag
from app.schemas import TodoCreate, TodoUpdate, TagCreate, TagUpdate

def get_todo(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Todo).offset(skip).limit(limit).all()

def get_todo_by_id(db: Session, todo_id: int):
    return db.query(Todo).filter(Todo.id == todo_id).first()

def get_todo_by_title(db: Session, todo_title: str):
    return db.query(Todo).filter(Todo.title == todo_title).first()

# 変更があった項目だけをループ処理で順番に上書き更新する
def update_todo(db: Session, todo_id: int, todo: TodoUpdate) -> Todo | None:
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        return None
    for field, value in todo.model_dump(exclude_unset=True).items():
        setattr(db_todo, field, value)
    db.commit()
    db.refresh(db_todo)
    return db_todo

# todo削除
def delete_todo(db: Session, todo_id: int) -> Todo | None:
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo:
        db.delete(db_todo)
        db.commit()
    return db_todo

# tag作成
def create_tag(db: Session, tag: TagCreate, username: str) -> Tag:
    db_tag = Tag(
        title=tag.title,
        description=tag.description,
        usage=tag.usage,
        username=username
    )
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def get_tag(db: Session, tag_id: int):
    return db.query(Tag).filter(Tag.id == tag_id).first()

def get_tag_by_id(db: Session, tag_id: int):
    return db.query(Tag).filter(Tag.id == tag_id).first()

def get_tag_by_title(db: Session, tag_title: str):
    return db.query(Tag).filter(Tag.title == tag_title).first()

def get_tag_list(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Tag).offset(skip).limit(limit).all()

def update_tag(db: Session, tag_id: int, tag: TagUpdate) -> Tag | None:
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not db_tag:
        return None
    for field, value in tag.model_dump(exclude_unset=True).items():
        setattr(db_tag, field, value)
    db.commit()
    db.refresh(db_tag)
    return db_tag


def delete_tag(db: Session, tag_id: int) -> Tag | None:
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if db_tag:
        db.delete(db_tag)
        db.commit()
    return db_tag

def create_todo_with_tags(db: Session, todo_data: TodoCreate, tag_ids: list[int], username: str) -> Todo:
    """Todo 本体と中間テーブル経由のタグ紐付けを同時に作成する"""
    todo_link = str(todo_data.link) if todo_data.link else None
    db_todo = Todo(title=todo_data.title, description=todo_data.description, due_date=todo_data.due_date, status=todo_data.status, link=todo_link, memo=todo_data.memo, username=username)
    db.add(db_todo)
    db.flush()
    if tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        db_todo.tags = tags
    db.commit()
    db.refresh(db_todo)
    return db_todo